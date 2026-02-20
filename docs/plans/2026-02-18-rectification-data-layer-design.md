# Rectification Data Layer Design

> **Date:** 2026-02-18
> **Scope:** Data collection layer adjustments to support Dynamic Birth Time Rectification
> **Phase:** Spec only — DB schema, API contract, UX flow redesign
> **Status:** Draft

---

## 1. Background & Motivation

`Dynamic_BirthTimeRectification_Spec.md` 定義了一套完整的出生時間校正系統，但目前的 codebase 只有基礎的資料收集（birth_date / birth_time / birth_time_exact / data_tier），缺少校正所需的資料結構。

### 1.1 Current vs. Spec Gap Summary

| Aspect | Current Implementation | Spec Requirement | Gap |
|--------|----------------------|------------------|-----|
| Birth time precision | `precise/morning/afternoon/evening/unknown` (dropdown) | `PRECISE/TWO_HOUR_SLOT/FUZZY_DAY` (guided flow) | Missing TWO_HOUR_SLOT; no guided UX |
| Time window | Only `birth_time_exact` (TIME) | `window_start/end` + `windowSizeMinutes` | No interval representation |
| Rectification state | None | `status/confidence/activeRange/calibratedTime/d9Slot/boundaryCase` | Entirely missing |
| Event log | None | `rectification_events` table | Entirely missing |
| User tags | None | `dealbreakers[]` + `priorities` | Entirely missing |
| DB constraint bug | `birth_time CHECK` excludes `evening` | Should include `evening` | Bug |
| Boundary case detection | None | Moon sign change + BaZi 身強/身弱 crossing + **Asc/Dsc sign change** | Entirely missing |

### 1.2 Design Philosophy

> **「從被動宿命到主動創造」** — 這套架構不只是算命，而是提供一張「關係導航圖」。
> - 八字告訴你相處的姿態
> - 西占告訴你吸引的成因
> - 時間不確定？沒關係，系統會帶你逐步校正

UI 語言保持現代、賦能感，避免「算命」氛圍。時間選項用一般時段呈現（01:00-03:00），不刻意使用傳統時辰名稱。

---

## 2. Database Schema Changes

### 2.1 Migration: `005_rectification.sql`

Strategy: **Additive migration** — 新增欄位，不破壞現有 API。舊欄位（`birth_time`, `data_tier`）保留供向下相容。

#### 2.1.1 New columns on `users` table

```sql
-- ============================================================
-- Birth Time Precision (spec §3.1)
-- ============================================================
-- AccuracyType: the user's declared precision level
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS accuracy_type TEXT
CHECK (accuracy_type IN ('PRECISE', 'TWO_HOUR_SLOT', 'FUZZY_DAY'));

-- The user's declared time window (original input, never mutated by rectification)
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS window_start TIME;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS window_end TIME;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS window_size_minutes INT;

-- ============================================================
-- Rectification State (spec §4)
-- ============================================================
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS rectification_status TEXT DEFAULT 'unrectified'
CHECK (rectification_status IN (
  'unrectified',
  'collecting_signals',
  'narrowed_to_2hr',
  'narrowed_to_d9',
  'locked',
  'needs_review'
));

ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS current_confidence DECIMAL(3,2) DEFAULT 0.00;

-- System's refined range (mutated by rectification engine)
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS active_range_start TIMESTAMPTZ;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS active_range_end TIMESTAMPTZ;

-- Final locked result
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS calibrated_time TIMESTAMPTZ;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS active_d9_slot INT
CHECK (active_d9_slot BETWEEN 1 AND 9);

-- Boundary case flag
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS is_boundary_case BOOLEAN DEFAULT FALSE;

-- ============================================================
-- User Tags (spec §4, for future Via Negativa quiz)
-- ============================================================
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS dealbreakers JSONB DEFAULT '[]'::jsonb;

ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS priorities TEXT
CHECK (priorities IN ('Achievement', 'LifeQuality'));

-- ============================================================
-- Fix existing constraint: add 'evening'
-- ============================================================
ALTER TABLE public.users DROP CONSTRAINT IF EXISTS users_birth_time_check;
ALTER TABLE public.users ADD CONSTRAINT users_birth_time_check
CHECK (birth_time IN ('precise', 'morning', 'afternoon', 'evening', 'unknown'));
```

#### 2.1.2 New table: `rectification_events`

```sql
CREATE TABLE public.rectification_events (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  source     TEXT NOT NULL CHECK (source IN (
    'signup', 'daily_quiz', 'interaction', 'post_date_feedback', 'admin'
  )),
  event_type TEXT NOT NULL CHECK (event_type IN (
    'range_initialized',
    'range_narrowed',
    'candidate_eliminated',
    'confidence_updated',
    'locked',
    'flagged_needs_review'
  )),
  payload    JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for efficient user event queries
CREATE INDEX idx_rectification_events_user
  ON public.rectification_events(user_id, created_at);

-- RLS: users can only read their own events
ALTER TABLE public.rectification_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own rectification events"
  ON public.rectification_events FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "System can insert rectification events"
  ON public.rectification_events FOR INSERT
  WITH CHECK (auth.uid() = user_id);
```

### 2.2 Column Mapping: Spec TypeScript ↔ DB

| Spec Interface | Spec Field | DB Column | Type |
|----------------|-----------|-----------|------|
| `BirthTimeInput` | `providedTime` | `birth_time_exact` | TIME |
| `BirthTimeInput` | `accuracyType` | `accuracy_type` | TEXT enum |
| `BirthTimeInput` | `windowSizeMinutes` | `window_size_minutes` | INT |
| (new) | — | `window_start` / `window_end` | TIME |
| `RectificationState` | `status` | `rectification_status` | TEXT enum |
| `RectificationState` | `currentConfidence` | `current_confidence` | DECIMAL(3,2) |
| `RectificationState` | `activeRangeStart` | `active_range_start` | TIMESTAMPTZ |
| `RectificationState` | `activeRangeEnd` | `active_range_end` | TIMESTAMPTZ |
| `RectificationState` | `calibratedTime` | `calibrated_time` | TIMESTAMPTZ |
| `RectificationState` | `activeD9Slot` | `active_d9_slot` | INT (1-9) |
| `RectificationState` | `isBoundaryCase` | `is_boundary_case` | BOOLEAN |
| `RectificationEvent` | — | `rectification_events` table | — |
| `UserTags` | `dealbreakers` | `dealbreakers` | JSONB |
| `UserTags` | `priorities` | `priorities` | TEXT enum |

---

## 3. Onboarding UX Redesign: Birth Data Page

### 3.1 Flow Architecture

```
Step 1: Birth Date + Birth Place (unchanged)
         ↓
Step 2: Guided Time Precision (NEW — 4 tappable cards)
         ↓ (conditional)
Step 2a: Sub-selection (time picker / 2hr slot grid / 3-option / skip)
         ↓
Step 3: Tier indicator (enhanced messaging)
         ↓
[Continue] → API call → next step
```

### 3.2 Guided Time Precision Cards

Question label:「你對出生時間的了解程度？」

| Card | Icon | Title | Sub-label | accuracy_type | Next action |
|------|------|-------|-----------|---------------|-------------|
| A | `verified` | 我有精確時間 | 出生證明或家人確認 | `PRECISE` | Show `<input type="time">` |
| B | `timelapse` | 我知道大概時段 | 約兩小時的範圍 | `TWO_HOUR_SLOT` | Show 12-slot grid |
| C | `wb_twilight` | 我只知道大概 | 早上、下午或晚上 | `FUZZY_DAY` | Show 3 options |
| D | `help` | 我完全不知道 | 沒關係，我們會幫你找到 | `FUZZY_DAY` | Proceed directly |

### 3.3 TWO_HOUR_SLOT Grid (12 slots)

Display as a 4×3 grid of tappable pills:

```
23:00 - 01:00    01:00 - 03:00    03:00 - 05:00    05:00 - 07:00
07:00 - 09:00    09:00 - 11:00    11:00 - 13:00    13:00 - 15:00
15:00 - 17:00    17:00 - 19:00    19:00 - 21:00    21:00 - 23:00
```

Each slot maps to: `window_start`, `window_end`, `window_size_minutes = 120`

### 3.4 FUZZY_DAY Sub-options

| Option | Time Range | window_start | window_end | window_size_minutes | birth_time (compat) |
|--------|-----------|-------------|-----------|--------------------|--------------------|
| 早上 | 06:00 - 12:00 | 06:00 | 12:00 | 360 | `morning` |
| 下午 | 12:00 - 18:00 | 12:00 | 18:00 | 360 | `afternoon` |
| 晚上 | 18:00 - 24:00 | 18:00 | 00:00 | 360 | `evening` |
| (Card D: 不知道) | 00:00 - 24:00 | 00:00 | 00:00 | 1440 | `unknown` |

### 3.5 Tier Indicator Enhancement

| accuracy_type | Tier | Badge | Message |
|---------------|------|-------|---------|
| `PRECISE` | Gold (1) | 黃金 | 完整 D1 & D9 星盤分析，最高精確配對 |
| `TWO_HOUR_SLOT` | Silver (2) | 白銀 | 中等精確度，大部分功能可用 |
| `FUZZY_DAY` (morning/afternoon/evening) | Silver (2) | 白銀 | 模糊邏輯中等精確度 |
| `FUZZY_DAY` (unknown) | Bronze (3) | 青銅 | 基礎相容性。別擔心，後續問答會幫你逐步提升精準度 |

---

## 4. API Contract: `POST /api/onboarding/birth-data`

### 4.1 Request Body (updated)

```typescript
interface BirthDataRequest {
  // Existing fields (preserved for backward compat)
  birth_date: string         // "1995-06-15"
  birth_city: string         // "台北市"
  birth_lat?: number         // 25.033
  birth_lng?: number         // 121.5654

  // New fields (from guided UX)
  accuracy_type: 'PRECISE' | 'TWO_HOUR_SLOT' | 'FUZZY_DAY'
  birth_time_exact?: string  // "14:30" (only if PRECISE)
  window_start?: string      // "13:00" (if TWO_HOUR_SLOT or FUZZY_DAY)
  window_end?: string        // "15:00"
  window_size_minutes?: number // 0 | 120 | 360 | 1440
}
```

### 4.2 Response Body

```typescript
interface BirthDataResponse {
  user: {
    id: string
    birth_date: string
    birth_city: string
    birth_lat: number | null
    birth_lng: number | null
    // Backward-compat fields (legacy)
    birth_time: 'precise' | 'morning' | 'afternoon' | 'evening' | 'unknown'
    birth_time_exact: string | null   // 'HH:mm'
    data_tier: 1 | 2 | 3
    // New rectification fields
    accuracy_type: 'PRECISE' | 'TWO_HOUR_SLOT' | 'FUZZY_DAY'
    window_start: string | null
    window_end: string | null
    window_size_minutes: number | null
    rectification_status: RectificationStatus
    current_confidence: number
    is_boundary_case: boolean
    boundary_reasons: string[]        // e.g. ['ascendant_descendant_sign_change']
  }
  // Whether to immediately show rectification questions
  show_immediate_rectification: boolean
  // Pre-fetched first question (if show_immediate_rectification = true)
  first_question?: {
    question_id: string
    phase: 'coarse' | 'fine'
    question_text: string
    options: { id: 'A' | 'B'; label: string; eliminates: string[] }[]
  }
}
```

### 4.3 API Logic

```
1. Validate required fields (birth_date, birth_city, accuracy_type)
2. Compute data_tier:
   - PRECISE → 1
   - TWO_HOUR_SLOT → 2
   - FUZZY_DAY + (morning/afternoon/evening) → 2
   - FUZZY_DAY + unknown → 3
3. Compute birth_time for backward compat:
   - PRECISE → 'precise'
   - TWO_HOUR_SLOT → map window to nearest period ('morning'/'afternoon'/'evening')
   - FUZZY_DAY → 'morning'/'afternoon'/'evening'/'unknown'
4. Initialize rectification state:
   - rectification_status = 'unrectified'
   - current_confidence = initial value based on accuracy_type:
     - PRECISE → 0.9
     - TWO_HOUR_SLOT → 0.3
     - FUZZY_DAY (period) → 0.15
     - FUZZY_DAY (unknown) → 0.05
   - active_range_start/end = birth_date + window_start/end as TIMESTAMPTZ
5. Detect boundary cases (see §5)
6. Log rectification event:
   {
     source: 'signup',
     event_type: 'range_initialized',
     payload: { accuracy_type, window_start, window_end, is_boundary_case, initial_confidence }
   }
7. Upsert to users table (all new + legacy columns)
8. Call astro-service (non-blocking, same as current)
9. Return updated user data
```

---

## 4.4 Rectification Quiz Endpoints

### `GET /api/rectification/next-question`

完整規格見 `Dynamic_BirthTimeRectification_Spec.md` §14.1。

**選題優先度（實作重點）：**
```typescript
function selectNextQuestion(user: User): Question | null {
  if (user.rectification_status === 'locked') return null
  if (getDaysSinceLastQuestion(user) < 1) return null  // rate limit: 1/day

  const priorityOrder = getBoundaryReasonPriority(user.boundary_reasons)
  // ['ascendant_descendant_sign_change', 'moon_sign_change', 'bazi_hour_pillar_change']

  for (const reason of priorityOrder) {
    const q = questionBank.findByReason(reason, user.answered_question_ids)
    if (q) return q
  }

  // fallback: information gain maximization over remaining D9 slots
  return questionBank.maxInfoGain(user.active_d9_slots_remaining, user.answered_question_ids)
}
```

### `POST /api/rectification/answer`

完整規格見 `Dynamic_BirthTimeRectification_Spec.md` §14.2。

**信心值更新公式：**
```typescript
function updateConfidence(current: number, remaining: number, total: number, hasContradiction: boolean): number {
  const candidateRatio = 1 - (remaining / total)          // 消除越多候選，信心越高
  const raw = current + (candidateRatio * (1 - current) * 0.4)  // 每題最多貢獻 40% 的剩餘空間
  return hasContradiction ? raw * 0.8 : raw               // 矛盾答案打 8 折
}
```

---

## 5. Boundary Case Detection

### 5.1 Why It Matters

出生時間的微小誤差在以下情況會造成星盤的重大變動：

| Factor | 變動頻率 | 影響層面 | 對配對的重要性 |
|--------|---------|---------|--------------|
| **Ascendant (上升星座)** | ~2hr/sign | 第一印象、人格面具 | High — 影響初次互動吸引 |
| **Descendant (下降星座)** | ~2hr/sign (= Asc 對面) | 理想伴侶類型、關係模式 | **Critical** — 直接決定配對邏輯核心 |
| **MC/IC 軸線** | ~2hr/sign | 事業/家庭取向 | Medium |
| **Moon sign (月亮星座)** | ~2.5 days/sign | 情緒需求、安全感模式 | High |
| **BaZi 時柱** | 2hr/pillar | 外在解題手段、社交面 | High |
| **BaZi 身強/身弱** | varies | 社交能量、主導性 | Medium |

### 5.2 Descendant (下降星座) 的特殊重要性

> **Descendant = Ascendant 正對面（180°）**，代表「你被什麼樣的人吸引」、「你在關係中需要什麼」。

對交友平台而言，Descendant 是配對的核心參數之一：
- Descendant 在 Aries → 被直接、有主見的人吸引
- Descendant 在 Libra → 被溫和、講求平衡的人吸引
- 當使用者的時間窗口橫跨 Ascendant 換座點，**Descendant 同時換座**，配對邏輯會完全翻轉

因此 Boundary Case 偵測必須同時考慮：
1. Ascendant 是否在窗口內換座（同時意味著 Descendant 也換座）
2. 換座對「配對核心參數」的影響程度

### 5.3 MVP Boundary Case Detection Rules

Phase 1 (本次 data layer scope)：**Flag only, don't resolve**

```typescript
function detectBoundaryCase(
  birthDate: string,
  windowStart: string,   // TIME
  windowEnd: string,     // TIME
  lat: number,
  lng: number,
  accuracyType: AccuracyType
): { isBoundary: boolean; reasons: string[] } {
  // Rule 1: PRECISE users are never boundary cases
  if (accuracyType === 'PRECISE') return { isBoundary: false, reasons: [] }

  const reasons: string[] = []

  // Rule 2: BaZi 時辰 boundary
  // If the window straddles a 2-hour 時辰 boundary (odd hours: 01, 03, 05...)
  // → 時柱 may change within the window
  if (windowStraddlesBaZiBoundary(windowStart, windowEnd)) {
    reasons.push('bazi_hour_pillar_change')
  }

  // Rule 3: Ascendant/Descendant sign change
  // Compute Ascendant at window_start and window_end
  // If they differ → Asc (and therefore Dsc) changes within window
  // This is the most critical boundary for matchmaking
  const ascStart = computeAscendant(birthDate, windowStart, lat, lng)
  const ascEnd = computeAscendant(birthDate, windowEnd, lat, lng)
  if (ascStart !== ascEnd) {
    reasons.push('ascendant_descendant_sign_change')
  }

  // Rule 4: Moon sign change (if applicable)
  // Moon moves ~13°/day, changes sign every ~2.5 days
  // For windows > 2 hours, check if moon changes sign
  const moonStart = computeMoonSign(birthDate, windowStart, lat, lng)
  const moonEnd = computeMoonSign(birthDate, windowEnd, lat, lng)
  if (moonStart !== moonEnd) {
    reasons.push('moon_sign_change')
  }

  return {
    isBoundary: reasons.length > 0,
    reasons
  }
}
```

偵測結果存入：
- `is_boundary_case = true/false`
- `rectification_events.payload.boundary_reasons = [...]`

> **Note:** Rule 3 (Asc/Dsc) 需要 astro-service 支援「給定時間計算 Ascendant」的能力。目前 `calculate-chart` 已回傳 `ascendant_sign`，但只接受單一時間點。需要擴充 astro-service 新增 endpoint 或在 birth-data API 呼叫兩次（window start + window end）。

### 5.4 Boundary Case 對後續校正的影響

| is_boundary_case | 後續行為 |
|------------------|---------|
| `false` | 正常校正流程，題目照排 |
| `true` (bazi_hour_pillar_change) | 提高 BaZi 相關校正題的優先度 |
| `true` (ascendant_descendant_sign_change) | **最高優先** — 提前觸發上升/下降排除題（spec §7.4.1），直接影響配對核心 |
| `true` (moon_sign_change) | 提高月亮情緒崩潰題的優先度（spec §6.3.1） |

---

## 6. Spec Amendments

以下修正建議應回寫到 `Dynamic_BirthTimeRectification_Spec.md`：

### 6.1 §3.1 — Clarify FUZZY_DAY sub-values

```diff
+ FUZZY_DAY 包含以下子分類：
+   - morning (06:00-12:00)
+   - afternoon (12:00-18:00)
+   - evening (18:00-24:00)
+   - unknown (00:00-24:00, 完全不知道)
```

### 6.2 §4 — Add `window_start/end` to BirthTimeInput

```diff
  export interface BirthTimeInput {
    providedTime: string | null;
    accuracyType: AccuracyType;
    windowSizeMinutes: number;
+   windowStart: string | null;   // 'HH:mm' — user's original declared window start
+   windowEnd: string | null;     // 'HH:mm' — user's original declared window end
  }
```

Reason: `activeRangeStart/End` is mutable (refined by rectification), but `windowStart/End` preserves the user's original input for audit trail.

### 6.3 §3.3 — Add Ascendant/Descendant to Boundary Case Detection

```diff
  - **Boundary Case 標記**
    - 若接近時辰交界或關鍵天象切換點，標記：`isBoundaryCase = true`
+   - 偵測項目：
+     1. BaZi 時柱交界（2 小時時辰邊界）
+     2. **上升/下降星座換座**（Ascendant/Descendant sign change）
+        — 下降星座 (Descendant) 代表理想伴侶類型，為配對核心參數。
+        若窗口內 Asc/Dsc 換座，此為最高優先邊界案例。
+     3. 月亮換座（若窗口 > 2 小時且當天月亮移動足以跨座）
    - Boundary Case 會提高後續校正題目的優先度。
+   - Boundary Case reason 記錄於 rectification_events payload。
```

### 6.4 §6.1 — Add Descendant-driven coarse filter

```diff
  ### 6.1 目的
  - 把大範圍（FUZZY_DAY）或不穩定的時間，先收斂到可用的 2 小時區間。
  - 優先使用「情緒地雷／崩潰點」做切分，讓使用者用反問題更容易給出強訊號。
+ - **若偵測到 Ascendant/Descendant 換座 (boundary case)**，優先使用上升排除法（§7.4.1）
+   作為粗過濾手段，因為 Descendant 直接影響配對核心邏輯。
```

### 6.5 §11 — Tier upgrade path

```diff
  ### Tier 2
  - 可輸出：模糊盤的區間結果（帶 Uncertain 標記）
+ - TWO_HOUR_SLOT 使用者初始為 Tier 2
+ - 若 rectification_status = 'locked' 且 current_confidence >= 0.8：
+   自動升級為 Tier 1，解鎖完整盤面與高精度媒合
```

### 6.6 New Section: Astro-Service Extension Needed

```
### 12.3 Astro-Service: Boundary Detection Support

For boundary case detection, the astro-service needs to support
computing Ascendant for arbitrary time points (not just the user's
declared time). Two options:

**Option A: New endpoint**
  POST /compute-ascendant
  { birth_date, time, lat, lng } → { ascendant_sign }

**Option B: Call /calculate-chart twice**
  Call existing endpoint with window_start and window_end,
  compare ascendant_sign in both responses.

Recommendation: Option B for MVP (no new endpoint needed),
Option A when performance matters (lighter computation).
```

---

## 7. TypeScript Types Update

New fields to add to `src/lib/supabase/types.ts` (users Row/Insert/Update):

```typescript
// Birth time precision
accuracy_type: 'PRECISE' | 'TWO_HOUR_SLOT' | 'FUZZY_DAY' | null
window_start: string | null    // TIME as 'HH:mm'
window_end: string | null
window_size_minutes: number | null

// Rectification state
rectification_status: 'unrectified' | 'collecting_signals' | 'narrowed_to_2hr' | 'narrowed_to_d9' | 'locked' | 'needs_review'
current_confidence: number     // 0.00 - 1.00
active_range_start: string | null  // ISO datetime
active_range_end: string | null
calibrated_time: string | null
active_d9_slot: number | null  // 1-9
is_boundary_case: boolean

// User tags
dealbreakers: string[]         // JSON array
priorities: 'Achievement' | 'LifeQuality' | null
```

New table: `rectification_events`:

```typescript
rectification_events: {
  Row: {
    id: string
    user_id: string
    source: 'signup' | 'daily_quiz' | 'interaction' | 'post_date_feedback' | 'admin'
    event_type: 'range_initialized' | 'range_narrowed' | 'candidate_eliminated' | 'confidence_updated' | 'locked' | 'flagged_needs_review'
    payload: Json
    created_at: string
  }
  // Insert/Update omitted for brevity
}
```

---

## 8. Files to Modify

| File | Change Type | Description |
|------|------------|-------------|
| `supabase/migrations/005_rectification.sql` | **New** | Add columns + events table + fix evening constraint |
| `src/lib/supabase/types.ts` | Edit | Add new columns + rectification_events table types |
| `src/app/onboarding/birth-data/page.tsx` | Rewrite | Card-style guided flow + 12-slot grid + conditional sub-selections |
| `src/app/api/onboarding/birth-data/route.ts` | Edit | Accept new fields, compute backward-compat values, init rectification state, log event, boundary detection |
| `src/__tests__/api/onboarding-birth-data.test.ts` | Edit | Add tests for PRECISE/TWO_HOUR_SLOT/FUZZY_DAY + boundary detection + event logging |
| `docs/Dynamic_BirthTimeRectification_Spec.md` | Edit | Apply amendments from §6 of this document |
| `docs/MVP-PROGRESS.md` | Edit | Update progress tracker |

---

## 9. Initial Confidence Values

| accuracy_type | Condition | initial_confidence | Rationale |
|---------------|----------|-------------------|-----------|
| `PRECISE` | Has exact HH:mm | 0.90 | High but not 1.0 — birth certificates can have ±5min rounding |
| `TWO_HOUR_SLOT` | 2hr window selected | 0.30 | One 時辰 = 1 of 12 possibilities |
| `FUZZY_DAY` | morning/afternoon/evening | 0.15 | 6hr = 3 時辰 candidates |
| `FUZZY_DAY` | unknown | 0.05 | Full day = 12 時辰 candidates |

---

## 10. Data Flow Diagram

```
User (Frontend)
  │
  ├─ birth_date, birth_city (unchanged)
  ├─ accuracy_type (NEW: card selection)
  ├─ birth_time_exact (if PRECISE)
  ├─ window_start/end (if TWO_HOUR_SLOT or FUZZY_DAY)
  │
  ▼
POST /api/onboarding/birth-data
  │
  ├─ Validate input
  ├─ Compute data_tier (backward compat)
  ├─ Compute birth_time (backward compat)
  ├─ Initialize rectification state
  │   ├─ rectification_status = 'unrectified'
  │   ├─ current_confidence = f(accuracy_type)
  │   └─ active_range_start/end = birth_date + window
  │
  ├─ Detect boundary cases
  │   ├─ BaZi 時柱 boundary check
  │   ├─ Ascendant/Descendant sign change check (via astro-service)
  │   └─ Moon sign change check (via astro-service)
  │
  ├─ Log rectification event (range_initialized)
  │
  ├─ Upsert users table
  │
  ├─ Call astro-service /calculate-chart (non-blocking)
  │   └─ Write back: sun_sign, moon_sign, ascendant_sign, bazi, etc.
  │
  └─ Return updated user data
```

---

## 11. Open Questions (for future phases)

1. ~~**Rectification quiz integration point**~~ → ✅ **已決定：混合觸發**
   - Phase 1（Onboarding 後）：accuracy_type ≠ PRECISE 時，soul report 後立即出 1-2 題粗過濾
   - Phase 2（Daily）：每日 Daily Feed 前出 1 題，rate limit 1/day，status ≠ locked 時持續
   - Phase 3（Profile）：顯示 `current_confidence` 進度 badge + "精準我的星盤" CTA
   - 完整流程見 `Dynamic_BirthTimeRectification_Spec.md` §15

2. **Astro-service performance:** boundary detection 呼叫 astro-service 兩次（window_start + window_end）。
   - MVP：可接受（非阻塞，signup 路徑不影響 UX）
   - 未來優化：新增輕量 `POST /astro/ascendant` endpoint（見 spec §12.3）

3. **Confidence decay:** 若用戶 N 天未回答校正題，confidence 是否下降？
   - **建議：不做 decay**（MVP 期）。Confidence 只能上升或在 `needs_review` 時重置（有 log）。
   - 未來可加：> 90 天未登入且 status ≠ locked，降為 `needs_review`，提醒重新確認。

4. **D9 slot computation:** D9（Navamsa）細過濾需要 Navamsa chart 計算 — astro-service 目前不支援。
   - **MVP 替代方案：** D9 slot 用時間均分（2 小時 ÷ 9 = ~13 分鐘/slot），以標準西占行星位置做 proxy 過濾，而非真正的 Navamsa 宮位。
   - 真正 Navamsa 支援列入 Phase C+ backlog。

5. **Dealbreakers collection timing:** 在 onboarding 收（有摩擦）或之後收（可能永遠不填）？
   - **建議：** Onboarding 後（混合校正流程的 Phase 1）同步收集 dealbreakers 1-2 題，與粗過濾題一起呈現，不單獨作為一個步驟。
