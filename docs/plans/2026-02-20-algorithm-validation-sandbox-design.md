# Algorithm Validation Sandbox — Design Document

**Date:** 2026-02-20
**Phase:** Pre-Phase-E validation tool
**Goal:** Internal sandbox to validate Phase G matching algorithm against real-world couples before building Phase E (Progressive Unlock + Auto-Disconnect).

---

## Context

Phase G (`compute_match_v2`) is implemented and tested. Before shipping Phase E, we need to validate that the algorithm produces sensible scores for known couples. The sandbox provides a manual testing interface without requiring the dating app flow.

---

## Architecture

### Files Changed / Created

| File | Action | Purpose |
|---|---|---|
| `astro-service/sandbox.html` | Create | Standalone internal UI (open directly in browser) |
| `astro-service/main.py` | Modify | Add CORS middleware + `/generate-archetype` endpoint |

### No Next.js changes needed. No auth required. Open `sandbox.html` while `astro-service` runs on port 8001.

---

## UI Structure (sandbox.html)

Two-tab layout, vanilla HTML/JS/CSS, dark theme to match DESTINY aesthetic.

```
[Tab: Mechanism A — 伴侶驗證] [Tab: Mechanism B — 校時模擬]
```

---

## Mechanism A: Positive Control (伴侶驗證)

### Input Form

**Person A & B (side by side):**
- `name` (display only)
- `birth_date` (YYYY-MM-DD)
- `birth_time_exact` (HH:MM, optional)
- `lat` / `lng` (default: Taipei 25.033, 121.565)
- `data_tier` (1 / 2 / 3)
- `rpv_conflict` (cold_war / argue)
- `rpv_power` (control / follow)
- `rpv_energy` (home / out)
- `attachment_style` (anxious / avoidant / secure)

**Ground Truth select:**
- 已婚（穩定）
- 已分手（和平）
- 已分手（慘烈）
- 萬年好友

### Data Flow

```
form submit
  → POST /calculate-chart for Person A  → { sun_sign, moon_sign, mercury_sign, venus_sign,
                                             mars_sign, pluto_sign, saturn_sign, jupiter_sign,
                                             chiron_sign, juno_sign, house4_sign, house8_sign,
                                             bazi_element, ascendant_sign }
  → POST /calculate-chart for Person B  → same fields
  → merge chart data + RPV/attachment from form
  → POST /compute-match { user_a: {...}, user_b: {...} }
  → receive { lust_score, soul_score, power, tracks, primary_track, quadrant, labels }
  → apply MATCH/MISMATCH logic
  → render results panel
```

### Results Panel

```
test_id: auto-generated (timestamp-based, e.g. "A-20260220-001")
ground_truth: [label]
⬛⬛ MATCH  or  ⬜⬜ MISMATCH  (colored badge)

VibeScore (lust_score):      82 / 100
  logs: venus=0.85 × 0.20 | mars=0.90 × 0.25 | pluto=0.75 × 0.25 | power_fit=0.73 × 0.30
  bazi_clash multiplier: ×1.2

ChemistryScore (soul_score): 71 / 100
  logs: moon=0.75 × 0.25 | mercury=0.65 × 0.20 | saturn=0.80 × 0.20
        attachment=0.80 × 0.20 | juno=0.65 × 0.20
  bazi_generation multiplier: ×1.2

Tracks:  friend=45  passion=78  partner=62  soul=55
primary_track: passion
quadrant: lover
power: rpv=+25  viewer=Dom  target=Sub  frame_break=false
labels: ["#Magnetic", "#Intense", "#Transformative"]

[Generate AI Archetype + 解讀報告]
  ↓ (after click, calls /generate-archetype)
archetype_tags: ["Mirror Twins", "Power Clash"]
report: "你們之間流動著一種火星對金星的強烈磁力..."
```

### MATCH / MISMATCH Logic

| ground_truth | MATCH condition |
|---|---|
| 已婚（穩定）| `soul_score >= 65` AND `primary_track in ["partner", "soul"]` |
| 已分手（慘烈）| `(lust_score + soul_score) / 2 <= 55` |
| 已分手（和平）| `lust_score <= 60` AND `soul_score < 65` |
| 萬年好友 | `primary_track == "friend"` AND `lust_score <= 60` |

Thresholds exposed as editable fields in the UI for easy tuning.

---

## Mechanism B: Rectification Simulation (校時模擬)

### Purpose

Validate that the birth time rectification system can recover a precise time from a fuzzy input.

### Input

- `name`, `birth_date`, `precise_time` (the "ground truth" time, e.g. "14:30")
- `lat` / `lng`

### Simulation Flow

1. Map precise_time → FUZZY_DAY slot (morning/afternoon/evening based on hour)
2. Initial state: `accuracy_type=FUZZY_DAY`, `confidence=0.15`, `window=360 min`
3. Display 5 hardcoded Via Negativa questions (from Phase B.5 spec)
4. User answers each [Yes] / [No]
5. Each answer: `confidence += 0.10`, window narrows by ~30%
6. After all 5: check if `precise_time` falls within final window
7. Result: **PASS** (time within window) or **FAIL** (time outside window)

### Sample Questions (hardcoded for V1)

From the Phase B.5 Via Negativa spec:
1. "你傾向強烈的目標導向而非隨流行事？"
2. "你在人群中通常是主動開口的那一個？"
3. "面對衝突你傾向直接說出來而非沉默？"
4. "你的精力在早晨比晚上更充沛？"
5. "你做決定時直覺多於分析？"

### Display

```
Original time:  14:30  (afternoon slot: 12:00-18:00)
Initial window: ±180 min from 15:00  →  12:00-18:00

Q1: ... [Yes] [No]
  → window: 12:00-16:30  confidence: 0.25
Q2: ... [Yes] [No]
  → window: 13:00-16:30  confidence: 0.35
...
Final window: 13:00-16:00  confidence: 0.75

Ground truth 14:30 is WITHIN window → ✅ PASS
```

---

## New Endpoint: `/generate-archetype`

Added to `astro-service/main.py`.

```python
class ArchetypeRequest(BaseModel):
    match_data: dict          # full compute_match_v2 output
    person_a_name: str = "A"
    person_b_name: str = "B"
    language: str = "zh-TW"

# POST /generate-archetype
# Reads ANTHROPIC_API_KEY from env
# Calls Claude API: claude-haiku-4-5-20251001 (fast + cheap for sandbox)
# Returns:
{
  "archetype_tags": ["Mirror Twins", "Power Clash", "Slow Burn"],
  "report": "你們之間流動著一種..."
}
```

Prompt template uses: lust_score, soul_score, primary_track, quadrant, labels, power.rpv, power.viewer_role.

---

## CORS

Add `CORSMiddleware` to astro-service to allow `null` origin (file:// HTML).

```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
```

---

## Implementation Tasks

1. Add CORS middleware to `astro-service/main.py`
2. Add `/generate-archetype` endpoint to `astro-service/main.py`
3. Build `astro-service/sandbox.html` — Mechanism A form + results panel
4. Add Mechanism B tab to sandbox.html
5. Add ANTHROPIC_API_KEY to astro-service env (`.env` or system env)
6. Manual validation: test with 2-3 real couples

---

## Test Cases to Validate

| test_id | ground_truth | Expected |
|---|---|---|
| T01 | 已婚（穩定） | soul_score ≥ 65, partner/soul track dominant |
| T02 | 已分手（慘烈） | avg(lust,soul) ≤ 55 |
| T03 | 萬年好友 | friend track primary, lust ≤ 60 |
| T04 | Rectification B | true time within narrowed window |
