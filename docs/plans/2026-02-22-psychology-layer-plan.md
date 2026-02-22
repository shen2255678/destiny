# Psychology Layer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Add a Psychology Layer to the DESTINY algorithm: per-user S/M tags, karmic degree tags, and element profiles computed at chart time and stored in DB; plus pairwise Shadow & Wound and Attachment Trap modifiers applied at the end of `compute_match_v2`.

**Architecture:** Phase I creates `psychology.py` (3 per-user functions called at chart time, results stored in users table via Migration 011). Phase II creates `shadow_engine.py` and modifies `compute_match_v2` to apply additive soul/lust/partner modifiers and `high_voltage` flag after the existing four-track computation. Nothing in the existing `WEIGHTS` dict is changed.

**Tech Stack:** Python 3.11, FastAPI, pytest, TypeScript, Supabase PostgreSQL, Next.js API Routes.

---

## Context

- `astro-service/chart.py` line 323: `calculate_chart()` returns `result` dict; line 324: `return result`
- `astro-service/matching.py` lines 1034-1078: `compute_match_v2` computes lust/soul/tracks, then BaZi branch modifiers, then assembles the return dict
- `destiny-app/src/app/api/onboarding/birth-data/route.ts` lines 280-308: Supabase `.update({})` call that writes chart fields; add new fields here
- `destiny-app/src/lib/supabase/types.ts` lines 23-101: `users.Row` interface; `Insert` starts at line 102
- Latest migration: `010_planet_degrees.sql`. Next migration number: **011**
- All existing tests: `pytest astro-service/ -v` (191 tests must stay green)

---

### Task 1: Create `psychology.py` with 3 per-user functions (TDD)

**Files:**
- Create: `astro-service/test_psychology.py`
- Create: `astro-service/psychology.py`

**Step 1: Write the failing tests**

Create `astro-service/test_psychology.py`:

```python
"""Tests for psychology.py — per-user tag extraction."""
import pytest
from psychology import extract_sm_dynamics, extract_critical_degrees, compute_element_profile


# ── extract_sm_dynamics ───────────────────────────────────────────────────────

def _chart(**kwargs):
    """Helper: build minimal chart dict."""
    return {k: v for k, v in kwargs.items()}


def test_sm_natural_dom_sun_pluto_conjunction():
    chart = _chart(sun_degree=10.0, pluto_degree=14.0)  # diff=4° < 8°
    tags = extract_sm_dynamics(chart)
    assert "Natural_Dom" in tags


def test_sm_natural_dom_mars_pluto_trine():
    chart = _chart(mars_degree=10.0, pluto_degree=130.0)  # diff=120° trine
    tags = extract_sm_dynamics(chart)
    assert "Natural_Dom" in tags


def test_sm_sadist_dom_mars_pluto_square():
    chart = _chart(mars_degree=10.0, pluto_degree=100.0)  # diff=90° square
    tags = extract_sm_dynamics(chart)
    assert "Sadist_Dom" in tags


def test_sm_anxious_sub_moon_pluto_conjunction():
    chart = _chart(moon_degree=200.0, pluto_degree=204.0)
    tags = extract_sm_dynamics(chart)
    assert "Anxious_Sub" in tags


def test_sm_brat_sub_mercury_mars_square():
    chart = _chart(mercury_degree=0.0, mars_degree=90.0)
    tags = extract_sm_dynamics(chart)
    assert "Brat_Sub" in tags


def test_sm_service_sub_venus_in_taurus():
    chart = _chart(venus_sign="taurus")
    tags = extract_sm_dynamics(chart)
    assert "Service_Sub" in tags


def test_sm_masochist_sub_mars_neptune_opposition():
    chart = _chart(mars_degree=0.0, neptune_degree=180.0)
    tags = extract_sm_dynamics(chart)
    assert "Masochist_Sub" in tags


def test_sm_no_tags_empty_chart():
    tags = extract_sm_dynamics({})
    assert tags == []


def test_sm_daddy_dom_saturn_sun_conjunction():
    chart = _chart(saturn_degree=50.0, sun_degree=54.0)
    tags = extract_sm_dynamics(chart)
    assert "Daddy_Dom" in tags


# ── extract_critical_degrees ──────────────────────────────────────────────────

def test_critical_karmic_venus_29_degree():
    # venus at 264.9° → sign degree = 264.9 % 30 = 24.9°... wait, 264/30=8rem24.9 → not 29
    # venus at 269.5° → 269.5 % 30 = 29.5° → Karmic_Crisis
    chart = _chart(venus_degree=269.5)
    tags = extract_critical_degrees(chart, is_exact_time=False)
    assert "Karmic_Crisis_VENUS" in tags


def test_critical_blind_sun_0_degree():
    chart = _chart(sun_degree=0.5)   # 0.5 % 30 = 0.5 < 1.0
    tags = extract_critical_degrees(chart, is_exact_time=False)
    assert "Blind_Impulse_SUN" in tags


def test_critical_moon_excluded_tier23():
    chart = _chart(moon_degree=269.5)   # moon at 29° sign
    tags = extract_critical_degrees(chart, is_exact_time=False)
    assert "Karmic_Crisis_MOON" not in tags


def test_critical_moon_included_tier1():
    chart = _chart(moon_degree=269.5)
    tags = extract_critical_degrees(chart, is_exact_time=True)
    assert "Karmic_Crisis_MOON" in tags


def test_critical_asc_excluded_tier23():
    chart = _chart(asc_degree=0.3)
    tags = extract_critical_degrees(chart, is_exact_time=False)
    assert "Blind_Impulse_ASC" not in tags


def test_critical_asc_included_tier1():
    chart = _chart(asc_degree=0.3)
    tags = extract_critical_degrees(chart, is_exact_time=True)
    assert "Blind_Impulse_ASC" in tags


def test_critical_normal_degree_no_tag():
    chart = _chart(sun_degree=90.0)   # 90 % 30 = 0.0 → Blind_Impulse!
    # Actually 90.0 % 30 = 0.0 → IS Blind_Impulse. Let's use 91.0 % 30 = 1.0
    chart = _chart(sun_degree=91.0)   # 91 % 30 = 1.0, not < 1.0
    tags = extract_critical_degrees(chart, is_exact_time=False)
    assert "Blind_Impulse_SUN" not in tags
    assert "Karmic_Crisis_SUN" not in tags


def test_critical_no_degrees_no_tags():
    tags = extract_critical_degrees({}, is_exact_time=True)
    assert tags == []


# ── compute_element_profile ───────────────────────────────────────────────────

def test_element_profile_counts_10_planets():
    # All fire: aries × 10 is impossible but let's use all fire planets
    chart = {
        "sun_sign": "aries", "moon_sign": "leo", "mercury_sign": "sagittarius",
        "venus_sign": "aries", "mars_sign": "leo",
        "jupiter_sign": "sagittarius", "saturn_sign": "aries",
        "uranus_sign": "leo", "neptune_sign": "sagittarius", "pluto_sign": "aries"
    }
    profile = compute_element_profile(chart)
    assert profile["counts"]["Fire"] == 10
    assert profile["counts"]["Earth"] == 0
    assert "Fire" in profile["dominant"]
    assert "Earth" in profile["deficiency"]


def test_element_profile_mixed():
    chart = {
        "sun_sign": "aries",        # fire
        "moon_sign": "taurus",       # earth
        "mercury_sign": "gemini",    # air
        "venus_sign": "cancer",      # water
        "mars_sign": "leo",          # fire
        "jupiter_sign": "virgo",     # earth
        "saturn_sign": "libra",      # air
        "uranus_sign": "scorpio",    # water
        "neptune_sign": "sagittarius", # fire
        "pluto_sign": "capricorn",   # earth
    }
    profile = compute_element_profile(chart)
    assert profile["counts"] == {"Fire": 3, "Earth": 3, "Air": 2, "Water": 2}
    assert profile["deficiency"] == []   # nothing <= 1
    assert profile["dominant"] == []     # nothing >= 4


def test_element_profile_missing_planets_graceful():
    chart = {"sun_sign": "aries"}  # only sun known
    profile = compute_element_profile(chart)
    assert profile["counts"]["Fire"] == 1
    assert "Earth" in profile["deficiency"]
    assert "Air" in profile["deficiency"]
    assert "Water" in profile["deficiency"]


def test_element_profile_unknown_sign_ignored():
    chart = {"sun_sign": "aries", "moon_sign": None}
    profile = compute_element_profile(chart)
    assert profile["counts"]["Fire"] == 1
```

**Step 2: Run tests to verify they fail**

```bash
cd astro-service
pytest test_psychology.py -v
```

Expected: `ImportError: No module named 'psychology'` or `ModuleNotFoundError`

**Step 3: Implement `astro-service/psychology.py`**

Create `astro-service/psychology.py`:

```python
"""
DESTINY — Psychology Layer
Per-user psychological tag extraction from natal chart data.

Three functions for single-user analysis (called at chart time):
  - extract_sm_dynamics(chart)           → List[str] S/M role tags
  - extract_critical_degrees(chart, exact) → List[str] 0°/29° karmic tags
  - compute_element_profile(chart)       → dict with counts/deficiency/dominant
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


# ── Aspect utilities ──────────────────────────────────────────────────────────

def _dist(deg_a: Optional[float], deg_b: Optional[float]) -> Optional[float]:
    """Shortest arc between two ecliptic longitudes."""
    if deg_a is None or deg_b is None:
        return None
    diff = abs(deg_a - deg_b)
    return min(diff, 360.0 - diff)


def _has_aspect(deg_a: Optional[float], deg_b: Optional[float],
                aspect_type: str, orb: float = 8.0) -> bool:
    """Return True if deg_a and deg_b form the named aspect within orb degrees.

    aspect_type values:
      "conjunction"  → 0°
      "trine"        → 120°
      "square"       → 90°
      "opposition"   → 180°
      "tension"      → conjunction OR square OR opposition
    """
    d = _dist(deg_a, deg_b)
    if d is None:
        return False
    if aspect_type == "conjunction":
        return d <= orb
    if aspect_type == "trine":
        return abs(d - 120.0) <= orb
    if aspect_type == "square":
        return abs(d - 90.0) <= orb
    if aspect_type == "opposition":
        return abs(d - 180.0) <= orb
    if aspect_type == "tension":
        return (d <= orb or
                abs(d - 90.0) <= orb or
                abs(d - 180.0) <= orb)
    return False


# ── S/M Dynamics ─────────────────────────────────────────────────────────────

def extract_sm_dynamics(chart: Dict[str, Any]) -> List[str]:
    """Analyse natal chart and return latent S/M role tags.

    Tags are backend-only variables used for matching modifiers and LLM prompts.
    They are never displayed raw to users.

    Parameters
    ----------
    chart : dict   Natal chart dict with ``*_degree`` and ``*_sign`` keys.

    Returns
    -------
    List[str]   Up to 8 role tags.
    """
    tags: List[str] = []

    sun    = chart.get("sun_degree")
    mars   = chart.get("mars_degree")
    saturn = chart.get("saturn_degree")
    moon   = chart.get("moon_degree")
    mercury = chart.get("mercury_degree")
    venus  = chart.get("venus_degree")
    neptune = chart.get("neptune_degree")
    pluto  = chart.get("pluto_degree")

    # ── Dominant (S) roles ────────────────────────────────────────────────────
    # Natural Dom: sun or mars in harmonic aspect with pluto
    if (_has_aspect(sun, pluto, "conjunction") or _has_aspect(sun, pluto, "trine") or
            _has_aspect(mars, pluto, "conjunction") or _has_aspect(mars, pluto, "trine")):
        tags.append("Natural_Dom")

    # Daddy Dom: saturn in harmonic aspect with sun
    if _has_aspect(saturn, sun, "conjunction") or _has_aspect(saturn, sun, "trine"):
        tags.append("Daddy_Dom")

    # Sadist Dom: mars in hard aspect with pluto
    if _has_aspect(mars, pluto, "square") or _has_aspect(mars, pluto, "opposition"):
        tags.append("Sadist_Dom")

    # ── Submissive (M) roles ──────────────────────────────────────────────────
    # Anxious Sub: moon in tension with pluto or neptune
    if _has_aspect(moon, pluto, "tension") or _has_aspect(moon, neptune, "tension"):
        tags.append("Anxious_Sub")

    # Brat Sub: mercury in tension with mars
    if _has_aspect(mercury, mars, "tension"):
        tags.append("Brat_Sub")

    # Service Sub: venus in an earth sign (sign-level, no degree needed)
    venus_sign = chart.get("venus_sign", "") or ""
    if venus_sign.lower() in {"taurus", "virgo", "capricorn"}:
        tags.append("Service_Sub")

    # Masochist Sub: mars in tension or conjunction with neptune
    if _has_aspect(mars, neptune, "tension") or _has_aspect(mars, neptune, "conjunction"):
        tags.append("Masochist_Sub")

    return tags


# ── Critical Degrees ──────────────────────────────────────────────────────────

# Personal planets reliable at any data tier (move < 1°/day so noon approximation is safe)
_RELIABLE_POINTS = ["sun", "mercury", "venus", "mars"]
# Fast-moving points: only reliable when exact birth time is known (Tier 1)
_TIER1_POINTS = ["moon", "asc"]


def extract_critical_degrees(chart: Dict[str, Any],
                              is_exact_time: bool = False) -> List[str]:
    """Extract 0° (Blind Impulse) and 29° (Karmic Crisis) degree tags.

    Only uses planets reliable for the user's data tier:
    - Always: sun, mercury, venus, mars
    - Tier 1 only: moon, asc  (excluded otherwise to prevent false labels)
    - Outer planets (Jupiter → Pluto) are intentionally excluded; they sit at
      the same degree for months/years and would produce world-generation labels.

    Parameters
    ----------
    chart         : dict   Natal chart dict with ``*_degree`` keys.
    is_exact_time : bool   True when user has precise birth time (Tier 1).

    Returns
    -------
    List[str]   Tags like ``"Karmic_Crisis_VENUS"``, ``"Blind_Impulse_SUN"``.
    """
    tags: List[str] = []
    points = list(_RELIABLE_POINTS)
    if is_exact_time:
        points.extend(_TIER1_POINTS)

    for point in points:
        degree = chart.get(f"{point}_degree")
        if degree is None:
            continue
        sign_deg = degree % 30.0
        if sign_deg >= 29.0:
            tags.append(f"Karmic_Crisis_{point.upper()}")
        elif sign_deg < 1.0:
            tags.append(f"Blind_Impulse_{point.upper()}")

    return tags


# ── Element Profile ───────────────────────────────────────────────────────────

_ELEMENT_MAP: Dict[str, str] = {
    "aries": "Fire", "leo": "Fire", "sagittarius": "Fire",
    "taurus": "Earth", "virgo": "Earth", "capricorn": "Earth",
    "gemini": "Air", "libra": "Air", "aquarius": "Air",
    "cancer": "Water", "scorpio": "Water", "pisces": "Water",
}

_CORE_PLANETS = [
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
]


def compute_element_profile(chart: Dict[str, Any]) -> Dict[str, Any]:
    """Count the four Western elements across the 10 core planets.

    Parameters
    ----------
    chart : dict   Natal chart dict with ``*_sign`` keys.

    Returns
    -------
    dict with keys:
      - ``counts``     : {Fire, Earth, Air, Water} planet counts
      - ``deficiency`` : elements with count <= 1  (soul "black holes")
      - ``dominant``   : elements with count >= 4  (soul "strengths")
    """
    counts: Dict[str, int] = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}

    for planet in _CORE_PLANETS:
        sign = (chart.get(f"{planet}_sign") or "").lower()
        element = _ELEMENT_MAP.get(sign)
        if element:
            counts[element] += 1

    deficiency = [elem for elem, cnt in counts.items() if cnt <= 1]
    dominant   = [elem for elem, cnt in counts.items() if cnt >= 4]

    return {
        "counts":     counts,
        "deficiency": deficiency,
        "dominant":   dominant,
    }
```

**Step 4: Run tests and verify they pass**

```bash
cd astro-service
pytest test_psychology.py -v
```

Expected: all tests PASS.

**Step 5: Confirm existing tests still pass**

```bash
cd astro-service
pytest test_chart.py test_matching.py -v
```

Expected: 191 tests PASS (psychology.py is not yet imported by anything — no side effects).

**Step 6: Commit**

```bash
git add astro-service/psychology.py astro-service/test_psychology.py
git commit -m "feat(astro): add psychology.py — SM tags, critical degrees, element profile"
```

---

### Task 2: Migration 011 + types.ts update

**Files:**
- Create: `destiny-app/supabase/migrations/011_psychology_tags.sql`
- Modify: `destiny-app/src/lib/supabase/types.ts` (lines 100-101, 160-165 area — Insert/Update sections)

**Step 1: Create `011_psychology_tags.sql`**

```sql
-- Migration 011: Psychology Layer tags
-- Phase I: per-user SM dynamics, karmic degree flags, and elemental profile
-- Populated by astro-service /calculate-chart via the birth-data onboarding API.

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS sm_tags         JSONB DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS karmic_tags     JSONB DEFAULT '[]',
  ADD COLUMN IF NOT EXISTS element_profile JSONB DEFAULT NULL;

COMMENT ON COLUMN public.users.sm_tags         IS 'S/M role tags from natal chart aspects (backend-only). e.g. ["Natural_Dom","Anxious_Sub"]';
COMMENT ON COLUMN public.users.karmic_tags      IS '0°/29° karmic degree tags (backend-only). e.g. ["Karmic_Crisis_VENUS"]';
COMMENT ON COLUMN public.users.element_profile  IS 'Western element counts + deficiency/dominant. {counts:{Fire,Earth,Air,Water}, deficiency:[], dominant:[]}';
```

**Step 2: Apply migration to Supabase (remote)**

```bash
cd destiny-app
npx supabase db push
```

Expected: migration 011 applied successfully. If local dev, run:

```bash
npx supabase migration up
```

**Step 3: Update `types.ts` — add to `Row` interface**

In `destiny-app/src/lib/supabase/types.ts`, after line 100 (`planet_degrees: Json | null`), add:

```typescript
          sm_tags: Json
          karmic_tags: Json
          element_profile: Json | null
```

**Step 4: Update `types.ts` — add to `Insert` interface**

In the `Insert` section (after the `planet_degrees` optional field in Insert), add:

```typescript
          sm_tags?: Json
          karmic_tags?: Json
          element_profile?: Json | null
```

**Step 5: Update `types.ts` — add to `Update` interface**

Same pattern in the `Update` section:

```typescript
          sm_tags?: Json
          karmic_tags?: Json
          element_profile?: Json | null
```

**Step 6: Verify TypeScript compiles**

```bash
cd destiny-app
npx tsc --noEmit
```

Expected: no type errors.

**Step 7: Commit**

```bash
git add destiny-app/supabase/migrations/011_psychology_tags.sql destiny-app/src/lib/supabase/types.ts
git commit -m "feat(db): migration 011 — sm_tags, karmic_tags, element_profile columns"
```

---

### Task 3: Wire `psychology.py` into `chart.py` and `birth-data` API

**Files:**
- Modify: `astro-service/chart.py` (line 322, before `return result`)
- Modify: `destiny-app/src/app/api/onboarding/birth-data/route.ts` (line 307, inside the `.update({})` call)

**Step 1: Modify `chart.py` — import and call psychology functions**

In `astro-service/chart.py`, at the very end of `calculate_chart()`, before `return result` (line 323):

Find this block (lines 317-324):
```python
    # ── Emotional Capacity (心理情緒容量) ───────────────────────
    # ...
    result["emotional_capacity"] = compute_emotional_capacity(result)

    return result
```

Replace with:
```python
    # ── Emotional Capacity (心理情緒容量) ───────────────────────
    # Computed from Western chart aspects only (ZWDS rules require zwds_data,
    # which is computed separately by compute_zwds_chart in main.py).
    # Callers with ZWDS data should call compute_emotional_capacity(chart_data, zwds_data)
    # separately and update this field after computing the ZWDS chart.
    result["emotional_capacity"] = compute_emotional_capacity(result)

    # ── Psychology Layer (Phase I) ───────────────────────────────
    from psychology import extract_sm_dynamics, extract_critical_degrees, compute_element_profile
    is_exact = (data_tier == 1)
    result["sm_tags"]        = extract_sm_dynamics(result)
    result["karmic_tags"]    = extract_critical_degrees(result, is_exact_time=is_exact)
    result["element_profile"] = compute_element_profile(result)

    return result
```

**Step 2: Verify chart tests still pass**

```bash
cd astro-service
pytest test_chart.py -v
```

Expected: all 30 tests PASS.

**Step 3: Modify `birth-data/route.ts` — store new fields**

In `destiny-app/src/app/api/onboarding/birth-data/route.ts`, find the `.update({})` call at line 280. Inside that update object, after line 307 (`planet_degrees: ...`), add:

```typescript
          // Phase I: Psychology Layer tags
          sm_tags:         chart.sm_tags         ?? [],
          karmic_tags:     chart.karmic_tags      ?? [],
          element_profile: chart.element_profile  ?? null,
```

The surrounding context (for exact edit):
```typescript
          // Phase H v1.4/v1.5 fields
          bazi_month_branch:  chart.bazi?.bazi_month_branch ?? null,
          bazi_day_branch:    chart.bazi?.bazi_day_branch ?? null,
          emotional_capacity: chart.emotional_capacity ?? 50,
          // Phase I: exact planet degrees for orb-based aspect matching
          planet_degrees: Object.keys(planetDegrees).length > 0 ? planetDegrees : null,
          // Phase I: Psychology Layer tags
          sm_tags:         chart.sm_tags         ?? [],
          karmic_tags:     chart.karmic_tags      ?? [],
          element_profile: chart.element_profile  ?? null,
        })
```

**Step 4: Verify TypeScript compiles**

```bash
cd destiny-app
npx tsc --noEmit
```

Expected: no type errors.

**Step 5: Run all existing Next.js tests**

```bash
cd destiny-app
npx vitest run
```

Expected: 82 tests pass (birth-data unit tests may or may not cover the new fields — that is OK).

**Step 6: Smoke test the astro endpoint returns new fields**

Start astro service, then:

```bash
cd astro-service
uvicorn main:app --port 8001 &
curl -s -X POST http://localhost:8001/calculate-chart \
  -H "Content-Type: application/json" \
  -d '{"birth_date":"1997-01-05","birth_time":"precise","birth_time_exact":"23:30","lat":25.033,"lng":121.565,"data_tier":1}' \
  | python -m json.tool | grep -E "sm_tags|karmic_tags|element_profile"
```

Expected: three keys present in the response.

**Step 7: Commit**

```bash
git add astro-service/chart.py destiny-app/src/app/api/onboarding/birth-data/route.ts
git commit -m "feat: wire psychology.py into chart.py and birth-data API — Phase I complete"
```

---

### Task 4: Create `shadow_engine.py` (Phase II pairwise modifiers, TDD)

**Files:**
- Create: `astro-service/test_shadow_engine.py`
- Create: `astro-service/shadow_engine.py`

**Step 1: Write the failing tests**

Create `astro-service/test_shadow_engine.py`:

```python
"""Tests for shadow_engine.py — pairwise match-time modifiers."""
import pytest
from shadow_engine import (
    compute_shadow_and_wound,
    compute_dynamic_attachment,
    compute_attachment_dynamics,
    compute_elemental_fulfillment,
)


# ── compute_shadow_and_wound ──────────────────────────────────────────────────

def test_chiron_heals_moon_soul_bonus():
    a = {"chiron_degree": 100.0}
    b = {"moon_degree": 104.0}   # diff=4° < 8° → conjunction
    result = compute_shadow_and_wound(a, b)
    assert result["soul_mod"] >= 25.0
    assert "A_Heals_B_Moon" in result["shadow_tags"]
    assert result["high_voltage"] is False


def test_chiron_heals_moon_bidirectional():
    a = {"chiron_degree": 100.0, "moon_degree": 200.0}
    b = {"chiron_degree": 195.0, "moon_degree": 104.0}
    result = compute_shadow_and_wound(a, b)
    assert "A_Heals_B_Moon" in result["shadow_tags"]
    assert "B_Heals_A_Moon" in result["shadow_tags"]
    assert result["soul_mod"] >= 50.0


def test_chiron_triggers_wound_lust_bonus_and_high_voltage():
    a = {"chiron_degree": 10.0}
    b = {"mars_degree": 100.0}   # diff=90° square → tension
    result = compute_shadow_and_wound(a, b)
    assert result["lust_mod"] >= 15.0
    assert result["high_voltage"] is True
    assert "B_Triggers_A_Wound" in result["shadow_tags"]


def test_12th_house_shadow_a_in_b_12th_requires_tier1():
    # sun_a falls into b's 12th house
    a = {"sun_degree": 200.0}
    b = {"house12_degree": 195.0, "ascendant_degree": 225.0}  # 12th house 195→225
    result = compute_shadow_and_wound(a, b)
    assert "A_Illuminates_B_Shadow" in result["shadow_tags"]
    assert result["high_voltage"] is True
    assert result["soul_mod"] >= 20.0


def test_no_trigger_far_degrees():
    a = {"chiron_degree": 0.0}
    b = {"moon_degree": 90.0}   # 90° apart — not a conjunction (orb=8°)
    result = compute_shadow_and_wound(a, b)
    assert result["soul_mod"] == 0.0
    assert result["lust_mod"] == 0.0
    assert result["high_voltage"] is False
    assert result["shadow_tags"] == []


def test_empty_charts_no_error():
    result = compute_shadow_and_wound({}, {})
    assert result["soul_mod"] == 0.0
    assert result["high_voltage"] is False


def test_mutual_shadow_double_bonus():
    a = {"sun_degree": 200.0, "house12_degree": 188.0, "ascendant_degree": 218.0}
    b = {"sun_degree": 195.0, "house12_degree": 193.0, "ascendant_degree": 223.0}
    result = compute_shadow_and_wound(a, b)
    assert "Mutual_Shadow_Integration" in result["shadow_tags"]
    assert result["soul_mod"] >= 80.0   # 20 + 20 + 40


# ── compute_dynamic_attachment ────────────────────────────────────────────────

def test_dynamic_attachment_uranus_makes_anxious():
    chart_a = {"moon_degree": 50.0}
    chart_b = {"uranus_degree": 140.0}   # diff=90° tension → A becomes anxious
    dyn_a, dyn_b = compute_dynamic_attachment("secure", "secure", chart_a, chart_b)
    assert dyn_a == "anxious"
    assert dyn_b == "secure"   # B not changed by A in this test


def test_dynamic_attachment_saturn_makes_avoidant():
    chart_a = {"moon_degree": 50.0}
    chart_b = {"saturn_degree": 55.0}    # diff=5° conjunction → A avoidant
    dyn_a, dyn_b = compute_dynamic_attachment("secure", "secure", chart_a, chart_b)
    assert dyn_a == "avoidant"


def test_dynamic_attachment_jupiter_heals_to_secure():
    chart_a = {"moon_degree": 50.0}
    chart_b = {"jupiter_degree": 170.0}  # 120° trine → secure
    dyn_a, dyn_b = compute_dynamic_attachment("anxious", "secure", chart_a, chart_b)
    assert dyn_a == "secure"


def test_dynamic_attachment_no_aspect_unchanged():
    chart_a = {"moon_degree": 50.0}
    chart_b = {"uranus_degree": 10.0}    # diff=40° — no aspect (orb 8°)
    dyn_a, dyn_b = compute_dynamic_attachment("secure", "avoidant", chart_a, chart_b)
    assert dyn_a == "secure"
    assert dyn_b == "avoidant"


def test_dynamic_attachment_empty_charts():
    dyn_a, dyn_b = compute_dynamic_attachment("anxious", "avoidant", {}, {})
    assert dyn_a == "anxious"
    assert dyn_b == "avoidant"


# ── compute_attachment_dynamics ───────────────────────────────────────────────

def test_attachment_secure_secure():
    result = compute_attachment_dynamics("secure", "secure")
    assert result["soul_mod"] == 20.0
    assert result["partner_mod"] == 20.0
    assert result["lust_mod"] == 0.0
    assert result["high_voltage"] is False
    assert result["trap_tag"] == "Safe_Haven"


def test_attachment_anxious_avoidant_high_voltage():
    result = compute_attachment_dynamics("anxious", "avoidant")
    assert result["lust_mod"] == 25.0
    assert result["partner_mod"] == -30.0
    assert result["high_voltage"] is True
    assert result["trap_tag"] == "Anxious_Avoidant_Trap"


def test_attachment_order_independent():
    r1 = compute_attachment_dynamics("anxious", "avoidant")
    r2 = compute_attachment_dynamics("avoidant", "anxious")
    assert r1 == r2


def test_attachment_anxious_anxious():
    result = compute_attachment_dynamics("anxious", "anxious")
    assert result["soul_mod"] == 15.0
    assert result["partner_mod"] == -15.0
    assert result["trap_tag"] == "Co_Dependency"


def test_attachment_avoidant_avoidant():
    result = compute_attachment_dynamics("avoidant", "avoidant")
    assert result["lust_mod"] == -20.0
    assert result["high_voltage"] is False
    assert result["trap_tag"] == "Parallel_Lines"


def test_attachment_secure_anxious_healing():
    result = compute_attachment_dynamics("secure", "anxious")
    assert result["soul_mod"] == 10.0
    assert result["trap_tag"] == "Healing_Anchor"


def test_attachment_fearful_high_voltage():
    result = compute_attachment_dynamics("fearful", "secure")
    assert result["high_voltage"] is True
    assert result["trap_tag"] == "Chaotic_Oscillation"


def test_attachment_unknown_style_defaults_no_error():
    result = compute_attachment_dynamics("secure", "disorganized")
    # disorganized treated as fearful-avoidant or defaults gracefully
    assert isinstance(result["soul_mod"], float)
    assert "trap_tag" in result


# ── compute_elemental_fulfillment ─────────────────────────────────────────────

def test_elemental_fulfillment_a_lacks_earth_b_dominant_earth():
    profile_a = {"deficiency": ["Earth"], "dominant": ["Fire"]}
    profile_b = {"deficiency": [],        "dominant": ["Earth"]}
    bonus = compute_elemental_fulfillment(profile_a, profile_b)
    assert bonus == 15.0


def test_elemental_fulfillment_bidirectional():
    profile_a = {"deficiency": ["Water"], "dominant": ["Fire"]}
    profile_b = {"deficiency": ["Fire"],  "dominant": ["Water"]}
    bonus = compute_elemental_fulfillment(profile_a, profile_b)
    assert bonus == 30.0   # 15 (B fills A) + 15 (A fills B)


def test_elemental_fulfillment_no_match():
    profile_a = {"deficiency": ["Earth"], "dominant": ["Fire"]}
    profile_b = {"deficiency": [],        "dominant": ["Air"]}
    bonus = compute_elemental_fulfillment(profile_a, profile_b)
    assert bonus == 0.0


def test_elemental_fulfillment_empty_profiles():
    bonus = compute_elemental_fulfillment({}, {})
    assert bonus == 0.0


def test_elemental_fulfillment_capped_at_30():
    # Even if 4 deficiencies are filled, cap applies
    profile_a = {"deficiency": ["Earth", "Water", "Air"], "dominant": ["Fire"]}
    profile_b = {"deficiency": [], "dominant": ["Earth", "Water", "Air"]}
    bonus = compute_elemental_fulfillment(profile_a, profile_b)
    assert bonus <= 30.0
```

**Step 2: Run tests to verify they fail**

```bash
cd astro-service
pytest test_shadow_engine.py -v
```

Expected: `ImportError: No module named 'shadow_engine'`

**Step 3: Implement `astro-service/shadow_engine.py`**

Create `astro-service/shadow_engine.py`:

```python
"""
DESTINY — Shadow & Wound Engine + Attachment Dynamics
Pairwise match-time modifier functions for compute_match_v2().

Four functions:
  - compute_shadow_and_wound(chart_a, chart_b)               → soul/lust mods + high_voltage
  - compute_dynamic_attachment(base_a, base_b, ca, cb)       → adjusted attachment types
  - compute_attachment_dynamics(att_a, att_b)                → soul/lust/partner mods + high_voltage
  - compute_elemental_fulfillment(element_profile_a, profile_b) → soul bonus float
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple


# ── Aspect utilities (local copy — shadow_engine has no dependency on psychology.py) ──

def _dist(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None:
        return None
    d = abs(a - b)
    return min(d, 360.0 - d)


def _conj(a: Optional[float], b: Optional[float], orb: float = 8.0) -> bool:
    d = _dist(a, b)
    return d is not None and d <= orb


def _tension(a: Optional[float], b: Optional[float], orb: float = 8.0) -> bool:
    """Conjunction, square, or opposition."""
    d = _dist(a, b)
    if d is None:
        return False
    return d <= orb or abs(d - 90.0) <= orb or abs(d - 180.0) <= orb


def _harmony(a: Optional[float], b: Optional[float], orb: float = 8.0) -> bool:
    """Conjunction or trine."""
    d = _dist(a, b)
    if d is None:
        return False
    return d <= orb or abs(d - 120.0) <= orb


def _in_house(planet_deg: Optional[float],
              cusp_deg: Optional[float],
              next_cusp_deg: Optional[float]) -> bool:
    """Return True if planet falls between cusp_deg and next_cusp_deg (arc-based)."""
    if planet_deg is None or cusp_deg is None or next_cusp_deg is None:
        return False
    house_size = (next_cusp_deg - cusp_deg) % 360.0
    planet_rel = (planet_deg - cusp_deg) % 360.0
    return planet_rel < house_size


# ── compute_shadow_and_wound ──────────────────────────────────────────────────

def compute_shadow_and_wound(chart_a: Dict[str, Any],
                              chart_b: Dict[str, Any]) -> Dict[str, Any]:
    """Compute 12th-house shadow and Chiron wound triggers across two charts.

    Requires Tier 1 data for 12th-house checks (house12_degree + ascendant_degree).
    Falls back silently if degrees are absent.

    Returns
    -------
    dict with keys:
      soul_mod    : float  (additive, apply to soul track)
      lust_mod    : float  (additive, apply to passion track)
      high_voltage: bool   (one-veto — any trigger sets this True)
      shadow_tags : List[str]
    """
    result: Dict[str, Any] = {
        "soul_mod": 0.0,
        "lust_mod": 0.0,
        "high_voltage": False,
        "shadow_tags": [],
    }

    chiron_a = chart_a.get("chiron_degree")
    chiron_b = chart_b.get("chiron_degree")
    moon_a   = chart_a.get("moon_degree")
    moon_b   = chart_b.get("moon_degree")
    mars_a   = chart_a.get("mars_degree")
    mars_b   = chart_b.get("mars_degree")
    sun_a    = chart_a.get("sun_degree")
    sun_b    = chart_b.get("sun_degree")
    h12_a    = chart_a.get("house12_degree")
    asc_a    = chart_a.get("ascendant_degree")
    h12_b    = chart_b.get("house12_degree")
    asc_b    = chart_b.get("ascendant_degree")

    # 1. Chiron (A) conjunct Moon (B) → A heals B's emotional wounds
    if _conj(chiron_a, moon_b):
        result["soul_mod"] += 25.0
        result["shadow_tags"].append("A_Heals_B_Moon")

    # 2. Chiron (B) conjunct Moon (A) → B heals A
    if _conj(chiron_b, moon_a):
        result["soul_mod"] += 25.0
        result["shadow_tags"].append("B_Heals_A_Moon")

    # 3. Chiron (A) in tension with Mars (B) → B triggers A's wound
    if chiron_a and mars_b:
        d = _dist(chiron_a, mars_b)
        if d is not None and (abs(d - 90.0) <= 8.0 or abs(d - 180.0) <= 8.0):
            result["lust_mod"] += 15.0
            result["high_voltage"] = True
            result["shadow_tags"].append("B_Triggers_A_Wound")

    # 4. Chiron (B) in tension with Mars (A) → A triggers B's wound
    if chiron_b and mars_a:
        d = _dist(chiron_b, mars_a)
        if d is not None and (abs(d - 90.0) <= 8.0 or abs(d - 180.0) <= 8.0):
            result["lust_mod"] += 15.0
            result["high_voltage"] = True
            result["shadow_tags"].append("A_Triggers_B_Wound")

    # 5. Sun/Mars (A) falls in B's 12th house (Tier 1 only)
    a_in_b12 = _in_house(sun_a, h12_b, asc_b) or _in_house(mars_a, h12_b, asc_b)
    if a_in_b12:
        result["soul_mod"] += 20.0
        result["high_voltage"] = True
        result["shadow_tags"].append("A_Illuminates_B_Shadow")

    # 6. Sun/Mars (B) falls in A's 12th house (Tier 1 only)
    b_in_a12 = _in_house(sun_b, h12_a, asc_a) or _in_house(mars_b, h12_a, asc_a)
    if b_in_a12:
        result["soul_mod"] += 20.0
        result["high_voltage"] = True
        result["shadow_tags"].append("B_Illuminates_A_Shadow")

    # 7. Mutual shadow integration (both in each other's 12th)
    if a_in_b12 and b_in_a12:
        result["soul_mod"] += 40.0   # additional bonus on top of the two +20s
        result["shadow_tags"].append("Mutual_Shadow_Integration")

    return result


# ── compute_dynamic_attachment ────────────────────────────────────────────────

def compute_dynamic_attachment(
    base_att_a: str,
    base_att_b: str,
    chart_a: Dict[str, Any],
    chart_b: Dict[str, Any],
) -> Tuple[str, str]:
    """Adjust baseline attachment types based on synastry planetary triggers.

    Checks how B's outer planets (Uranus, Saturn, Jupiter) aspect A's Moon,
    and vice versa, to derive the *dynamic* attachment each person will exhibit
    with this specific partner.

    Parameters
    ----------
    base_att_a / base_att_b : str   Baseline attachment from questionnaire
                                    ('secure' | 'anxious' | 'avoidant' | 'fearful')
    chart_a / chart_b       : dict  Natal chart dicts with ``*_degree`` keys.

    Returns
    -------
    Tuple[str, str]   (dynamic_att_a, dynamic_att_b)
    """
    moon_a    = chart_a.get("moon_degree")
    moon_b    = chart_b.get("moon_degree")
    uranus_b  = chart_b.get("uranus_degree")
    saturn_b  = chart_b.get("saturn_degree")
    jupiter_b = chart_b.get("jupiter_degree")
    venus_b   = chart_b.get("venus_degree")
    uranus_a  = chart_a.get("uranus_degree")
    saturn_a  = chart_a.get("saturn_degree")
    jupiter_a = chart_a.get("jupiter_degree")
    venus_a   = chart_a.get("venus_degree")

    dyn_a = base_att_a
    dyn_b = base_att_b

    # B affects A's attachment (via A's Moon)
    if _tension(moon_a, uranus_b):    # instability → anxious
        dyn_a = "anxious"
    elif _tension(moon_a, saturn_b) or _conj(moon_a, saturn_b):  # cold wall → avoidant
        dyn_a = "avoidant"
    elif _harmony(moon_a, jupiter_b) or _harmony(moon_a, venus_b):  # warmth → healed
        dyn_a = "secure"

    # A affects B's attachment (via B's Moon)
    if _tension(moon_b, uranus_a):
        dyn_b = "anxious"
    elif _tension(moon_b, saturn_a) or _conj(moon_b, saturn_a):
        dyn_b = "avoidant"
    elif _harmony(moon_b, jupiter_a) or _harmony(moon_b, venus_a):
        dyn_b = "secure"

    return dyn_a, dyn_b


# ── compute_attachment_dynamics ───────────────────────────────────────────────

def compute_attachment_dynamics(att_a: str, att_b: str) -> Dict[str, Any]:
    """Score the chemical reaction between two attachment types.

    Parameters
    ----------
    att_a / att_b : str   Attachment style: 'secure' | 'anxious' | 'avoidant' | 'fearful'
                          (or 'disorganized' — mapped to 'fearful' internally)

    Returns
    -------
    dict with keys: soul_mod, partner_mod, lust_mod, high_voltage, trap_tag
    """
    # Normalise & alias
    _alias = {"disorganized": "fearful"}
    a = _alias.get((att_a or "secure").lower(), (att_a or "secure").lower())
    b = _alias.get((att_b or "secure").lower(), (att_b or "secure").lower())

    pair = tuple(sorted([a, b]))

    result: Dict[str, Any] = {
        "soul_mod":    0.0,
        "partner_mod": 0.0,
        "lust_mod":    0.0,
        "high_voltage": False,
        "trap_tag":    None,
    }

    if pair == ("secure", "secure"):
        result.update(soul_mod=20.0, partner_mod=20.0, trap_tag="Safe_Haven")

    elif pair == ("anxious", "avoidant"):
        result.update(lust_mod=25.0, partner_mod=-30.0,
                      high_voltage=True, trap_tag="Anxious_Avoidant_Trap")

    elif pair == ("anxious", "anxious"):
        result.update(soul_mod=15.0, partner_mod=-15.0, trap_tag="Co_Dependency")

    elif pair == ("avoidant", "avoidant"):
        result.update(lust_mod=-20.0, partner_mod=-10.0, trap_tag="Parallel_Lines")

    elif "fearful" in pair:
        result.update(lust_mod=15.0, partner_mod=-20.0,
                      high_voltage=True, trap_tag="Chaotic_Oscillation")

    elif "secure" in pair:   # secure + (anxious|avoidant)
        result.update(soul_mod=10.0, partner_mod=10.0, trap_tag="Healing_Anchor")

    return result


# ── compute_elemental_fulfillment ─────────────────────────────────────────────

_FULFILLMENT_PER_MATCH = 15.0
_FULFILLMENT_CAP       = 30.0   # maximum total bonus regardless of matches


def compute_elemental_fulfillment(
    profile_a: Dict[str, Any],
    profile_b: Dict[str, Any],
) -> float:
    """Score how well A's elemental deficiencies are filled by B's dominant elements,
    and vice versa.

    Parameters
    ----------
    profile_a / profile_b : dict   Output of ``psychology.compute_element_profile``.
                                   Expected keys: ``deficiency`` (list), ``dominant`` (list).

    Returns
    -------
    float   Soul bonus to add to soul track score. Capped at 30.0.
    """
    def_a = set(profile_a.get("deficiency") or [])
    dom_b = set(profile_b.get("dominant")   or [])
    def_b = set(profile_b.get("deficiency") or [])
    dom_a = set(profile_a.get("dominant")   or [])

    matches = len(def_a & dom_b) + len(def_b & dom_a)
    bonus = matches * _FULFILLMENT_PER_MATCH
    return min(bonus, _FULFILLMENT_CAP)
```

**Step 4: Run tests and verify they pass**

```bash
cd astro-service
pytest test_shadow_engine.py -v
```

Expected: all tests PASS.

**Step 5: Run full suite**

```bash
cd astro-service
pytest -v
```

Expected: 191 + new shadow_engine tests all PASS.

**Step 6: Commit**

```bash
git add astro-service/shadow_engine.py astro-service/test_shadow_engine.py
git commit -m "feat(astro): add shadow_engine.py — shadow/wound, attachment dynamics, elemental fulfillment"
```

---

### Task 5: Wire Phase II modifiers into `compute_match_v2`

**Files:**
- Modify: `astro-service/matching.py` (lines 1039-1078, after BaZi branch modifier block)

**Step 1: Add import at top of `matching.py`**

In `astro-service/matching.py`, after line 18 (`from zwds_synastry import compute_zwds_synastry`), add:

```python
from shadow_engine import (
    compute_shadow_and_wound,
    compute_dynamic_attachment,
    compute_attachment_dynamics,
    compute_elemental_fulfillment,
)
```

**Step 2: Add modifier block before the `primary_track` line**

In `astro-service/matching.py`, find this block (lines 1045-1047):

```python
    primary_track = max(tracks, key=lambda k: tracks[k])
    quadrant      = classify_quadrant(lust, soul)
    label         = TRACK_LABELS.get(primary_track, primary_track)
```

Insert the following **immediately before** `primary_track = ...`:

```python
    # ── Phase II: Psychology Modifiers ────────────────────────────────────────
    # Applied after all four-track computation. Uses additive modifiers (not
    # WEIGHTS redistribution) so they only influence scores when conditions are met.

    soul_adj    = 0.0
    lust_adj    = 0.0
    partner_adj = 0.0
    high_voltage = False
    psychological_tags: List[str] = []

    # 1. Shadow & Wound Engine (Chiron + 12th house cross-chart triggers)
    try:
        _shadow = compute_shadow_and_wound(user_a, user_b)
        soul_adj    += _shadow["soul_mod"]
        lust_adj    += _shadow["lust_mod"]
        high_voltage = high_voltage or _shadow["high_voltage"]
        psychological_tags.extend(_shadow["shadow_tags"])
    except Exception:
        pass   # never block matching for shadow engine errors

    # 2. Dynamic Attachment + Attachment Dynamics
    _att_a = user_a.get("attachment_style")
    _att_b = user_b.get("attachment_style")
    if _att_a and _att_b:
        try:
            _dyn_a, _dyn_b = compute_dynamic_attachment(
                _att_a, _att_b, user_a, user_b
            )
            _att = compute_attachment_dynamics(_dyn_a, _dyn_b)
            soul_adj    += _att["soul_mod"]
            lust_adj    += _att["lust_mod"]
            partner_adj += _att["partner_mod"]
            high_voltage = high_voltage or _att["high_voltage"]
            if _att["trap_tag"]:
                psychological_tags.append(_att["trap_tag"])
        except Exception:
            pass

    # 3. Elemental Fulfillment (from pre-computed element_profile stored in DB)
    _ep_a = user_a.get("element_profile")
    _ep_b = user_b.get("element_profile")
    if _ep_a and _ep_b:
        try:
            soul_adj += compute_elemental_fulfillment(_ep_a, _ep_b)
        except Exception:
            pass

    # Apply modifiers — clamp each track to [0, 100]
    if soul_adj != 0.0:
        tracks["soul"]    = _clamp(tracks["soul"]    + soul_adj)
    if lust_adj != 0.0:
        tracks["passion"] = _clamp(tracks["passion"] + lust_adj)
    if partner_adj != 0.0:
        tracks["partner"] = _clamp(tracks["partner"] + partner_adj)
```

**Step 3: Add `psychological_tags` and `high_voltage` to the return dict**

In `astro-service/matching.py`, find the `return {` statement at line 1060.

After `"spiciness_level": spiciness,` (line ~1072), add:

```python
        "psychological_tags":  psychological_tags,
        "high_voltage":        high_voltage,
```

Also update the spiciness upgrade logic. After the existing punishment check (line 1058), add:

```python
    # high_voltage from psychology modifiers also upgrades spiciness
    if high_voltage:
        cur_idx    = _SPICINESS_ORDER.index(spiciness) if spiciness in _SPICINESS_ORDER else 0
        target_idx = _SPICINESS_ORDER.index("HIGH_VOLTAGE")
        if cur_idx < target_idx:
            spiciness = "HIGH_VOLTAGE"
```

**Step 4: Run the existing matching tests**

```bash
cd astro-service
pytest test_matching.py -v
```

Expected: all 161 tests PASS. (The modifier block is wrapped in try/except and user dicts in tests may not have `element_profile` / `attachment_style` — that is fine, the block degrades gracefully.)

**Step 5: Run the full test suite**

```bash
cd astro-service
pytest -v
```

Expected: all tests PASS.

**Step 6: Add one integration test to `test_matching.py`**

Open `astro-service/test_matching.py` and append:

```python
# ── Phase II: psychology modifier integration ─────────────────────────────────

def test_compute_match_v2_psychological_tags_key_present():
    """Result dict must always contain psychological_tags and high_voltage keys."""
    ua = {
        "birth_year": 1995, "birth_date": "1995-06-15",
        "sun_sign": "gemini", "moon_sign": "aries", "venus_sign": "taurus",
        "mars_sign": "cancer", "mercury_sign": "gemini", "jupiter_sign": "sagittarius",
        "saturn_sign": "pisces", "uranus_sign": "capricorn", "neptune_sign": "capricorn",
        "pluto_sign": "scorpio", "chiron_sign": "virgo", "juno_sign": "leo",
        "bazi_element": "wood",
    }
    ub = {
        "birth_year": 1993, "birth_date": "1993-09-01",
        "sun_sign": "virgo", "moon_sign": "capricorn", "venus_sign": "leo",
        "mars_sign": "cancer", "mercury_sign": "virgo", "jupiter_sign": "libra",
        "saturn_sign": "aquarius", "uranus_sign": "capricorn", "neptune_sign": "capricorn",
        "pluto_sign": "scorpio", "chiron_sign": "virgo", "juno_sign": "aries",
        "bazi_element": "fire",
    }
    result = compute_match_v2(ua, ub)
    assert "psychological_tags" in result
    assert "high_voltage" in result
    assert isinstance(result["psychological_tags"], list)
    assert isinstance(result["high_voltage"], bool)


def test_compute_match_v2_attachment_dynamics_applied():
    """Anxious + Avoidant pair should trigger high_voltage in v2 result."""
    ua = {
        "birth_year": 1995, "birth_date": "1995-06-15",
        "sun_sign": "gemini", "moon_sign": "aries", "venus_sign": "taurus",
        "mars_sign": "cancer", "mercury_sign": "gemini", "jupiter_sign": "sagittarius",
        "saturn_sign": "pisces", "uranus_sign": "capricorn", "neptune_sign": "capricorn",
        "pluto_sign": "scorpio", "chiron_sign": "virgo", "juno_sign": "leo",
        "bazi_element": "wood",
        "attachment_style": "anxious",
    }
    ub = {
        "birth_year": 1993, "birth_date": "1993-09-01",
        "sun_sign": "virgo", "moon_sign": "capricorn", "venus_sign": "leo",
        "mars_sign": "cancer", "mercury_sign": "virgo", "jupiter_sign": "libra",
        "saturn_sign": "aquarius", "uranus_sign": "capricorn", "neptune_sign": "capricorn",
        "pluto_sign": "scorpio", "chiron_sign": "virgo", "juno_sign": "aries",
        "bazi_element": "fire",
        "attachment_style": "avoidant",
    }
    result = compute_match_v2(ua, ub)
    assert result["high_voltage"] is True
    assert "Anxious_Avoidant_Trap" in result["psychological_tags"]
```

Run:

```bash
cd astro-service
pytest test_matching.py -v -k "psychological"
```

Expected: 2 new tests PASS.

**Step 7: Commit**

```bash
git add astro-service/matching.py astro-service/test_matching.py
git commit -m "feat(matching): wire Phase II psychology modifiers into compute_match_v2"
```

---

### Task 6: Update `docs/MVP-PROGRESS.md`

**Files:**
- Modify: `docs/MVP-PROGRESS.md`

**Step 1: Find the Phase G entry and add Phase I below it**

In `docs/MVP-PROGRESS.md`, find the line:

```
| **Matching Algorithm v2 (Phase G)** | **Done ✅** | ...
```

Add a new row immediately after it:

```markdown
| **Psychology Layer (Phase I)** | **Done ✅** | psychology.py (SM tags, critical degrees, element profile) + shadow_engine.py (Chiron, 12th house, attachment dynamics, elemental fulfillment) + modifier block in compute_match_v2. Migration 011. Design doc: `docs/plans/2026-02-22-psychology-layer-design.md`. |
| **Mode Filter Phase I.5 (Future)** | **Planned** | Hunt / Nest / Abyss mode via `?mode=` query param on `/api/matches/daily`. Re-weights four-track output. No DB column needed. |
```

**Step 2: Commit**

```bash
git add docs/MVP-PROGRESS.md
git commit -m "docs: update MVP-PROGRESS.md — Phase I psychology layer done, Phase I.5 planned"
```

---

## Final Verification

After all tasks complete, run the full suite from the repo root:

```bash
cd astro-service && pytest -v
cd ../destiny-app && npx vitest run
```

Expected:
- All Python tests pass (191 + ~30 new psychology/shadow tests)
- All 82 Vitest tests pass
- No TypeScript errors (`npx tsc --noEmit`)
