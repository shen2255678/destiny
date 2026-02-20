# Phase G: Matching Algorithm v2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the matching engine to Lust × Soul dual-axis + four-track scoring (friend/passion/partner/soul), adding Mercury, Jupiter, Pluto, Chiron, Juno, House 4/8, and attachment questionnaire.

**Architecture:** Replace the single `Match_Score` in `matching.py` with a new `compute_match_v2` function that returns `{lust_score, soul_score, power, tracks, primary_track, quadrant, labels}`. The old `compute_match_score` is kept for backward-compat during transition. New chart fields are computed in `chart.py` and stored via the existing `birth-data` API.

**Tech Stack:** Python FastAPI + pyswisseph (astro-service), Next.js 14 API routes + Supabase (destiny-app), pytest, Vitest

---

## Task G1: DB Migration 007 — New Chart Columns

**Files:**
- Create: `destiny-app/supabase/migrations/007_phase_g_chart_columns.sql`

### Step 1: Write the migration SQL

```sql
-- Migration 007: Phase G — Expanded matching columns
-- New celestial bodies + House cusps + Attachment questionnaire

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS mercury_sign      TEXT,
  ADD COLUMN IF NOT EXISTS jupiter_sign      TEXT,
  ADD COLUMN IF NOT EXISTS pluto_sign        TEXT,
  ADD COLUMN IF NOT EXISTS chiron_sign       TEXT,
  ADD COLUMN IF NOT EXISTS juno_sign         TEXT,
  ADD COLUMN IF NOT EXISTS house4_sign       TEXT,
  ADD COLUMN IF NOT EXISTS house8_sign       TEXT,
  ADD COLUMN IF NOT EXISTS attachment_style  TEXT
    CHECK (attachment_style IN ('anxious', 'avoidant', 'secure')),
  ADD COLUMN IF NOT EXISTS attachment_role   TEXT
    CHECK (attachment_role IN ('dom_secure', 'sub_secure', 'balanced'));
```

### Step 2: Apply migration to Supabase

```bash
cd destiny-app
npx supabase db push
```

Expected: `Applied migration 007_phase_g_chart_columns.sql`

### Step 3: Verify columns exist

```bash
npx supabase db diff
```

Expected: No diff (migration fully applied)

### Step 4: Commit

```bash
git add destiny-app/supabase/migrations/007_phase_g_chart_columns.sql
git commit -m "feat(db): add phase G chart columns — migration 007"
```

---

## Task G2: chart.py — Add New Celestial Bodies + Houses

**Files:**
- Modify: `astro-service/chart.py`
- Test: `astro-service/test_chart.py`

### Step 1: Write the failing tests first

Add to `test_chart.py`:

```python
# ── Phase G: New Planets ──────────────────────────────────────

def test_tier1_has_mercury_jupiter_pluto():
    """Tier 1 chart should include mercury, jupiter, pluto signs."""
    result = calculate_chart(
        birth_date="1995-06-15",
        birth_time="precise",
        birth_time_exact="14:30",
        lat=25.033,
        lng=121.565,
        data_tier=1,
    )
    assert result["mercury_sign"] is not None
    assert result["jupiter_sign"] is not None
    assert result["pluto_sign"] is not None
    assert result["mercury_sign"] in (
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
    )

def test_tier3_has_mercury_jupiter_pluto():
    """Even Tier 3 (date-only) should return mercury/jupiter/pluto (slow planets)."""
    result = calculate_chart(birth_date="1995-06-15", data_tier=3)
    assert result["mercury_sign"] is not None
    assert result["jupiter_sign"] is not None
    assert result["pluto_sign"] is not None

def test_tier1_has_chiron_juno():
    """Tier 1 should include chiron and juno signs (requires ephe files)."""
    result = calculate_chart(
        birth_date="1995-06-15",
        birth_time="precise",
        birth_time_exact="14:30",
        lat=25.033,
        lng=121.565,
        data_tier=1,
    )
    # Chiron and Juno need ./ephe/seas_18.se1
    assert result["chiron_sign"] is not None
    assert result["juno_sign"] is not None

def test_tier1_has_house4_house8():
    """Tier 1 (precise time) should include house 4 and 8 signs."""
    result = calculate_chart(
        birth_date="1995-06-15",
        birth_time="precise",
        birth_time_exact="14:30",
        lat=25.033,
        lng=121.565,
        data_tier=1,
    )
    assert result["house4_sign"] is not None
    assert result["house8_sign"] is not None

def test_tier2_house4_house8_are_null():
    """Tier 2/3 should NOT have house 4/8 (requires precise time)."""
    result = calculate_chart(
        birth_date="1995-06-15",
        birth_time="morning",
        lat=25.033,
        lng=121.565,
        data_tier=2,
    )
    assert result["house4_sign"] is None
    assert result["house8_sign"] is None

def test_tier3_house4_house8_are_null():
    result = calculate_chart(birth_date="1995-06-15", data_tier=3)
    assert result["house4_sign"] is None
    assert result["house8_sign"] is None
```

### Step 2: Run tests to confirm they fail

```bash
cd astro-service
pytest test_chart.py -k "mercury_jupiter_pluto or chiron_juno or house4_house8" -v
```

Expected: FAIL — `KeyError` or `AssertionError` because fields don't exist yet.

### Step 3: Implement in chart.py

In `chart.py`, make these changes:

**a) At the top, add ephe path + new planet IDs:**

```python
import os
import swisseph as swe

# Set ephemeris path for asteroids (Chiron, Juno)
_EPHE_DIR = os.path.join(os.path.dirname(__file__), "ephe")
swe.set_ephe_path(_EPHE_DIR)

# Planet IDs — extend PLANETS dict
PLANETS = {
    "sun":     swe.SUN,
    "moon":    swe.MOON,
    "mercury": swe.MERCURY,
    "venus":   swe.VENUS,
    "mars":    swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn":  swe.SATURN,
    "pluto":   swe.PLUTO,
}

# Asteroid IDs (requires seas_18.se1)
ASTEROIDS = {
    "chiron": swe.CHIRON,
    "juno":   swe.AST_OFFSET + 3,
}
```

**b) In `calculate_chart`, add after the PLANETS loop:**

```python
# ── Asteroids (Chiron, Juno) ─────────────────────────────────
for name, asteroid_id in ASTEROIDS.items():
    try:
        pos, _ret = swe.calc_ut(jd, asteroid_id)
        result[f"{name}_sign"] = longitude_to_sign(pos[0])
    except Exception:
        result[f"{name}_sign"] = None  # ephe file missing — degrade gracefully

# ── House Cusps (Tier 1 only: House 4 and 8) ─────────────────
if data_tier == 1:
    cusps, ascmc = swe.houses(jd, lat, lng, b"P")
    # cusps[0] = House 1, cusps[3] = House 4, cusps[7] = House 8
    result["house4_sign"] = longitude_to_sign(cusps[3])
    result["house8_sign"] = longitude_to_sign(cusps[7])
else:
    result["house4_sign"] = None
    result["house8_sign"] = None
```

**c) Also fix: move the Tier 1 Ascendant block to use the same `cusps` already computed:**

```python
# ── Ascendant (Tier 1 only, uses same house cusps) ───────────
if data_tier >= 2:
    result["ascendant_sign"] = None
else:
    cusps, ascmc = swe.houses(jd, lat, lng, b"P")
    result["ascendant_sign"] = longitude_to_sign(ascmc[0])
    result["house4_sign"] = longitude_to_sign(cusps[3])
    result["house8_sign"] = longitude_to_sign(cusps[7])
```

> **Note:** Combine the two `swe.houses()` calls into one — compute ascendant AND house4/8 together in the same `if data_tier < 2` block.

### Step 4: Run all chart tests

```bash
pytest test_chart.py -v
```

Expected: All tests PASS (including old ones + 6 new ones).

### Step 5: Commit

```bash
git add astro-service/chart.py astro-service/test_chart.py
git commit -m "feat(chart): add Mercury/Jupiter/Pluto/Chiron/Juno + House 4/8"
```

---

## Task G3: bazi.py — Add ephe Path

**Files:**
- Modify: `astro-service/bazi.py` (add `swe.set_ephe_path` at module load)

### Step 1: Check if bazi.py already has set_ephe_path

Read the top of `bazi.py`. If `swe.set_ephe_path` is not present, add it.

### Step 2: Add at the top of bazi.py (after `import swisseph as swe`)

```python
import os
_EPHE_DIR = os.path.join(os.path.dirname(__file__), "ephe")
swe.set_ephe_path(_EPHE_DIR)
```

### Step 3: Run bazi tests to confirm nothing broke

```bash
pytest test_chart.py -v
```

Expected: All 36 tests PASS (the new 6 + existing 30).

### Step 4: Commit

```bash
git add astro-service/bazi.py
git commit -m "fix(bazi): set ephe path for asteroid ephemeris consistency"
```

---

## Task G4: matching.py — Full Rewrite to v2 Architecture

**Files:**
- Modify: `astro-service/matching.py`

> **Strategy:** Add `compute_match_v2` function with the new Lust/Soul/Power/Tracks architecture. Keep the old `compute_match_score` intact (backward compat). The FastAPI endpoint `/compute-match` will start returning the new format.

### Step 1: Write the failing integration test first (in test_matching.py)

Add to `test_matching.py`:

```python
from matching import compute_match_v2

class TestComputeMatchV2Integration:
    def _user(self, **kwargs):
        """Build a minimal v2 user dict."""
        defaults = {
            "data_tier": 3,
            "sun_sign": "aries", "moon_sign": None, "venus_sign": "taurus",
            "mars_sign": "gemini", "saturn_sign": "cancer",
            "mercury_sign": "aries", "jupiter_sign": "taurus",
            "pluto_sign": "scorpio",
            "chiron_sign": None, "juno_sign": None,
            "house4_sign": None, "house8_sign": None,
            "ascendant_sign": None,
            "bazi_element": None,
            "rpv_conflict": None, "rpv_power": None, "rpv_energy": None,
            "attachment_style": None,
        }
        defaults.update(kwargs)
        return defaults

    def test_v2_returns_required_keys(self):
        a = self._user()
        b = self._user(venus_sign="leo")
        result = compute_match_v2(a, b)
        assert "lust_score" in result
        assert "soul_score" in result
        assert "power" in result
        assert "tracks" in result
        assert "primary_track" in result
        assert "quadrant" in result
        assert "labels" in result

    def test_lust_score_in_range(self):
        a = self._user(rpv_power="control")
        b = self._user(rpv_power="follow")
        result = compute_match_v2(a, b)
        assert 0 <= result["lust_score"] <= 100

    def test_soul_score_in_range(self):
        a = self._user()
        b = self._user()
        result = compute_match_v2(a, b)
        assert 0 <= result["soul_score"] <= 100

    def test_primary_track_is_valid(self):
        a = self._user()
        b = self._user()
        result = compute_match_v2(a, b)
        assert result["primary_track"] in ("friend", "passion", "partner", "soul")

    def test_quadrant_is_valid(self):
        a = self._user()
        b = self._user()
        result = compute_match_v2(a, b)
        assert result["quadrant"] in ("lover", "soulmate", "colleague", "partner")
```

### Step 2: Run to confirm it fails

```bash
pytest test_matching.py::TestComputeMatchV2Integration -v
```

Expected: FAIL — `ImportError: cannot import name 'compute_match_v2'`

### Step 3: Implement `compute_match_v2` in matching.py

Add these new functions to `matching.py` (do NOT remove old ones):

```python
# ═══════════════════════════════════════════════════════════════════
# Phase G: Matching v2 — Lust × Soul + Four Tracks
# ═══════════════════════════════════════════════════════════════════

# AttachmentFit matrix [style_a][style_b] → 0.0-1.0
ATTACHMENT_FIT: dict[str, dict[str, float]] = {
    "anxious":  {"anxious": 0.50, "avoidant": 0.70, "secure": 0.80},
    "avoidant": {"anxious": 0.70, "avoidant": 0.55, "secure": 0.75},
    "secure":   {"anxious": 0.80, "avoidant": 0.75, "secure": 0.90},
}

NEUTRAL_SIGNAL = 0.65  # default when field is None


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _signal(user_a: dict, user_b: dict, field_a: str, field_b: str | None = None) -> float:
    """Compute aspect score between two sign fields. Returns NEUTRAL_SIGNAL if either is None."""
    fa = field_b or field_a  # allow asymmetric cross-comparison
    return compute_sign_aspect(user_a.get(field_a), user_b.get(fa))


def _rpv_to_frame(rpv_power: str | None, rpv_conflict: str | None) -> float:
    """Map RPV responses to a frame stability score (0-100)."""
    frame = 50.0  # neutral baseline
    if rpv_power == "control":
        frame += 20
    elif rpv_power == "follow":
        frame -= 20
    if rpv_conflict == "cold_war":
        frame += 10
    elif rpv_conflict == "argue":
        frame -= 10
    return frame


def compute_lust_score(user_a: dict, user_b: dict) -> float:
    """Lust Score (X axis): physical/desire attraction.

    Weights (Eros-absent version):
      venus   × 0.20
      mars    × 0.25
      house8  × 0.15  (0 when tier 2/3)
      pluto   × 0.25
      power_fit × 0.30

    Multiplier: × 1.2 if bazi_clash between day masters.
    """
    venus  = compute_sign_aspect(user_a.get("venus_sign"),  user_b.get("venus_sign"))
    mars   = compute_sign_aspect(user_a.get("mars_sign"),   user_b.get("mars_sign"))
    pluto  = compute_sign_aspect(user_a.get("pluto_sign"),  user_b.get("pluto_sign"))

    # House 8: use aspect if both have it, else 0 (degrade gracefully)
    h8_a = user_a.get("house8_sign")
    h8_b = user_b.get("house8_sign")
    if h8_a and h8_b:
        house8 = compute_sign_aspect(h8_a, h8_b)
    else:
        house8 = 0.0

    # Power fit from RPV
    power_score = compute_power_score(user_a, user_b)

    score = (
        venus   * 0.20 +
        mars    * 0.25 +
        house8  * 0.15 +
        pluto   * 0.25 +
        power_score * 0.30
    )

    # BaZi clash multiplier (相剋 = high-tension attraction)
    elem_a = user_a.get("bazi_element")
    elem_b = user_b.get("bazi_element")
    if elem_a and elem_b:
        rel = analyze_element_relation(elem_a, elem_b)
        if rel["relation"] in ("a_restricts_b", "b_restricts_a"):
            score *= 1.2

    return _clamp(score * 100)


def compute_soul_score(user_a: dict, user_b: dict) -> float:
    """Soul Score (Y axis): depth / long-term commitment.

    Weights:
      moon       × 0.25
      mercury    × 0.20
      house4     × 0.15  (0 when tier 2/3)
      saturn     × 0.20
      attachment × 0.20
      juno       × 0.20

    Multiplier: × 1.2 if bazi_generation between day masters.
    """
    moon    = compute_sign_aspect(user_a.get("moon_sign"),    user_b.get("moon_sign"))
    mercury = compute_sign_aspect(user_a.get("mercury_sign"), user_b.get("mercury_sign"))
    saturn  = compute_sign_aspect(user_a.get("saturn_sign"),  user_b.get("saturn_sign"))

    h4_a = user_a.get("house4_sign")
    h4_b = user_b.get("house4_sign")
    house4 = compute_sign_aspect(h4_a, h4_b) if (h4_a and h4_b) else 0.0

    juno_a = user_a.get("juno_sign")
    juno_b = user_b.get("juno_sign")
    juno = compute_sign_aspect(juno_a, juno_b) if (juno_a and juno_b) else NEUTRAL_SIGNAL

    # Attachment fit
    style_a = user_a.get("attachment_style")
    style_b = user_b.get("attachment_style")
    if style_a and style_b and style_a in ATTACHMENT_FIT:
        attachment = ATTACHMENT_FIT[style_a].get(style_b, NEUTRAL_SIGNAL)
    else:
        attachment = NEUTRAL_SIGNAL

    score = (
        moon       * 0.25 +
        mercury    * 0.20 +
        house4     * 0.15 +
        saturn     * 0.20 +
        attachment * 0.20 +
        juno       * 0.20
    )

    # BaZi generation multiplier (相生 = nurturing)
    elem_a = user_a.get("bazi_element")
    elem_b = user_b.get("bazi_element")
    if elem_a and elem_b:
        rel = analyze_element_relation(elem_a, elem_b)
        if rel["relation"] in ("a_generates_b", "b_generates_a"):
            score *= 1.2

    return _clamp(score * 100)


def compute_power_v2(user_a: dict, user_b: dict, chiron_triggered: bool = False) -> dict:
    """Power D/s Frame calculation.

    frame_A / frame_B derived from RPV.
    Chiron rule: if A's Mars/Pluto hard-aspects B's Chiron → frame_B -15.
    RPV: +20 control/-20 follow, +10 cold_war/-10 argue.
    """
    frame_a = _rpv_to_frame(user_a.get("rpv_power"), user_a.get("rpv_conflict"))
    frame_b = _rpv_to_frame(user_b.get("rpv_power"), user_b.get("rpv_conflict"))

    frame_break = chiron_triggered
    if chiron_triggered:
        frame_b -= 15

    rpv = frame_a - frame_b

    if rpv > 15:
        viewer_role, target_role = "Dom", "Sub"
    elif rpv < -15:
        viewer_role, target_role = "Sub", "Dom"
    else:
        viewer_role, target_role = "Equal", "Equal"

    return {
        "rpv": round(rpv, 1),
        "frame_break": frame_break,
        "viewer_role": viewer_role,
        "target_role": target_role,
    }


def _check_chiron_triggered(user_a: dict, user_b: dict) -> bool:
    """Check if A's Mars or Pluto forms hard aspect (square/opposition) to B's Chiron.

    Uses sign-level approximation: square = 3 signs apart, opposition = 6 apart.
    """
    chiron_b = user_b.get("chiron_sign")
    if not chiron_b:
        return False
    mars_a  = user_a.get("mars_sign")
    pluto_a = user_a.get("pluto_sign")

    def is_hard_aspect(sign_x: str | None, sign_y: str) -> bool:
        if not sign_x or sign_x not in SIGN_INDEX or sign_y not in SIGN_INDEX:
            return False
        dist = abs(SIGN_INDEX[sign_x] - SIGN_INDEX[sign_y]) % 12
        if dist > 6:
            dist = 12 - dist
        return dist in (3, 6)  # square or opposition

    return is_hard_aspect(mars_a, chiron_b) or is_hard_aspect(pluto_a, chiron_b)


def compute_tracks(user_a: dict, user_b: dict, power: dict) -> dict:
    """Four-track scoring: friend / passion / partner / soul.

    Returns each track 0-100.
    """
    # Helper signals (0.0-1.0)
    mercury = compute_sign_aspect(user_a.get("mercury_sign"), user_b.get("mercury_sign"))
    jupiter = compute_sign_aspect(user_a.get("jupiter_sign"), user_b.get("jupiter_sign"))
    mars    = compute_sign_aspect(user_a.get("mars_sign"),    user_b.get("mars_sign"))
    venus   = compute_sign_aspect(user_a.get("venus_sign"),   user_b.get("venus_sign"))
    pluto   = compute_sign_aspect(user_a.get("pluto_sign"),   user_b.get("pluto_sign"))
    moon    = compute_sign_aspect(user_a.get("moon_sign"),    user_b.get("moon_sign"))

    h8_a, h8_b = user_a.get("house8_sign"), user_b.get("house8_sign")
    house8 = compute_sign_aspect(h8_a, h8_b) if (h8_a and h8_b) else 0.0

    juno_a, juno_b = user_a.get("juno_sign"), user_b.get("juno_sign")
    juno = compute_sign_aspect(juno_a, juno_b) if (juno_a and juno_b) else NEUTRAL_SIGNAL

    chiron_a, chiron_b = user_a.get("chiron_sign"), user_b.get("chiron_sign")
    chiron = compute_sign_aspect(chiron_a, chiron_b) if (chiron_a and chiron_b) else NEUTRAL_SIGNAL

    # BaZi signals
    elem_a = user_a.get("bazi_element")
    elem_b = user_b.get("bazi_element")
    bazi_harmony = bazi_clash = bazi_generation = False
    if elem_a and elem_b:
        rel = analyze_element_relation(elem_a, elem_b)
        bazi_harmony    = rel["relation"] == "same"
        bazi_clash      = rel["relation"] in ("a_restricts_b", "b_restricts_a")
        bazi_generation = rel["relation"] in ("a_generates_b", "b_generates_a")

    # Tracks
    friend = (
        0.40 * mercury +
        0.40 * jupiter +
        0.20 * (1.0 if bazi_harmony else 0.0)
    )

    passion_extremity = max(pluto, house8)
    passion = (
        0.30 * mars +
        0.30 * venus +
        0.10 * passion_extremity +
        0.30 * (1.0 if bazi_clash else 0.0)
    )

    partner = (
        0.35 * moon +
        0.35 * juno +
        0.30 * (1.0 if bazi_generation else 0.0)
    )

    soul_track = (
        0.40 * chiron +
        0.40 * pluto +
        0.20 * (1.0 if bazi_harmony else 0.0)  # useful_god_complement → bazi_harmony proxy
    )

    # Chiron frame_break bonus on soul track
    if power["frame_break"]:
        soul_track += 0.10

    return {
        "friend":  round(_clamp(friend  * 100), 1),
        "passion": round(_clamp(passion * 100), 1),
        "partner": round(_clamp(partner * 100), 1),
        "soul":    round(_clamp(soul_track * 100), 1),
    }


def classify_quadrant(lust_score: float, soul_score: float, threshold: float = 60.0) -> str:
    """Lust × Soul 2D quadrant.

    lust ≥ threshold, soul ≥ threshold → soulmate
    lust ≥ threshold, soul <  threshold → lover
    lust <  threshold, soul ≥ threshold → partner
    lust <  threshold, soul <  threshold → colleague
    """
    if lust_score >= threshold and soul_score >= threshold:
        return "soulmate"
    if lust_score >= threshold:
        return "lover"
    if soul_score >= threshold:
        return "partner"
    return "colleague"


# Track label display map (Traditional Chinese)
TRACK_LABELS = {
    "friend":  "✦ 朋友型連結",
    "passion": "✦ 激情型連結",
    "partner": "✦ 伴侶型連結",
    "soul":    "✦ 靈魂型連結",
}


def compute_match_v2(user_a: dict, user_b: dict) -> dict:
    """Compute full v2 match score.

    Returns:
      lust_score   (0-100)
      soul_score   (0-100)
      power        {rpv, frame_break, viewer_role, target_role}
      tracks       {friend, passion, partner, soul}  (0-100 each)
      primary_track  argmax of tracks
      quadrant     soulmate | lover | partner | colleague
      labels       [primary_track display label]
    """
    chiron_triggered = _check_chiron_triggered(user_a, user_b)
    power  = compute_power_v2(user_a, user_b, chiron_triggered)
    lust   = compute_lust_score(user_a, user_b)
    soul   = compute_soul_score(user_a, user_b)
    tracks = compute_tracks(user_a, user_b, power)

    primary_track = max(tracks, key=lambda k: tracks[k])
    quadrant      = classify_quadrant(lust, soul)
    label         = TRACK_LABELS.get(primary_track, primary_track)

    return {
        "lust_score":    round(lust, 1),
        "soul_score":    round(soul, 1),
        "power":         power,
        "tracks":        tracks,
        "primary_track": primary_track,
        "quadrant":      quadrant,
        "labels":        [label],
    }
```

### Step 4: Run the integration test

```bash
pytest test_matching.py::TestComputeMatchV2Integration -v
```

Expected: All 5 tests PASS.

### Step 5: Commit

```bash
git add astro-service/matching.py
git commit -m "feat(matching): add compute_match_v2 — Lust/Soul/Power/Tracks engine"
```

---

## Task G5: test_matching.py — Full v2 Test Suite (~37 tests)

**Files:**
- Modify: `astro-service/test_matching.py`

### Step 1: Write all new test classes

Add after `TestComputeMatchV2Integration`:

```python
from matching import (
    compute_lust_score,
    compute_soul_score,
    compute_power_v2,
    compute_tracks,
    classify_quadrant,
    _check_chiron_triggered,
    ATTACHMENT_FIT,
)


# ── compute_lust_score ────────────────────────────────────────

class TestLustScore:
    def _user(self, venus="aries", mars="aries", pluto="scorpio",
              house8=None, bazi_elem=None, rpv_power=None, rpv_conflict=None):
        return {
            "venus_sign": venus, "mars_sign": mars, "pluto_sign": pluto,
            "house8_sign": house8, "bazi_element": bazi_elem,
            "rpv_power": rpv_power, "rpv_conflict": rpv_conflict,
        }

    def test_score_in_range(self):
        a = self._user(rpv_power="control")
        b = self._user(rpv_power="follow")
        assert 0 <= compute_lust_score(a, b) <= 100

    def test_bazi_clash_multiplier_increases_score(self):
        """Metal restricts Wood → × 1.2 multiplier."""
        base_a = self._user()
        base_b = self._user()
        a_clash = self._user(bazi_elem="metal")
        b_clash = self._user(bazi_elem="wood")
        score_no_clash = compute_lust_score(base_a, base_b)
        score_clash = compute_lust_score(a_clash, b_clash)
        assert score_clash > score_no_clash

    def test_no_house8_gives_zero_house8_contribution(self):
        """When house8_sign is None, house8 weight = 0."""
        a = self._user(house8=None)
        b = self._user(house8=None)
        a_with = {**a, "house8_sign": "scorpio"}
        b_with = {**b, "house8_sign": "scorpio"}
        score_without = compute_lust_score(a, b)
        score_with = compute_lust_score(a_with, b_with)
        # Having matching house8 should increase or not decrease score
        assert score_with >= score_without

    def test_power_control_follow_increases_lust(self):
        """Complementary RPV power → higher power_fit → higher lust."""
        a = self._user(rpv_power="control")
        b = self._user(rpv_power="follow")
        a_same = self._user(rpv_power="control")
        b_same = self._user(rpv_power="control")
        assert compute_lust_score(a, b) > compute_lust_score(a_same, b_same)


# ── compute_soul_score ────────────────────────────────────────

class TestSoulScore:
    def _user(self, moon="cancer", mercury="gemini", saturn="capricorn",
              house4=None, juno=None, bazi_elem=None, attachment=None):
        return {
            "moon_sign": moon, "mercury_sign": mercury, "saturn_sign": saturn,
            "house4_sign": house4, "juno_sign": juno,
            "bazi_element": bazi_elem, "attachment_style": attachment,
        }

    def test_score_in_range(self):
        a = self._user()
        b = self._user()
        assert 0 <= compute_soul_score(a, b) <= 100

    def test_bazi_generation_multiplier(self):
        """Wood generates Fire → × 1.2 multiplier."""
        a_gen = self._user(bazi_elem="wood")
        b_gen = self._user(bazi_elem="fire")
        a_no  = self._user()
        b_no  = self._user()
        assert compute_soul_score(a_gen, b_gen) > compute_soul_score(a_no, b_no)

    def test_secure_secure_attachment_highest(self):
        """secure+secure attachment fit = 0.90 (highest)."""
        a = self._user(attachment="secure")
        b = self._user(attachment="secure")
        score = compute_soul_score(a, b)
        # secure+anxious = 0.80; secure+secure should yield higher soul
        a2 = self._user(attachment="anxious")
        score2 = compute_soul_score(a2, b)
        assert score > score2

    def test_missing_attachment_uses_neutral(self):
        """No attachment_style → neutral 0.65, should not crash."""
        a = self._user(attachment=None)
        b = self._user(attachment=None)
        assert 0 <= compute_soul_score(a, b) <= 100


# ── compute_power_v2 ──────────────────────────────────────────

class TestComputePowerV2:
    def test_control_vs_follow_gives_dom_sub(self):
        """control (frame+20) vs follow (frame-20) → rpv=40 → Dom/Sub."""
        a = {"rpv_power": "control", "rpv_conflict": None}
        b = {"rpv_power": "follow",  "rpv_conflict": None}
        result = compute_power_v2(a, b)
        assert result["viewer_role"] == "Dom"
        assert result["target_role"] == "Sub"

    def test_equal_rpv_gives_equal_roles(self):
        """Same RPV → frame_A == frame_B → Equal/Equal."""
        a = {"rpv_power": "control", "rpv_conflict": "cold_war"}
        b = {"rpv_power": "control", "rpv_conflict": "cold_war"}
        result = compute_power_v2(a, b)
        assert result["viewer_role"] == "Equal"
        assert result["rpv"] == pytest.approx(0.0)

    def test_chiron_triggered_sets_frame_break(self):
        """chiron_triggered=True → frame_break=True, frame_b -15."""
        a = {"rpv_power": None, "rpv_conflict": None}
        b = {"rpv_power": None, "rpv_conflict": None}
        result = compute_power_v2(a, b, chiron_triggered=True)
        assert result["frame_break"] is True

    def test_chiron_trigger_shifts_rpv(self):
        """Chiron trigger reduces frame_b by 15 → rpv increases by 15."""
        a = {"rpv_power": None, "rpv_conflict": None}
        b = {"rpv_power": None, "rpv_conflict": None}
        no_trigger = compute_power_v2(a, b, chiron_triggered=False)
        with_trigger = compute_power_v2(a, b, chiron_triggered=True)
        assert with_trigger["rpv"] == pytest.approx(no_trigger["rpv"] + 15)


# ── _check_chiron_triggered ───────────────────────────────────

class TestChironTriggered:
    def test_mars_square_chiron_triggers(self):
        """Mars square (3 signs) to Chiron = hard aspect → triggered."""
        a = {"mars_sign": "aries", "pluto_sign": None}   # aries
        b = {"chiron_sign": "cancer"}                     # cancer = 3 from aries
        assert _check_chiron_triggered(a, b) is True

    def test_pluto_opposition_chiron_triggers(self):
        """Pluto opposition (6 signs) to Chiron → triggered."""
        a = {"mars_sign": None, "pluto_sign": "aries"}
        b = {"chiron_sign": "libra"}   # 6 from aries
        assert _check_chiron_triggered(a, b) is True

    def test_no_hard_aspect_does_not_trigger(self):
        """Trine (4 signs) is not a hard aspect."""
        a = {"mars_sign": "aries", "pluto_sign": None}
        b = {"chiron_sign": "leo"}   # 4 from aries (trine)
        assert _check_chiron_triggered(a, b) is False

    def test_no_chiron_does_not_trigger(self):
        """Missing Chiron → no trigger."""
        a = {"mars_sign": "aries", "pluto_sign": "aries"}
        b = {"chiron_sign": None}
        assert _check_chiron_triggered(a, b) is False


# ── classify_quadrant ─────────────────────────────────────────

class TestClassifyQuadrant:
    def test_soulmate(self):
        assert classify_quadrant(75, 80) == "soulmate"

    def test_lover(self):
        assert classify_quadrant(70, 40) == "lover"

    def test_partner(self):
        assert classify_quadrant(40, 70) == "partner"

    def test_colleague(self):
        assert classify_quadrant(40, 40) == "colleague"

    def test_boundary_at_threshold(self):
        """Exactly at threshold (60) → included in high category."""
        assert classify_quadrant(60, 60) == "soulmate"
        assert classify_quadrant(60, 59) == "lover"
        assert classify_quadrant(59, 60) == "partner"


# ── AttachmentFit matrix ──────────────────────────────────────

class TestAttachmentFit:
    def test_secure_secure_highest(self):
        assert ATTACHMENT_FIT["secure"]["secure"] == 0.90

    def test_anxious_avoidant_tension_attraction(self):
        assert ATTACHMENT_FIT["anxious"]["avoidant"] == 0.70

    def test_matrix_symmetric_for_anxious_avoidant(self):
        """anxious→avoidant should equal avoidant→anxious."""
        assert ATTACHMENT_FIT["anxious"]["avoidant"] == ATTACHMENT_FIT["avoidant"]["anxious"]
```

### Step 2: Run all new tests

```bash
pytest test_matching.py -v -k "Lust or Soul or PowerV2 or Chiron or Quadrant or Attachment or V2"
```

Expected: All new tests PASS.

### Step 3: Run the full test suite

```bash
pytest -v
```

Expected: All 71+ tests PASS (old 71 + new ~37).

### Step 4: Commit

```bash
git add astro-service/test_matching.py
git commit -m "test(matching): add 37 Phase G v2 tests for Lust/Soul/Power/Tracks/Quadrant"
```

---

## Task G6: Next.js — New Attachment Onboarding Endpoint

**Files:**
- Create: `destiny-app/src/app/api/onboarding/attachment/route.ts`
- Test: `destiny-app/src/__tests__/api/onboarding/attachment.test.ts`

### Step 1: Write the failing test

Create `destiny-app/src/__tests__/api/onboarding/attachment.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock Supabase
const mockUpdate = vi.fn().mockReturnValue({ data: {}, error: null })
const mockEq = vi.fn().mockReturnValue({ data: {}, error: null })
const mockGetUser = vi.fn().mockResolvedValue({
  data: { user: { id: 'user-123', email: 'test@example.com' } },
  error: null,
})
const mockFrom = vi.fn().mockReturnValue({
  update: mockUpdate,
})
mockUpdate.mockReturnValue({ eq: mockEq })

vi.mock('@/lib/supabase/server', () => ({
  createClient: vi.fn().mockResolvedValue({
    auth: { getUser: mockGetUser },
    from: mockFrom,
  }),
}))

import { POST } from '@/app/api/onboarding/attachment/route'

describe('POST /api/onboarding/attachment', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetUser.mockResolvedValue({
      data: { user: { id: 'user-123', email: 'test@example.com' } },
      error: null,
    })
    mockFrom.mockReturnValue({ update: mockUpdate })
    mockUpdate.mockReturnValue({ eq: mockEq })
    mockEq.mockResolvedValue({ data: {}, error: null })
  })

  it('returns 400 if attachment_style is missing', async () => {
    const req = new Request('http://localhost/api/onboarding/attachment', {
      method: 'POST',
      body: JSON.stringify({ attachment_role: 'balanced' }),
    })
    const res = await POST(req)
    expect(res.status).toBe(400)
  })

  it('returns 400 for invalid attachment_style', async () => {
    const req = new Request('http://localhost/api/onboarding/attachment', {
      method: 'POST',
      body: JSON.stringify({ attachment_style: 'invalid', attachment_role: 'balanced' }),
    })
    const res = await POST(req)
    expect(res.status).toBe(400)
  })

  it('returns 200 and saves valid attachment data', async () => {
    const req = new Request('http://localhost/api/onboarding/attachment', {
      method: 'POST',
      body: JSON.stringify({ attachment_style: 'secure', attachment_role: 'balanced' }),
    })
    const res = await POST(req)
    expect(res.status).toBe(200)
    expect(mockFrom).toHaveBeenCalledWith('users')
  })

  it('accepts all valid attachment_style values', async () => {
    for (const style of ['anxious', 'avoidant', 'secure']) {
      const req = new Request('http://localhost/api/onboarding/attachment', {
        method: 'POST',
        body: JSON.stringify({ attachment_style: style }),
      })
      const res = await POST(req)
      expect(res.status).toBe(200)
    }
  })
})
```

### Step 2: Run to confirm it fails

```bash
cd destiny-app
npx vitest run src/__tests__/api/onboarding/attachment.test.ts
```

Expected: FAIL — module not found.

### Step 3: Implement the route

Create `destiny-app/src/app/api/onboarding/attachment/route.ts`:

```typescript
import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

const VALID_STYLES = ['anxious', 'avoidant', 'secure'] as const
const VALID_ROLES  = ['dom_secure', 'sub_secure', 'balanced'] as const

export async function POST(request: Request) {
  const body = await request.json()
  const { attachment_style, attachment_role } = body

  if (!attachment_style) {
    return NextResponse.json({ error: 'Missing required field: attachment_style' }, { status: 400 })
  }
  if (!VALID_STYLES.includes(attachment_style)) {
    return NextResponse.json(
      { error: `Invalid attachment_style. Must be: ${VALID_STYLES.join(', ')}` },
      { status: 400 }
    )
  }
  if (attachment_role && !VALID_ROLES.includes(attachment_role)) {
    return NextResponse.json(
      { error: `Invalid attachment_role. Must be: ${VALID_ROLES.join(', ')}` },
      { status: 400 }
    )
  }

  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  const update: Record<string, string> = {
    attachment_style,
    onboarding_step: 'photos',
  }
  if (attachment_role) {
    update.attachment_role = attachment_role
  }

  const { error } = await supabase
    .from('users')
    .update(update)
    .eq('id', user.id)

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json({ success: true })
}
```

### Step 4: Run tests

```bash
npx vitest run src/__tests__/api/onboarding/attachment.test.ts
```

Expected: All 4 tests PASS.

### Step 5: Commit

```bash
git add destiny-app/src/app/api/onboarding/attachment/route.ts
git add destiny-app/src/__tests__/api/onboarding/attachment.test.ts
git commit -m "feat(api): add POST /api/onboarding/attachment endpoint"
```

---

## Task G7: birth-data route — Write New Chart Fields to DB

**Files:**
- Modify: `destiny-app/src/app/api/onboarding/birth-data/route.ts` (lines 264-278)

### Step 1: Read the current chart update block

Current code writes: `sun_sign, moon_sign, venus_sign, mars_sign, saturn_sign, ascendant_sign, element_primary, bazi_day_master, bazi_element, bazi_four_pillars`.

### Step 2: Extend the update block to include Phase G fields

Replace the `.update({...})` call (lines 264-278) with:

```typescript
await supabase
  .from('users')
  .update({
    sun_sign:        chart.sun_sign ?? null,
    moon_sign:       chart.moon_sign ?? null,
    venus_sign:      chart.venus_sign ?? null,
    mars_sign:       chart.mars_sign ?? null,
    saturn_sign:     chart.saturn_sign ?? null,
    ascendant_sign:  chart.ascendant_sign ?? null,
    element_primary: chart.element_primary ?? null,
    bazi_day_master: chart.bazi?.day_master ?? null,
    bazi_element:    chart.bazi?.day_master_element ?? null,
    bazi_four_pillars: chart.bazi ?? null,
    // Phase G new fields
    mercury_sign:  chart.mercury_sign ?? null,
    jupiter_sign:  chart.jupiter_sign ?? null,
    pluto_sign:    chart.pluto_sign ?? null,
    chiron_sign:   chart.chiron_sign ?? null,
    juno_sign:     chart.juno_sign ?? null,
    house4_sign:   chart.house4_sign ?? null,
    house8_sign:   chart.house8_sign ?? null,
  })
  .eq('id', user.id)
```

### Step 3: Run existing API tests

```bash
cd destiny-app
npx vitest run src/__tests__/api/onboarding/birth-data.test.ts
```

Expected: All tests PASS (adding new null-safe fields shouldn't break anything).

### Step 4: Commit

```bash
git add destiny-app/src/app/api/onboarding/birth-data/route.ts
git commit -m "feat(api): write Phase G chart fields to users table in birth-data route"
```

---

## Task G8: types.ts — Add New Column Types

**Files:**
- Modify: `destiny-app/src/lib/supabase/types.ts`

### Step 1: Read the current types file

Find the `users` table Row type.

### Step 2: Add new fields to the Row type

In the `users` table `Row` interface, add after `saturn_sign`:

```typescript
mercury_sign: string | null
jupiter_sign: string | null
pluto_sign: string | null
chiron_sign: string | null
juno_sign: string | null
house4_sign: string | null
house8_sign: string | null
attachment_style: 'anxious' | 'avoidant' | 'secure' | null
attachment_role: 'dom_secure' | 'sub_secure' | 'balanced' | null
```

Also add these to the `Insert` and `Update` interfaces (with `?:` optional syntax).

### Step 3: Run type checks

```bash
cd destiny-app
npx tsc --noEmit
```

Expected: No type errors.

### Step 4: Commit

```bash
git add destiny-app/src/lib/supabase/types.ts
git commit -m "feat(types): add Phase G chart and attachment columns to Supabase types"
```

---

## Task G9: main.py — Update /compute-match to v2 + Run Final Tests

**Files:**
- Modify: `astro-service/main.py`

### Step 1: Update the /compute-match endpoint to use v2

In `main.py`, update the import and the `compute_match` endpoint:

```python
from matching import compute_match_score, compute_match_v2

@app.post("/compute-match")
def compute_match(req: MatchRequest):
    """Compute match score between two user profiles (v2 architecture).

    user_a / user_b should contain flat profile fields including Phase G:
      data_tier, sun_sign, moon_sign, venus_sign, mars_sign, saturn_sign,
      mercury_sign, jupiter_sign, pluto_sign, chiron_sign, juno_sign,
      house4_sign, house8_sign, ascendant_sign,
      bazi_element, rpv_conflict, rpv_power, rpv_energy, attachment_style
    """
    try:
        result = compute_match_v2(req.user_a, req.user_b)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Step 2: Run all Python tests

```bash
cd astro-service
pytest -v
```

Expected: All tests PASS (minimum 108: old 71 + new 37).

### Step 3: Manual smoke test (start the service)

```bash
uvicorn main:app --port 8001 --reload
```

Then in another terminal:

```bash
curl -s -X POST http://localhost:8001/compute-match \
  -H "Content-Type: application/json" \
  -d '{
    "user_a": {
      "data_tier": 1,
      "sun_sign": "gemini",
      "moon_sign": "cancer",
      "venus_sign": "taurus",
      "mars_sign": "aries",
      "mercury_sign": "gemini",
      "jupiter_sign": "leo",
      "pluto_sign": "scorpio",
      "chiron_sign": "cancer",
      "juno_sign": "virgo",
      "house4_sign": "cancer",
      "house8_sign": "scorpio",
      "bazi_element": "wood",
      "rpv_power": "control",
      "rpv_conflict": "cold_war",
      "attachment_style": "secure"
    },
    "user_b": {
      "data_tier": 1,
      "sun_sign": "scorpio",
      "moon_sign": "pisces",
      "venus_sign": "libra",
      "mars_sign": "capricorn",
      "mercury_sign": "scorpio",
      "jupiter_sign": "sagittarius",
      "pluto_sign": "sagittarius",
      "chiron_sign": "libra",
      "juno_sign": "cancer",
      "house4_sign": "pisces",
      "house8_sign": "cancer",
      "bazi_element": "fire",
      "rpv_power": "follow",
      "rpv_conflict": "argue",
      "attachment_style": "anxious"
    }
  }' | python -m json.tool
```

Expected: JSON with `lust_score`, `soul_score`, `power`, `tracks`, `primary_track`, `quadrant`, `labels`.

### Step 4: Run all Next.js tests

```bash
cd destiny-app
npx vitest run
```

Expected: All 82+ tests PASS.

### Step 5: Final commit

```bash
git add astro-service/main.py
git commit -m "feat(api): update /compute-match to v2 — Lust/Soul/Power/Tracks output"
```

---

## Summary Checklist

| Task | Files Changed | Tests |
|------|--------------|-------|
| G1: Migration 007 | `migrations/007_phase_g_chart_columns.sql` | Manual (supabase db push) |
| G2: chart.py expansion | `chart.py`, `test_chart.py` | +6 tests |
| G3: bazi.py ephe path | `bazi.py` | Existing tests |
| G4: matching.py v2 | `matching.py` | +5 integration tests |
| G5: test_matching.py v2 | `test_matching.py` | +32 unit tests |
| G6: attachment route | `attachment/route.ts`, `attachment.test.ts` | +4 tests |
| G7: birth-data fields | `birth-data/route.ts` | Existing tests |
| G8: types.ts update | `types.ts` | tsc --noEmit |
| G9: main.py v2 endpoint | `main.py` | All 108+ tests |

**Total new tests: ~47**
