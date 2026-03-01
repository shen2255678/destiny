# Saved Profiles Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Allow users to save birth profiles to `soul_cards` (Supabase), pre-fill the lounge form from saved cards, and view a personal `/me` chart page with planet data, prompt preview, and match history.

**Architecture:** `soul_cards` table already exists (migration 013) — add 3 fields via migration 014. Four Next.js API routes wrap the table. Lounge gains a profile picker dropdown + cached chart skip. `/me` page shows personal chart + match history. NavBar gains a link.

**Tech Stack:** Next.js 16 App Router, Supabase SSR (`@supabase/ssr`), TypeScript. No new npm packages.

**Design doc:** `docs/plans/2026-03-01-saved-profiles-design.md`

---

## Key Files Reference

- **Lounge (form):** `destiny-mvp/app/lounge/page.tsx`
- **BirthInput component:** `destiny-mvp/components/BirthInput.tsx` — `BirthData` interface: `{ name, birth_date, birth_time, lat, lng, data_tier, gender }`
- **NavBar:** `destiny-mvp/components/NavBar.tsx`
- **ReportClient:** `destiny-mvp/app/report/[id]/ReportClient.tsx`
- **Report page:** `destiny-mvp/app/report/[id]/page.tsx`
- **Supabase server:** `destiny-mvp/lib/supabase/server.ts` — `import { createClient } from "@/lib/supabase/server"`
- **Supabase browser:** `destiny-mvp/lib/supabase/client.ts` — `import { createClient } from "@/lib/supabase/client"`
- **Existing migration:** `destiny-mvp/supabase/migrations/013_mvp_tables.sql` — `soul_cards` table with `owner_id, display_name, birth_date, birth_time (TIME), lat, lng, data_tier, gender, natal_cache JSONB`
- **soul_cards note:** `birth_time` is type `TIME` (postgres), stored as `"HH:MM:SS"` — when reading back, trim to `"HH:MM"` for BirthInput
- **shadowTagsZh:** `destiny-mvp/lib/shadowTagsZh.ts` — pattern for zh translation utils

## Supabase Project

Project ref: `masninqgihbazjirweiy`
Run SQL migrations in Supabase SQL Editor (https://supabase.com/dashboard/project/masninqgihbazjirweiy/sql/new)

---

## Task 1: DB Migration 014 — extend soul_cards

**Files:**
- Create: `destiny-mvp/supabase/migrations/014_soul_cards_extend.sql`

**Step 1: Write the migration SQL**

```sql
-- Migration 014: extend soul_cards with yin_yang + profile cache fields
ALTER TABLE public.soul_cards
  ADD COLUMN IF NOT EXISTS yin_yang          TEXT NOT NULL DEFAULT 'yang',
  ADD COLUMN IF NOT EXISTS profile_card_data JSONB,
  ADD COLUMN IF NOT EXISTS ideal_match_data  JSONB,
  ADD COLUMN IF NOT EXISTS updated_at        TIMESTAMPTZ DEFAULT NOW();
```

Save this as `destiny-mvp/supabase/migrations/014_soul_cards_extend.sql`.

**Step 2: Run in Supabase SQL Editor**

Go to https://supabase.com/dashboard/project/masninqgihbazjirweiy/sql/new, paste and run. Confirm: no error, table updated.

**Step 3: Verify in table editor**

In Supabase Table Editor, open `soul_cards` → confirm 4 new columns: `yin_yang`, `profile_card_data`, `ideal_match_data`, `updated_at`.

**Step 4: Commit**

```bash
git add destiny-mvp/supabase/migrations/014_soul_cards_extend.sql
git commit -m "feat(db): migration 014 — extend soul_cards with yin_yang + profile cache"
```

---

## Task 2: API Routes — GET + POST /api/profiles

**Files:**
- Create: `destiny-mvp/app/api/profiles/route.ts`

**Context:**
- GET: list authenticated user's soul_cards, return array
- POST: (1) free tier check — count existing rows, ≥ 1 → 403; (2) call `POST http://localhost:8001/calculate-chart`; (3) INSERT soul_cards
- `ASTRO_SERVICE_URL` = `process.env.ASTRO_SERVICE_URL ?? "http://localhost:8001"`
- Auth: use `createClient()` from `@/lib/supabase/server` — same pattern as other API routes

**Step 1: Create the file**

```typescript
// destiny-mvp/app/api/profiles/route.ts
import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";

const ASTRO = process.env.ASTRO_SERVICE_URL ?? "http://localhost:8001";

export async function GET() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { data, error } = await supabase
    .from("soul_cards")
    .select("id, display_name, birth_date, birth_time, lat, lng, data_tier, gender, yin_yang, natal_cache, profile_card_data, ideal_match_data, created_at")
    .eq("owner_id", user.id)
    .order("created_at", { ascending: false });

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data ?? []);
}

export async function POST(req: NextRequest) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  // Free tier check
  const { count } = await supabase
    .from("soul_cards")
    .select("id", { count: "exact", head: true })
    .eq("owner_id", user.id);

  if ((count ?? 0) >= 1) {
    return NextResponse.json({ error: "upgrade_required" }, { status: 403 });
  }

  const body = await req.json() as {
    label: string;
    birth_date: string;
    birth_time?: string;
    lat: number;
    lng: number;
    data_tier: 1 | 2 | 3;
    gender: "M" | "F";
    yin_yang?: "yin" | "yang";
  };

  // Calculate chart (non-blocking on failure)
  let natal_cache: Record<string, unknown> | null = null;
  try {
    const chartRes = await fetch(`${ASTRO}/calculate-chart`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        birth_date: body.birth_date,
        birth_time_exact: body.birth_time || null,
        lat: body.lat,
        lng: body.lng,
        data_tier: body.data_tier,
      }),
    });
    if (chartRes.ok) natal_cache = await chartRes.json();
  } catch {
    // astro-service down — save profile without chart cache
  }

  const { data, error } = await supabase
    .from("soul_cards")
    .insert({
      owner_id: user.id,
      display_name: body.label,
      birth_date: body.birth_date,
      birth_time: body.birth_time || null,
      lat: body.lat,
      lng: body.lng,
      data_tier: body.data_tier,
      gender: body.gender,
      yin_yang: body.yin_yang ?? "yang",
      natal_cache,
    })
    .select("id, display_name, birth_date, birth_time, lat, lng, data_tier, gender, yin_yang, natal_cache")
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data, { status: 201 });
}
```

**Step 2: Test GET manually**

With browser logged into destiny-mvp, open DevTools console and run:
```js
fetch("/api/profiles").then(r => r.json()).then(console.log)
// Expected: [] (empty array if no profiles saved yet)
```

**Step 3: Test POST manually**

```js
fetch("/api/profiles", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    label: "測試卡",
    birth_date: "1995-06-15",
    birth_time: "14:30",
    lat: 25.033,
    lng: 121.565,
    data_tier: 1,
    gender: "F",
    yin_yang: "yin"
  })
}).then(r => r.json()).then(console.log)
// Expected: { id: "...", display_name: "測試卡", natal_cache: { sun_sign: "...", ... } }
```

Test free tier block: POST again → Expected: `{ error: "upgrade_required" }` with status 403.

**Step 4: Commit**

```bash
git add destiny-mvp/app/api/profiles/route.ts
git commit -m "feat(api): GET+POST /api/profiles wrapping soul_cards"
```

---

## Task 3: API Routes — PATCH + DELETE /api/profiles/[id]

**Files:**
- Create: `destiny-mvp/app/api/profiles/[id]/route.ts`

**Context:**
- PATCH: update `yin_yang` (and `updated_at`). Validate ownership.
- DELETE: delete by id. Validate ownership via RLS (Supabase RLS already enforces owner_id = auth.uid()).

**Step 1: Create the file**

```typescript
// destiny-mvp/app/api/profiles/[id]/route.ts
import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const body = await req.json() as { yin_yang?: "yin" | "yang" };

  const updates: Record<string, unknown> = { updated_at: new Date().toISOString() };
  if (body.yin_yang) updates.yin_yang = body.yin_yang;

  const { data, error } = await supabase
    .from("soul_cards")
    .update(updates)
    .eq("id", id)
    .eq("owner_id", user.id)
    .select("id, yin_yang")
    .single();

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json(data);
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { error } = await supabase
    .from("soul_cards")
    .delete()
    .eq("id", id)
    .eq("owner_id", user.id);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return new NextResponse(null, { status: 204 });
}
```

**Step 2: Test PATCH manually**

```js
// Use the id from Task 2 test
fetch("/api/profiles/<id>", {
  method: "PATCH",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ yin_yang: "yin" })
}).then(r => r.json()).then(console.log)
// Expected: { id: "...", yin_yang: "yin" }
```

**Step 3: Commit**

```bash
git add destiny-mvp/app/api/profiles/[id]/route.ts
git commit -m "feat(api): PATCH+DELETE /api/profiles/[id]"
```

---

## Task 4: Lounge — SavedProfilePicker + chart caching

**Files:**
- Modify: `destiny-mvp/app/lounge/page.tsx`

**Context:**
- Add state: `cachedChartA` and `cachedChartB` (the `natal_cache` from the selected soul_card)
- Add state: `profiles` (list of saved soul_cards, fetched on mount)
- Add state: `saving` (which slot is being saved: `null | "A" | "B"`) and `saveLabel` (input text)
- Add state: `savedSuccess` and `savedError`
- Profile picker: a `<select>` dropdown above each BirthInput — selecting a profile pre-fills all BirthInput fields + sets cachedChart
- Save button: below each BirthInput — opens a small inline save form (label input + confirm button)
- In `runMatch()`: skip `fetch("/api/calculate-chart")` for each side if cachedChart exists
- `birth_time` from soul_cards: postgres TIME returns `"HH:MM:SS"`, trim to `"HH:MM"` — use helper: `bt?.slice(0, 5) ?? ""`

**Step 1: Add imports and state to LoungePage**

At the top of the component, add:

```typescript
// Add to imports at top of file
import { useEffect } from "react";

// Add these state variables inside LoungePage():
const [profiles, setProfiles] = useState<Array<{
  id: string;
  display_name: string;
  birth_date: string;
  birth_time: string | null;
  lat: number;
  lng: number;
  data_tier: 1 | 2 | 3;
  gender: "M" | "F";
  yin_yang: string;
  natal_cache: Record<string, unknown> | null;
}>>([]);
const [cachedChartA, setCachedChartA] = useState<Record<string, unknown> | null>(null);
const [cachedChartB, setCachedChartB] = useState<Record<string, unknown> | null>(null);
const [saving, setSaving] = useState<null | "A" | "B">(null);
const [saveLabel, setSaveLabel] = useState("");
const [saveStatus, setSaveStatus] = useState("");

// Fetch saved profiles on mount
useEffect(() => {
  fetch("/api/profiles")
    .then((r) => r.json())
    .then((data) => {
      if (Array.isArray(data)) setProfiles(data);
    })
    .catch(() => {});
}, []);
```

**Step 2: Add profile picker + save UI helper (above return statement)**

Add this helper function inside the component:

```typescript
function ProfilePicker({
  slot,
  cached,
  onSelect,
  onClear,
}: {
  slot: "A" | "B";
  cached: boolean;
  onSelect: (p: typeof profiles[0]) => void;
  onClear: () => void;
}) {
  if (profiles.length === 0) return null;
  return (
    <div style={{ marginBottom: 10, display: "flex", gap: 8, alignItems: "center" }}>
      <select
        defaultValue=""
        onChange={(e) => {
          const p = profiles.find((x) => x.id === e.target.value);
          if (p) onSelect(p);
          else onClear();
        }}
        style={{
          flex: 1,
          padding: "6px 10px",
          borderRadius: 10,
          border: "1px solid rgba(255,255,255,0.6)",
          background: "rgba(255,255,255,0.5)",
          fontSize: 12,
          color: "#5c4059",
          cursor: "pointer",
        }}
      >
        <option value="">── 從已儲存命盤選取 ──</option>
        {profiles.map((p) => (
          <option key={p.id} value={p.id}>
            {p.display_name}
          </option>
        ))}
      </select>
      {cached && (
        <span style={{ fontSize: 10, color: "#34d399", fontWeight: 600 }}>
          ✓ 快取
        </span>
      )}
    </div>
  );
}
```

**Step 3: Modify the JSX for each BirthInput column**

Replace:
```tsx
<BirthInput label="A" value={a} onChange={setA} />
```

With:
```tsx
<div>
  <ProfilePicker
    slot="A"
    cached={!!cachedChartA}
    onSelect={(p) => {
      setA({
        name: p.display_name,
        birth_date: p.birth_date,
        birth_time: p.birth_time?.slice(0, 5) ?? "",
        lat: p.lat,
        lng: p.lng,
        data_tier: p.data_tier,
        gender: p.gender,
      });
      setCachedChartA(p.natal_cache);
    }}
    onClear={() => setCachedChartA(null)}
  />
  <BirthInput label="A" value={a} onChange={(v) => { setA(v); setCachedChartA(null); }} />
  <div style={{ marginTop: 8, textAlign: "right" }}>
    {saving === "A" ? (
      <div style={{ display: "flex", gap: 6, alignItems: "center", justifyContent: "flex-end" }}>
        <input
          value={saveLabel}
          onChange={(e) => setSaveLabel(e.target.value)}
          placeholder="幫這個命盤取個名字"
          style={{
            padding: "5px 10px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.6)",
            background: "rgba(255,255,255,0.5)", fontSize: 12, color: "#5c4059", width: 160,
          }}
        />
        <button
          onClick={async () => {
            setSaveStatus("儲存中...");
            const res = await fetch("/api/profiles", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ label: saveLabel || a.name, birth_date: a.birth_date, birth_time: a.birth_time || undefined, lat: a.lat, lng: a.lng, data_tier: a.data_tier, gender: a.gender }),
            });
            if (res.status === 403) { setSaveStatus("❌ 免費方案限 1 張，升級解鎖更多"); return; }
            if (!res.ok) { setSaveStatus("❌ 儲存失敗"); return; }
            const saved = await res.json();
            setProfiles((prev) => [saved, ...prev]);
            setSaving(null);
            setSaveLabel("");
            setSaveStatus("✓ 已儲存");
            setTimeout(() => setSaveStatus(""), 3000);
          }}
          style={{ padding: "5px 12px", borderRadius: 8, background: "#d98695", color: "#fff", border: "none", fontSize: 12, cursor: "pointer" }}
        >
          確認
        </button>
        <button onClick={() => { setSaving(null); setSaveLabel(""); }} style={{ padding: "5px 10px", borderRadius: 8, background: "transparent", border: "1px solid rgba(200,160,170,0.4)", fontSize: 12, color: "#8c7089", cursor: "pointer" }}>
          取消
        </button>
      </div>
    ) : (
      <button
        onClick={() => setSaving("A")}
        style={{ fontSize: 11, color: "#8c7089", background: "transparent", border: "none", cursor: "pointer", padding: "4px 0" }}
      >
        💾 儲存此命盤
      </button>
    )}
  </div>
</div>
```

Do the same for `BirthInput label="B"` — replace `setA`/`cachedChartA`/`saving === "A"` with `setB`/`cachedChartB`/`saving === "B"`.

Also add `saveStatus` display below the two-column grid:
```tsx
{saveStatus && (
  <p style={{ fontSize: 12, color: saveStatus.startsWith("✓") ? "#34d399" : "#c0392b", marginBottom: 8 }}>
    {saveStatus}
  </p>
)}
```

**Step 4: Modify runMatch() to use cached chart**

Find the line:
```typescript
const [resA, resB] = await Promise.all([
  fetch("/api/calculate-chart", { ... }),
  fetch("/api/calculate-chart", { ... }),
]);
const [chartA, chartB] = await Promise.all([
  resA.json() as Promise<Record<string, unknown>>,
  resB.json() as Promise<Record<string, unknown>>,
]);
```

Replace with:
```typescript
const [chartA, chartB] = await Promise.all([
  cachedChartA
    ? Promise.resolve(cachedChartA)
    : fetch("/api/calculate-chart", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildChartPayload(a)),
      }).then((r) => r.json() as Promise<Record<string, unknown>>),
  cachedChartB
    ? Promise.resolve(cachedChartB)
    : fetch("/api/calculate-chart", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildChartPayload(b)),
      }).then((r) => r.json() as Promise<Record<string, unknown>>),
]);
```

Remove the now-unused `const [resA, resB]` and the old `Promise.all` for `.json()`.

**Step 5: Verify in browser**

1. Open http://localhost:3000/lounge (logged in)
2. No profiles yet → no picker shown
3. Fill in Person A data → click "💾 儲存此命盤" → enter label → confirm
4. Picker appears with the saved profile
5. Select it → BirthInput pre-fills, "✓ 快取" badge appears
6. Hit "✦ 解析命運" → status shows "⟳ 解析命運共振..." (skips first chart calc) — check browser Network tab: only 1 `/api/calculate-chart` call (for B), none for A

**Step 6: Commit**

```bash
git add destiny-mvp/app/lounge/page.tsx
git commit -m "feat(lounge): saved profile picker + chart cache skip + save modal"
```

---

## Task 5: /me page — personal chart + match history

**Files:**
- Create: `destiny-mvp/app/me/page.tsx`
- Create: `destiny-mvp/app/me/MeClient.tsx`

**Context:**
- `page.tsx` = server component: fetch soul_cards for user, fetch recent mvp_matches, pass to MeClient
- `MeClient.tsx` = client component: yin-yang toggle, planet display, match history list, prompt preview (collapsible)
- Planet signs display: same logic as ReportClient's collapsible chart section (SIGN_ZH, ATT_ZH, BAZI_ZH maps)
- Prompt preview: show `natal_cache` JSON in a collapsible `<pre>` for now (not a full PromptPreviewPanel — that requires match data)
- Match history: from `mvp_matches` where `name_a ILIKE profile.display_name OR name_b ILIKE profile.display_name`
- Yin-yang toggle: calls `PATCH /api/profiles/[id]` on change

**Step 1: Create page.tsx (server component)**

```typescript
// destiny-mvp/app/me/page.tsx
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import { MeClient } from "./MeClient";

export default async function MePage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: profiles } = await supabase
    .from("soul_cards")
    .select("id, display_name, birth_date, birth_time, lat, lng, data_tier, gender, yin_yang, natal_cache, created_at")
    .eq("owner_id", user.id)
    .order("created_at", { ascending: false })
    .limit(1);

  const profile = profiles?.[0] ?? null;

  // Fetch match history where this person's name appears
  let matches: Array<{
    id: string;
    name_a: string | null;
    name_b: string | null;
    harmony_score: number | null;
    lust_score: number | null;
    soul_score: number | null;
    created_at: string;
  }> = [];

  if (profile) {
    const name = profile.display_name.toLowerCase();
    const { data: allMatches } = await supabase
      .from("mvp_matches")
      .select("id, name_a, name_b, harmony_score, lust_score, soul_score, created_at")
      .eq("user_id", user.id)
      .order("created_at", { ascending: false })
      .limit(20);

    matches = (allMatches ?? []).filter(
      (m) =>
        m.name_a?.toLowerCase().includes(name) ||
        m.name_b?.toLowerCase().includes(name)
    );
  }

  return <MeClient profile={profile} matches={matches} />;
}
```

**Step 2: Create MeClient.tsx (client component)**

```typescript
// destiny-mvp/app/me/MeClient.tsx
"use client";

import { useState } from "react";
import Link from "next/link";

const SIGN_ZH: Record<string, string> = {
  Aries: "牡羊座", Taurus: "金牛座", Gemini: "雙子座", Cancer: "巨蟹座",
  Leo: "獅子座", Virgo: "處女座", Libra: "天秤座", Scorpio: "天蠍座",
  Sagittarius: "射手座", Capricorn: "摩羯座", Aquarius: "水瓶座", Pisces: "雙魚座",
};
const ATT_ZH: Record<string, string> = {
  secure: "安全依戀型", anxious: "焦慮依戀型", avoidant: "迴避依戀型", fearful: "恐懼依戀型",
};
const BAZI_ZH: Record<string, string> = {
  Wood: "木", Fire: "火", Earth: "土", Metal: "金", Water: "水",
};
function zh(val: string | undefined | null, map: Record<string, string>): string {
  if (!val) return "—";
  return map[val] ?? val;
}

interface Profile {
  id: string;
  display_name: string;
  birth_date: string;
  birth_time: string | null;
  data_tier: number;
  gender: string;
  yin_yang: string;
  natal_cache: Record<string, unknown> | null;
}

interface Match {
  id: string;
  name_a: string | null;
  name_b: string | null;
  harmony_score: number | null;
  lust_score: number | null;
  soul_score: number | null;
  created_at: string;
}

export function MeClient({
  profile,
  matches,
}: {
  profile: Profile | null;
  matches: Match[];
}) {
  const [yinYang, setYinYang] = useState<"yin" | "yang">(
    (profile?.yin_yang as "yin" | "yang") ?? "yang"
  );
  const [promptOpen, setPromptOpen] = useState(false);

  const c = (profile?.natal_cache ?? {}) as Record<string, unknown>;

  async function toggleYinYang(val: "yin" | "yang") {
    setYinYang(val);
    if (profile) {
      await fetch(`/api/profiles/${profile.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ yin_yang: val }),
      });
    }
  }

  if (!profile) {
    return (
      <main style={{ maxWidth: 640, margin: "0 auto", padding: "48px 24px", textAlign: "center" }}>
        <p style={{ color: "#8c7089", fontSize: 14, marginBottom: 24 }}>
          你還沒有儲存任何命盤卡。
        </p>
        <Link
          href="/lounge"
          style={{
            background: "linear-gradient(135deg, #d98695 0%, #b86e7d 100%)",
            color: "#fff",
            padding: "10px 28px",
            borderRadius: 999,
            fontSize: 13,
            fontWeight: 600,
            textDecoration: "none",
          }}
        >
          ✦ 前往命運大廳
        </Link>
      </main>
    );
  }

  const isYin = yinYang === "yin";

  return (
    <main style={{ maxWidth: 640, margin: "0 auto", padding: "32px 24px" }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "#5c4059", letterSpacing: "0.08em", marginBottom: 4 }}>
          ✦ 我的命盤
        </h1>
        <p style={{ color: "#8c7089", fontSize: 13 }}>{profile.display_name}</p>
      </div>

      {/* Yin-Yang toggle */}
      <div style={{
        background: "rgba(255,255,255,0.35)", backdropFilter: "blur(12px)",
        border: "1px solid rgba(255,255,255,0.6)", borderRadius: 20,
        padding: "20px 24px", marginBottom: 24,
        display: "flex", alignItems: "center", gap: 20,
      }}>
        {/* Half-circle SVG */}
        <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
          {isYin ? (
            <>
              <path d="M30 5 A25 25 0 0 0 30 55 A25 25 0 0 1 30 5 Z" fill="#5c4059" opacity="0.8" />
              <path d="M30 5 A25 25 0 0 1 30 55 A25 25 0 0 0 30 5 Z" fill="#f4e0e8" opacity="0.5" />
            </>
          ) : (
            <>
              <path d="M30 5 A25 25 0 0 1 30 55 A25 25 0 0 0 30 5 Z" fill="#f4d5be" opacity="0.8" />
              <path d="M30 5 A25 25 0 0 0 30 55 A25 25 0 0 1 30 5 Z" fill="#f4e0e8" opacity="0.4" />
            </>
          )}
        </svg>
        <div>
          <p style={{ fontSize: 11, color: "#8c7089", marginBottom: 8 }}>你的命盤極性</p>
          <div style={{ display: "flex", gap: 8 }}>
            {(["yin", "yang"] as const).map((v) => (
              <button
                key={v}
                onClick={() => toggleYinYang(v)}
                style={{
                  padding: "6px 16px", borderRadius: 999, fontSize: 12, cursor: "pointer",
                  fontWeight: yinYang === v ? 700 : 400,
                  background: yinYang === v ? "rgba(217,134,149,0.2)" : "rgba(255,255,255,0.4)",
                  border: yinYang === v ? "1px solid rgba(217,134,149,0.5)" : "1px solid rgba(255,255,255,0.6)",
                  color: yinYang === v ? "#b86e7d" : "#8c7089",
                  transition: "all 0.2s",
                }}
              >
                {v === "yin" ? "☽ 陰" : "☀ 陽"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Planet grid */}
      <div style={{
        background: "rgba(255,255,255,0.3)", backdropFilter: "blur(12px)",
        border: "1px solid rgba(255,255,255,0.6)", borderRadius: 20,
        padding: "20px 24px", marginBottom: 24,
      }}>
        <p style={{ fontSize: 12, fontWeight: 700, color: "#b86e7d", marginBottom: 12 }}>
          行星速覽 · Tier {profile.data_tier}
        </p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 24px" }}>
          {[
            { label: "☀ 太陽", key: "sun_sign" },
            { label: "☽ 月亮", key: "moon_sign" },
            { label: "↑ 上升", key: "ascendant_sign" },
            { label: "♀ 金星", key: "venus_sign" },
            { label: "♂ 火星", key: "mars_sign" },
            { label: "☿ 水星", key: "mercury_sign" },
            { label: "♄ 土星", key: "saturn_sign" },
          ].map(({ label, key }) => (
            <div key={key} style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
              <span style={{ color: "#8c7089" }}>{label}</span>
              <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(c[key] as string, SIGN_ZH)}</span>
            </div>
          ))}
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
            <span style={{ color: "#8c7089" }}>🔥 八字元素</span>
            <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(c["bazi_element"] as string, BAZI_ZH)}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
            <span style={{ color: "#8c7089" }}>🧠 依戀類型</span>
            <span style={{ color: "#5c4059", fontWeight: 600 }}>{zh(c["attachment_style"] as string, ATT_ZH)}</span>
          </div>
        </div>
      </div>

      {/* Prompt preview (collapsible) */}
      <div style={{ marginBottom: 24 }}>
        <button
          onClick={() => setPromptOpen((v) => !v)}
          style={{
            width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
            background: "rgba(255,255,255,0.3)", border: "1px solid rgba(255,255,255,0.55)",
            borderRadius: promptOpen ? "16px 16px 0 0" : 16, padding: "12px 18px",
            fontSize: 13, fontWeight: 600, color: "#8c7089", cursor: "pointer",
            backdropFilter: "blur(8px)",
          }}
        >
          <span>🔍 命盤原始資料預覽</span>
          <span style={{ transform: promptOpen ? "rotate(180deg)" : "rotate(0deg)", display: "inline-block", transition: "transform 0.25s" }}>▾</span>
        </button>
        {promptOpen && (
          <div style={{
            background: "rgba(0,0,0,0.04)", border: "1px solid rgba(255,255,255,0.45)",
            borderTop: "none", borderRadius: "0 0 16px 16px", padding: "16px 18px",
            maxHeight: 320, overflowY: "auto",
          }}>
            <pre style={{ fontSize: 10, color: "#5c4059", whiteSpace: "pre-wrap", wordBreak: "break-all", margin: 0 }}>
              {JSON.stringify(c, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Match history */}
      <div>
        <p style={{ fontSize: 12, fontWeight: 700, color: "#b86e7d", marginBottom: 12 }}>
          ✦ 合盤記錄（連連看）
        </p>
        {matches.length === 0 ? (
          <p style={{ fontSize: 12, color: "#c4a0aa" }}>
            還沒有合盤記錄，
            <Link href="/lounge" style={{ color: "#d98695" }}>去解析命運</Link>
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {matches.map((m) => {
              const other = m.name_a?.toLowerCase().includes(profile.display_name.toLowerCase())
                ? m.name_b
                : m.name_a;
              return (
                <Link
                  key={m.id}
                  href={`/report/${m.id}`}
                  style={{
                    display: "flex", alignItems: "center", justifyContent: "space-between",
                    background: "rgba(255,255,255,0.3)", border: "1px solid rgba(255,255,255,0.55)",
                    borderRadius: 14, padding: "12px 16px", textDecoration: "none",
                    backdropFilter: "blur(8px)", transition: "all 0.2s",
                  }}
                >
                  <div>
                    <span style={{ fontSize: 13, fontWeight: 600, color: "#5c4059" }}>
                      {profile.display_name} × {other ?? "？"}
                    </span>
                    <span style={{ fontSize: 10, color: "#c4a0aa", marginLeft: 8 }}>
                      {new Date(m.created_at).toLocaleDateString("zh-TW")}
                    </span>
                  </div>
                  <span style={{ fontSize: 15, fontWeight: 700, color: "#b86e7d" }}>
                    ♥ {m.harmony_score ?? "—"}
                  </span>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}
```

**Step 3: Verify**

Navigate to http://localhost:3000/me — should see the profile card, planet data, and empty match history (or real matches if any exist).

**Step 4: Commit**

```bash
git add destiny-mvp/app/me/page.tsx destiny-mvp/app/me/MeClient.tsx
git commit -m "feat(me): personal chart page with yin-yang toggle + planet grid + match history"
```

---

## Task 6: NavBar — add /me link

**Files:**
- Modify: `destiny-mvp/components/NavBar.tsx`

**Context:**
Current NavBar has only the DESTINY logo link (left) and 登出 button (right). Add "我的命盤" link between them.

**Step 1: Add the link**

Find the `</Link>` closing tag after the DESTINY logo block, and after it (before the `<button onClick={handleLogout}`) add:

```tsx
<Link
  href="/me"
  style={{
    fontSize: 12,
    fontWeight: 600,
    color: pathname === "/me" ? "#b86e7d" : "#8c7089",
    textDecoration: "none",
    padding: "6px 14px",
    borderRadius: 999,
    background: pathname === "/me" ? "rgba(217,134,149,0.12)" : "transparent",
    border: pathname === "/me" ? "1px solid rgba(217,134,149,0.3)" : "1px solid transparent",
    transition: "all 0.2s",
  }}
>
  ✦ 我的命盤
</Link>
```

**Step 2: Verify**

NavBar now shows: `DESTINY logo` · `✦ 我的命盤` · `登出`. On `/me` route, the link is highlighted.

**Step 3: Commit**

```bash
git add destiny-mvp/components/NavBar.tsx
git commit -m "feat(nav): add /me link to NavBar"
```

---

## Task 7: Report page — save profile buttons

**Files:**
- Modify: `destiny-mvp/app/report/[id]/ReportClient.tsx`

**Context:**
After the collapsible chart section, add two "💾 儲存 X 的命盤" buttons (one for person A, one for B). Clicking calls `POST /api/profiles` with the chart data from `chartA`/`chartB` props.

**Step 1: Add save state and handler to ReportClient**

Add to the existing state declarations (after `const [chartOpen, setChartOpen] = useState(false);`):

```typescript
const [savingSlot, setSavingSlot] = useState<null | "A" | "B">(null);
const [saveLabel, setSaveLabel] = useState("");
const [saveMsg, setSaveMsg] = useState("");

async function saveProfile(slot: "A" | "B") {
  const name = slot === "A" ? nameA : nameB;
  const chart = slot === "A" ? chartA : chartB;
  if (!chart) { setSaveMsg("❌ 無命盤資料（請重新跑一次匹配）"); return; }
  setSaveMsg("儲存中...");
  const res = await fetch("/api/profiles", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      label: saveLabel || name,
      birth_date: chart["birth_date"] as string ?? "1990-01-01",
      birth_time: chart["birth_time_exact"] as string ?? undefined,
      lat: (chart["lat"] as number) ?? 25.033,
      lng: (chart["lng"] as number) ?? 121.565,
      data_tier: (chart["data_tier"] as number) ?? 3,
      gender: (chart["gender"] as string) ?? "M",
    }),
  });
  if (res.status === 403) { setSaveMsg("❌ 免費方案限 1 張命盤，升級解鎖更多"); setSavingSlot(null); return; }
  if (!res.ok) { setSaveMsg("❌ 儲存失敗"); setSavingSlot(null); return; }
  setSaveMsg("✓ 已儲存到我的命盤");
  setSavingSlot(null);
  setSaveLabel("");
  setTimeout(() => setSaveMsg(""), 4000);
}
```

**Step 2: Add save UI after the collapsible chart section**

After the closing `</div>` of the collapsible chart section (just before the final `</>`), add:

```tsx
{/* Save profile buttons */}
<div style={{ marginTop: 20, display: "flex", flexDirection: "column", gap: 10 }}>
  {savingSlot ? (
    <div style={{
      background: "rgba(255,255,255,0.35)", backdropFilter: "blur(12px)",
      border: "1px solid rgba(255,255,255,0.6)", borderRadius: 16, padding: "16px 20px",
    }}>
      <p style={{ fontSize: 12, color: "#8c7089", marginBottom: 10 }}>
        儲存 {savingSlot === "A" ? nameA : nameB} 的命盤：
      </p>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={saveLabel}
          onChange={(e) => setSaveLabel(e.target.value)}
          placeholder={`e.g. ${savingSlot === "A" ? nameA : nameB}`}
          style={{
            flex: 1, padding: "7px 12px", borderRadius: 10,
            border: "1px solid rgba(255,255,255,0.6)", background: "rgba(255,255,255,0.5)",
            fontSize: 12, color: "#5c4059",
          }}
        />
        <button
          onClick={() => saveProfile(savingSlot)}
          style={{ padding: "7px 18px", borderRadius: 10, background: "#d98695", color: "#fff", border: "none", fontSize: 12, cursor: "pointer" }}
        >
          確認
        </button>
        <button
          onClick={() => { setSavingSlot(null); setSaveLabel(""); setSaveMsg(""); }}
          style={{ padding: "7px 12px", borderRadius: 10, border: "1px solid rgba(200,160,170,0.4)", background: "transparent", fontSize: 12, color: "#8c7089", cursor: "pointer" }}
        >
          取消
        </button>
      </div>
    </div>
  ) : (
    <div style={{ display: "flex", gap: 10 }}>
      <button
        onClick={() => setSavingSlot("A")}
        style={{ flex: 1, padding: "10px", borderRadius: 12, background: "rgba(255,255,255,0.3)", border: "1px solid rgba(255,255,255,0.6)", fontSize: 12, color: "#8c7089", cursor: "pointer", backdropFilter: "blur(8px)" }}
      >
        💾 儲存 {nameA} 的命盤
      </button>
      <button
        onClick={() => setSavingSlot("B")}
        style={{ flex: 1, padding: "10px", borderRadius: 12, background: "rgba(255,255,255,0.3)", border: "1px solid rgba(255,255,255,0.6)", fontSize: 12, color: "#8c7089", cursor: "pointer", backdropFilter: "blur(8px)" }}
      >
        💾 儲存 {nameB} 的命盤
      </button>
    </div>
  )}
  {saveMsg && (
    <p style={{ fontSize: 12, color: saveMsg.startsWith("✓") ? "#34d399" : "#c0392b", textAlign: "center" }}>
      {saveMsg}
    </p>
  )}
</div>
```

**Step 3: Verify**

On any report page, scroll to bottom — should see two save buttons. Clicking one shows label input + confirm. Confirm → success message. Second save attempt → "免費方案限 1 張" message.

**Step 4: Commit**

```bash
git add destiny-mvp/app/report/[id]/ReportClient.tsx
git commit -m "feat(report): add save profile buttons for A and B"
```

---

## Done

All 7 tasks complete. The full feature:

- **Migration 014** extends `soul_cards` with `yin_yang`, `profile_card_data`, `ideal_match_data`, `updated_at`
- **`/api/profiles`** (GET/POST) and **`/api/profiles/[id]`** (PATCH/DELETE) wrap the table with auth + free tier enforcement
- **Lounge** shows a profile picker dropdown per BirthInput, skips `/calculate-chart` when cached, has inline save flow
- **`/me`** shows personal chart page: yin-yang toggle (persisted), planet grid, raw data preview, match history list
- **NavBar** has "✦ 我的命盤" link
- **Report page** has save buttons for each person

**Backlog (future):**
- `/me` prompt preview using `get_profile_prompt()` → solo LLM archetype card
- `/me` ideal match section using `/generate-ideal-match`
- Paid tier: increase save limit via user metadata
- Yin-yang visual on match report: show both persons' polarities
