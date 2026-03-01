# Saved Profiles & Personal Chart Design

**Goal:** Allow users to save their birth profile to Supabase so they don't have to re-enter data on every visit. Free tier = 1 saved profile. Includes a `/me` personal chart page with chart data viewer and LLM prompt preview.

**Architecture:** New `saved_profiles` Supabase table caches `chart_data` (from astro-service `/calculate-chart`). `profile_card_data` and `ideal_match_data` are null for now — surfaced via prompt preview panel instead of LLM calls. The lounge form pre-fills from a saved profile and skips the chart API call when a cached chart is available.

**Tech Stack:** Next.js 16 App Router, Supabase (PostgreSQL + RLS), existing astro-service endpoints (`/calculate-chart`, `/generate-profile-card` prompt preview), existing `PromptPreviewPanel` component pattern.

---

## DB Schema

```sql
-- Migration 013
CREATE TABLE saved_profiles (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id       UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  label         TEXT NOT NULL,           -- user-chosen name e.g. "我自己"
  name          TEXT NOT NULL,           -- person name → pre-fills BirthInput
  birth_date    DATE NOT NULL,
  birth_time    TEXT,                    -- "HH:MM" or null
  lat           FLOAT NOT NULL DEFAULT 25.033,
  lng           FLOAT NOT NULL DEFAULT 121.565,
  data_tier     INTEGER NOT NULL DEFAULT 3,
  gender        TEXT NOT NULL DEFAULT 'M',
  yin_yang      TEXT NOT NULL DEFAULT 'yang',  -- 'yin' | 'yang'

  chart_data         JSONB,  -- cached result from /calculate-chart
  profile_card_data  JSONB,  -- null for now (future LLM)
  ideal_match_data   JSONB,  -- null for now (future LLM)

  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE saved_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own profiles only" ON saved_profiles
  FOR ALL USING (auth.uid() = user_id);
```

**Freemium enforcement:** application-side only. `POST /api/profiles` counts existing rows; if ≥ 1, returns 403 `{ error: "upgrade_required" }`. Paid tier controlled via auth metadata or future `user_plans` table.

---

## API Routes (destiny-mvp Next.js)

### `GET /api/profiles`
Returns all saved profiles for the authenticated user.
Response: array of profile objects with all fields.

### `POST /api/profiles`
Pipeline:
1. Count user's existing profiles → ≥ 1 → 403 `{ error: "upgrade_required" }`
2. `POST astro-service/calculate-chart` → `chart_data`
3. `INSERT saved_profiles` with `profile_card_data = null`, `ideal_match_data = null`
4. Return saved profile

Request body:
```json
{
  "label": "我自己",
  "name": "Alice",
  "birth_date": "1995-06-15",
  "birth_time": "14:30",
  "lat": 25.033,
  "lng": 121.565,
  "data_tier": 1,
  "gender": "F",
  "yin_yang": "yin"
}
```

### `PATCH /api/profiles/[id]`
Updates `yin_yang` (and future fields). Validates `user_id = auth.uid()`.

### `DELETE /api/profiles/[id]`
Deletes profile. Validates ownership.

---

## UX Flow

### Entry Points

**① Lounge page (`/lounge`)**
- Above each BirthInput: "從已儲存命盤選取 ▾" dropdown
- Selecting a profile: pre-fills all BirthInput fields; stores `chart_data` in state as `_cachedChart`
- In `runMatch()`: if `_cachedChart` exists for a person, skip `fetch("/api/calculate-chart")` for that person
- Below each BirthInput: "💾 儲存此命盤" button → save modal

**② Report page (`/report/[id]`)**
- Below ReportClient: "💾 儲存 A 的命盤" and "💾 儲存 B 的命盤" buttons
- Uses `report_json.user_a_chart` / `user_b_chart` + form data to pre-populate save modal

**③ NavBar → `/me`**
- New link in NavBar leading to personal profile page

### `/me` Page Layout

```
┌─────────────────────────────────────┐
│  ✦ 我的命盤                          │
│  [label] · [name]                   │
│                                     │
│  [☽ 陰] / [☀ 陽] toggle             │
│  (half-circle SVG preview)          │
│                                     │
│  § 行星速覽                          │
│  ☀ 太陽 · ☽ 月亮 · ↑ 上升 · ...    │
│  八字元素 · 依戀類型                  │
│                                     │
│  § Prompt 預覽 (collapsible)         │
│  chart_data → solo profile prompt   │
│  (same pattern as PromptPreviewPanel)│
│                                     │
│  § 我的合盤記錄（連連看）             │
│  mvp_matches WHERE name_a OR name_b  │
│  = profile.name (case-insensitive)   │
│  → list: 對方名字 · score · 報告連結 │
└─────────────────────────────────────┘
```

### Yin-Yang Visual
- Half-circle SVG: yin = dark crescent (`#5c4059`), yang = light arc (`#f4e0e8`)
- Toggle saves to DB via `PATCH /api/profiles/[id]`
- Future: match report shows "你（陰）× 對方（陽）= ☯ 完整圓"

### Save Modal
Triggered from Lounge or Report page:
```
┌──────────────────────────┐
│  💾 儲存命盤              │
│  幫這個命盤取個名字：      │
│  [________________]      │
│  e.g. 我自己、老公、初戀  │
│                          │
│  [取消]  [儲存]           │
└──────────────────────────┘
```
If free tier already has 1 profile:
```
│  ✦ 升級方案解鎖無限命盤儲存 │
│  [查看方案]  [取消]         │
```

---

## Chart Caching Logic

When a saved profile is loaded in lounge:
```typescript
// state in LoungePage
const [cachedChartA, setCachedChartA] = useState<Record<string, unknown> | null>(null);

// runMatch() modified:
const [chartA, chartB] = await Promise.all([
  cachedChartA
    ? Promise.resolve(cachedChartA)  // skip API
    : fetch("/api/calculate-chart", ...).then(r => r.json()),
  cachedChartB
    ? Promise.resolve(cachedChartB)
    : fetch("/api/calculate-chart", ...).then(r => r.json()),
]);
```

---

## Decisions & Constraints

- `profile_card_data` and `ideal_match_data` are null initially; the `/me` page shows a prompt preview panel (deterministic, no LLM call) instead
- Free tier = 1 profile (application-side enforcement, not DB constraint)
- "連連看" is a list view for MVP, not an interactive graph
- Yin-yang is a user preference, no algorithmic impact in MVP
- The save flow from Report page uses `user_a_chart` / `user_b_chart` from `report_json` for `chart_data` — no new API call needed if data already exists
