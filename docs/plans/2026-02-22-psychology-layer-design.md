# Psychology Layer (Phase I) — Design Document

**Date:** 2026-02-22
**Status:** Approved — ready for implementation

---

## Goal

Add a Psychology Layer to the DESTINY algorithm that computes per-user psychological tags at chart time, and pairwise soul/lust/partner modifiers at match time. This gives the system the ability to detect S/M dynamics, karmic degree vulnerabilities, elemental soul deficiencies, shadow/wound triggers, and attachment trap patterns — without touching the existing WEIGHTS architecture.

---

## Architecture

```
Phase I — Per-user (chart time → stored in DB)
  chart.py → psychology.py
  ├── extract_sm_dynamics(chart)         → sm_tags: List[str]
  ├── extract_critical_degrees(chart, is_exact_time)  → karmic_tags: List[str]
  └── compute_element_profile(chart)     → element_profile: {counts, deficiency, dominant}
  ↓ Stored in users table via birth-data API (Migration 009)

Phase II — Pairwise (match time → additive modifiers)
  matching.py / compute_match_v2() final stage
  ├── shadow_engine.compute_shadow_and_wound(a, b)
  │   → soul_mod, lust_mod, high_voltage, shadow_tags
  ├── compute_dynamic_attachment(base_a, base_b, chart_a, chart_b)
  │   → dyn_att_a, dyn_att_b (synastry-adjusted attachment type)
  ├── compute_attachment_dynamics(dyn_att_a, dyn_att_b)
  │   → soul_mod, partner_mod, lust_mod, high_voltage, trap_tag
  └── compute_elemental_fulfillment(element_profile_a, element_profile_b)
      → soul_bonus (per deficiency filled: +15, capped)
  → All mods summed → applied to tracks["soul/passion/partner"]
  → high_voltage: one-veto rule (any module can trigger it)

Phase III — Planning note only
  MVP-PROGRESS.md: Mode Filter (Hunt / Nest / Abyss) future roadmap
```

---

## File Plan

| File | Action | Contains |
|------|--------|----------|
| `astro-service/psychology.py` | **Create** | `PSYCH_DRIVES`, `extract_sm_dynamics`, `extract_critical_degrees`, `compute_element_profile` |
| `astro-service/shadow_engine.py` | **Create** | `compute_shadow_and_wound`, `compute_dynamic_attachment`, `compute_attachment_dynamics`, `compute_elemental_fulfillment` |
| `astro-service/chart.py` | **Modify** | Import psychology, call 3 functions at end of `calculate_chart`, add to result dict |
| `astro-service/main.py` | **Modify** | Pass `is_exact_time` to psychology functions; return new fields from `/calculate-chart` |
| `astro-service/matching.py` | **Modify** | Import shadow_engine; add Phase II modifier block at end of `compute_match_v2` |
| `supabase/migrations/009_psychology_tags.sql` | **Create** | Add `sm_tags JSONB`, `karmic_tags JSONB`, `element_profile JSONB` to users |
| `destiny-app/src/lib/supabase/types.ts` | **Modify** | Add 3 new columns to Database.public.Tables.users type |
| `destiny-app/src/app/api/onboarding/birth-data/route.ts` | **Modify** | Write sm_tags, karmic_tags, element_profile returned by astro-service into users row |
| `astro-service/test_psychology.py` | **Create** | pytest tests for all 3 per-user functions |
| `astro-service/test_shadow_engine.py` | **Create** | pytest tests for shadow + attachment + element fulfillment |
| `docs/MVP-PROGRESS.md` | **Modify** | Add Phase I entry (Done) + Phase I.5 future note (Mode Filter) |

---

## Section 1: `psychology.py` (Per-user extraction)

### 1a. S/M Dynamics — `extract_sm_dynamics(chart)`

**Input:** chart dict with `*_degree` and `*_sign` keys
**Output:** `List[str]` — up to 8 tags
**Orb:** 8° for all aspects

| Tag | Trigger condition |
|-----|-------------------|
| `Natural_Dom` | sun/mars conjunct/trine pluto |
| `Daddy_Dom` | saturn conjunct/trine sun |
| `Sadist_Dom` | mars square/opposition pluto |
| `Anxious_Sub` | moon tension (conj/sq/opp) with pluto or neptune |
| `Brat_Sub` | mercury tension with mars |
| `Service_Sub` | venus_sign in [Taurus, Virgo, Capricorn] |
| `Masochist_Sub` | mars tension/conjunction with neptune |

No Tier restriction — all use `*_degree` which is available regardless of birth time precision.

### 1b. Critical Degrees — `extract_critical_degrees(chart, is_exact_time)`

**Reliable always (Tier 1/2/3):** sun, mercury, venus, mars
**Tier 1 only:** moon, asc (fast-moving — unreliable without precise birth time)

| Tag | Trigger |
|-----|---------|
| `Karmic_Crisis_{POINT}` | `degree % 30 >= 29.0` |
| `Blind_Impulse_{POINT}` | `degree % 30 < 1.0` |

Outer planets (Jupiter, Saturn, Uranus, Neptune, Pluto) deliberately excluded — they stay in one degree for too long to be personal markers.

### 1c. Element Profile — `compute_element_profile(chart)`

**Planets counted:** sun, moon, mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto (10 total)

```python
{
  "counts": {"Fire": 3, "Earth": 1, "Air": 4, "Water": 2},
  "deficiency": ["Earth"],   # count <= 1
  "dominant": ["Air"]        # count >= 4
}
```

---

## Section 2: Supabase — Migration 009

```sql
ALTER TABLE users
  ADD COLUMN sm_tags        JSONB DEFAULT '[]',
  ADD COLUMN karmic_tags    JSONB DEFAULT '[]',
  ADD COLUMN element_profile JSONB DEFAULT NULL;
```

- Computed and written at onboarding `birth-data` step
- Read back in `soul-report` to feed LLM prompt
- Nullable — users with no astro data gracefully get `[]` / `null`

---

## Section 3: `shadow_engine.py` (Pairwise modifiers)

### 3a. Shadow & Wound — `compute_shadow_and_wound(chart_a, chart_b)`

**Returns:** `{soul_mod, lust_mod, high_voltage: bool, shadow_tags: List[str]}`
Requires `house12_degree` and `asc_degree` (Tier 1 only for 12th house; Chiron aspects use sign-level fallback for Tier 2/3).

| Trigger | soul_mod | lust_mod | high_voltage | Tag |
|---------|----------|----------|--------------|-----|
| chiron_a conjunct moon_b (≤8°) | +25 | 0 | False | `A_Heals_B_Moon` |
| chiron_b conjunct moon_a (≤8°) | +25 | 0 | False | `B_Heals_A_Moon` |
| chiron_a square/opp mars_b | 0 | +15 | True | `B_Triggers_A_Wound` |
| chiron_b square/opp mars_a | 0 | +15 | True | `A_Triggers_B_Wound` |
| sun_a or mars_a in B's 12th house (Tier 1) | +20 | 0 | True | `A_Illuminates_B_Shadow` |
| sun_b or mars_b in A's 12th house (Tier 1) | +20 | 0 | True | `B_Illuminates_A_Shadow` |
| Both in each other's 12th (Tier 1) | +40 additional | 0 | True | `Mutual_Shadow_Integration` |

### 3b. Dynamic Attachment — `compute_dynamic_attachment(base_a, base_b, chart_a, chart_b)`

Modifies baseline attachment type based on synastry before passing to the matrix.

| B's planet → A's Moon | Effect on A |
|------------------------|-------------|
| B's Uranus tension (sq/opp/conj) | A → `anxious` |
| B's Saturn conj/tension | A → `avoidant` |
| B's Jupiter/Venus harmony (conj/trine) | A → `secure` (healing) |

Then compute bidirectionally (A→B), output `(dyn_att_a, dyn_att_b)`.

### 3c. Attachment Dynamics — `compute_attachment_dynamics(att_a, att_b)`

**Returns:** `{soul_mod, partner_mod, lust_mod, high_voltage, trap_tag}`

| Pair | soul_mod | partner_mod | lust_mod | high_voltage | trap_tag |
|------|----------|-------------|----------|--------------|----------|
| secure + secure | +20 | +20 | 0 | False | `Safe_Haven` |
| anxious + avoidant | 0 | -30 | +25 | **True** | `Anxious_Avoidant_Trap` |
| anxious + anxious | +15 | -15 | 0 | False | `Co_Dependency` |
| avoidant + avoidant | 0 | -10 | -20 | False | `Parallel_Lines` |
| secure + (any) | +10 | +10 | 0 | False | `Healing_Anchor` |
| fearful + (any) | 0 | -20 | +15 | **True** | `Chaotic_Oscillation` |

Note: existing `ATTACHMENT_FIT` + `WEIGHTS["soul_attachment"]` in soul_score is NOT replaced — this is an additional post-track modifier.

### 3d. Elemental Fulfillment — `compute_elemental_fulfillment(profile_a, profile_b)`

```python
# A缺Earth，B主導Earth → soul bonus +15
# B缺Water，A主導Water → soul bonus +15
# Capped at +30 total (max 2 fulfilled deficiencies per direction)
```

**Input:** element_profile dicts (from DB). Returns `float` (soul bonus).

---

## Section 4: `compute_match_v2` Modifier Block

Added **after** existing four-track computation, **before** ZWDS result assembly:

```python
soul_adj = partner_adj = lust_adj = 0.0
high_voltage = False
psychological_tags = []

# Shadow & Wound
shadow = compute_shadow_and_wound(user_a, user_b)
soul_adj    += shadow["soul_mod"]
lust_adj    += shadow["lust_mod"]
high_voltage |= shadow["high_voltage"]
psychological_tags.extend(shadow["shadow_tags"])

# Dynamic Attachment + Attachment Dynamics
if user_a.get("attachment_style") and user_b.get("attachment_style"):
    dyn_a, dyn_b = compute_dynamic_attachment(
        user_a["attachment_style"], user_b["attachment_style"], user_a, user_b
    )
    att = compute_attachment_dynamics(dyn_a, dyn_b)
    soul_adj    += att["soul_mod"]
    partner_adj += att["partner_mod"]
    lust_adj    += att["lust_mod"]
    high_voltage |= att["high_voltage"]
    if att["trap_tag"]:
        psychological_tags.append(att["trap_tag"])

# Elemental Fulfillment
ep_a = user_a.get("element_profile")
ep_b = user_b.get("element_profile")
if ep_a and ep_b:
    soul_adj += compute_elemental_fulfillment(ep_a, ep_b)

# Apply modifiers (clamp 0-100)
tracks["soul"]    = _clamp(tracks["soul"]    + soul_adj)
tracks["passion"] = _clamp(tracks["passion"] + lust_adj)
tracks["partner"] = _clamp(tracks["partner"] + partner_adj)

result["high_voltage"]       = high_voltage
result["psychological_tags"] = psychological_tags
```

---

## Section 5: Phase III — Mode Filter (Planning Note Only)

Future roadmap entry in `MVP-PROGRESS.md`:

> **Phase I.5 — Mode Filter (Hunt / Nest / Abyss)**
> User selects current intent in daily feed. System re-weights track output:
> - **Hunt**: emphasize passion + lust, suppress partner track, pass through HIGH_VOLTAGE
> - **Nest**: emphasize partner + soul, suppress high_voltage matches
> - **Abyss**: unlock all extremes, surface highest soul+lust regardless of high_voltage

Implementation: API query param `?mode=hunt|nest|abyss` on `/api/matches/daily`. No DB column needed.

---

## Testing Plan

### `test_psychology.py` (pytest)
- `test_extract_sm_dynamics_natural_dom` — sun conjunct pluto within 8° → `Natural_Dom`
- `test_extract_sm_dynamics_anxious_sub` — moon conjunct pluto → `Anxious_Sub`
- `test_extract_critical_degrees_karmic` — venus at 264.9° → `Karmic_Crisis_VENUS`
- `test_extract_critical_degrees_blind` — sun at 0.5° → `Blind_Impulse_SUN`
- `test_critical_degrees_excludes_moon_tier23` — no exact time → moon excluded
- `test_element_profile_deficiency` — 0 earth planets → deficiency includes Earth
- `test_element_profile_dominant` — 5 fire planets → dominant includes Fire

### `test_shadow_engine.py` (pytest)
- `test_chiron_heals_moon` — chiron_a conjunct moon_b → `A_Heals_B_Moon` + soul_mod=25
- `test_chiron_triggers_wound` — chiron sq mars → high_voltage + lust_mod=15
- `test_12th_house_shadow` — sun_a in B's 12th → high_voltage + soul_mod=20
- `test_attachment_anxious_avoidant` — trap triggers high_voltage + partner_mod=-30
- `test_dynamic_attachment_uranus` — B uranus tension A moon → A becomes anxious
- `test_elemental_fulfillment` — A lacks Earth, B dominant Earth → +15 bonus
- `test_compute_match_v2_includes_psychological_tags` — end-to-end: result has key

---

*Design approved 2026-02-22 | Implementation: Phase I + II*
