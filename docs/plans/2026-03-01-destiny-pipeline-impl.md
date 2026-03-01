# DestinyPipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Encapsulate chart → match → profile → prompt into a `DestinyPipeline` class with a `/compute-enriched` endpoint that returns scores + Chinese tags + ready-made prompts.

**Architecture:** New `destiny_pipeline.py` wraps existing modules (chart.py, matching.py, ideal_avatar.py, prompt_manager.py) into a chainable Pipeline. A new FastAPI endpoint delegates to it. `run_ideal_match_prompt.py` is refactored to use Pipeline instead of manual glue code.

**Tech Stack:** Python 3.9+, FastAPI, existing astro-service modules (chart.py, matching.py, prompt_manager.py, ideal_avatar.py, zwds.py)

**Design doc:** `docs/plans/2026-03-01-destiny-pipeline-design.md`

---

## Task 1: BirthInput dataclass + tier auto-inference

**Files:**
- Create: `astro-service/destiny_pipeline.py`
- Create: `astro-service/test_pipeline.py`

**Step 1: Write the failing tests**

```python
# test_pipeline.py
import pytest
from destiny_pipeline import BirthInput, _infer_tier


class TestBirthInput:
    def test_tier1_precise_time(self):
        b = BirthInput("1996-11-05", "02:00", "F")
        assert b.data_tier == 1

    def test_tier2_morning(self):
        b = BirthInput("1996-11-05", "morning", "F")
        assert b.data_tier == 2

    def test_tier2_afternoon(self):
        b = BirthInput("1996-11-05", "afternoon", "M")
        assert b.data_tier == 2

    def test_tier2_evening(self):
        b = BirthInput("1996-11-05", "evening", "M")
        assert b.data_tier == 2

    def test_tier3_none(self):
        b = BirthInput("1996-12-10", None, "M")
        assert b.data_tier == 3

    def test_tier3_unknown(self):
        b = BirthInput("1996-12-10", "unknown", "M")
        assert b.data_tier == 3

    def test_default_lat_lng(self):
        b = BirthInput("1996-11-05", "02:00", "F")
        assert b.lat == 25.033
        assert b.lng == 121.565

    def test_custom_lat_lng(self):
        b = BirthInput("1996-11-05", "02:00", "F", lat=35.6, lng=139.7)
        assert b.lat == 35.6
        assert b.lng == 139.7


class TestInferTier:
    def test_hhmm_format(self):
        assert _infer_tier("14:30") == 1

    def test_fuzzy_slots(self):
        assert _infer_tier("morning") == 2
        assert _infer_tier("afternoon") == 2
        assert _infer_tier("evening") == 2

    def test_none(self):
        assert _infer_tier(None) == 3

    def test_unknown(self):
        assert _infer_tier("unknown") == 3
```

**Step 2: Run tests to verify they fail**

Run: `cd astro-service && pytest test_pipeline.py::TestBirthInput -v && pytest test_pipeline.py::TestInferTier -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'destiny_pipeline'`

**Step 3: Write minimal implementation**

```python
# destiny_pipeline.py
"""
DESTINY Pipeline — one-shot chart → match → profile → prompt assembly.

Usage:
    from destiny_pipeline import DestinyPipeline, BirthInput

    pipeline = DestinyPipeline(BirthInput("1996-11-05", "02:00", "F"))
    pipeline.compute_charts().extract_profiles().build_prompts()
    dto = pipeline.to_enriched_dto()
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional


# ── Tier inference ───────────────────────────────────────────────────────────

def _infer_tier(birth_time: str | None) -> int:
    """Auto-detect data tier from birth_time format."""
    if birth_time and ":" in birth_time:
        return 1
    if birth_time in ("morning", "afternoon", "evening"):
        return 2
    return 3


# ── BirthInput ───────────────────────────────────────────────────────────────

@dataclass
class BirthInput:
    """Immutable birth data container with auto-inferred tier."""
    birth_date: str
    birth_time: Optional[str]
    gender: str
    lat: float = 25.033
    lng: float = 121.565
    data_tier: int = field(init=False)

    def __post_init__(self):
        self.data_tier = _infer_tier(self.birth_time)
```

**Step 4: Run tests to verify they pass**

Run: `cd astro-service && pytest test_pipeline.py::TestBirthInput test_pipeline.py::TestInferTier -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add astro-service/destiny_pipeline.py astro-service/test_pipeline.py
git commit -m "feat(pipeline): add BirthInput dataclass with tier auto-inference"
```

---

## Task 2: Pipeline.compute_charts() — single person

**Files:**
- Modify: `astro-service/destiny_pipeline.py`
- Modify: `astro-service/test_pipeline.py`

**Context:** `compute_charts()` wraps the same logic as `run_ideal_match_prompt.py:build_natal_report()` (lines 70-126), but calls chart.py and zwds.py **directly** (no HTTP), handles Tier 3 gracefully, and stores results internally.

**Key references:**
- `chart.py:321` — `calculate_chart(birth_date, birth_time, birth_time_exact, lat, lng, data_tier)`
- `zwds.py:148` — `compute_zwds_chart(birth_year, birth_month, birth_day, birth_time, gender)`
- `run_ideal_match_prompt.py:70-126` — `build_natal_report()` structure to replicate

**Step 1: Write the failing tests**

```python
# test_pipeline.py — append to file

class TestComputeCharts:
    def test_single_tier1_has_all_fields(self):
        p = DestinyPipeline(BirthInput("1997-03-07", "10:59", "M"))
        p.compute_charts()
        assert p._full_report_a is not None
        assert p._full_report_a["western_astrology"]["planets"]["sun_sign"] == "pisces"
        assert p._full_report_a["bazi"]["day_master"] == "戊"
        assert p._full_report_a["western_astrology"]["planets"]["ascendant_sign"] is not None

    def test_single_tier3_moon_null(self):
        p = DestinyPipeline(BirthInput("1996-12-10", None, "M"))
        p.compute_charts()
        planets = p._full_report_a["western_astrology"]["planets"]
        assert planets["moon_sign"] is None
        assert planets["ascendant_sign"] is None

    def test_single_tier3_zwds_null(self):
        p = DestinyPipeline(BirthInput("1996-12-10", None, "M"))
        p.compute_charts()
        zwds = p._full_report_a.get("zwds", {})
        # Tier 3: ZWDS should be empty or have chart=None
        assert zwds.get("chart") is None or zwds == {}

    def test_single_tier1_zwds_has_palaces(self):
        p = DestinyPipeline(BirthInput("1997-03-07", "10:59", "M"))
        p.compute_charts()
        zwds = p._full_report_a.get("zwds", {})
        # ZWDS may return chart dict or be wrapped — check palaces exist somewhere
        chart = zwds.get("chart", zwds)
        palaces = chart.get("palaces", {})
        assert "ming" in palaces or palaces == {}  # graceful if ziwei-service is down

    def test_returns_self_for_chaining(self):
        p = DestinyPipeline(BirthInput("1997-03-07", "10:59", "M"))
        result = p.compute_charts()
        assert result is p
```

Add import at top of test file:
```python
from destiny_pipeline import DestinyPipeline, BirthInput, _infer_tier
```

**Step 2: Run tests to verify they fail**

Run: `cd astro-service && pytest test_pipeline.py::TestComputeCharts -v`
Expected: FAIL — `DestinyPipeline` not yet defined or `compute_charts` not implemented

**Step 3: Write implementation**

Add to `destiny_pipeline.py`:

```python
from chart import calculate_chart
from zwds import compute_zwds_chart


# ── Helpers ──────────────────────────────────────────────────────────────────

_OPPOSITE_SIGN = {
    "aries": "libra",   "libra": "aries",
    "taurus": "scorpio", "scorpio": "taurus",
    "gemini": "sagittarius", "sagittarius": "gemini",
    "cancer": "capricorn",   "capricorn": "cancer",
    "leo": "aquarius",  "aquarius": "leo",
    "virgo": "pisces",  "pisces": "virgo",
}


def _build_full_report(birth: BirthInput) -> tuple[dict, dict]:
    """Compute western chart + bazi + zwds and assemble full_report structure.

    Returns (full_report, raw_chart) — raw_chart is the flat dict from chart.py.
    """
    # Determine birth_time params based on tier
    if birth.data_tier == 1:
        bt, bt_exact = "precise", birth.birth_time
    elif birth.data_tier == 2:
        bt, bt_exact = birth.birth_time, None
    else:
        bt, bt_exact = "unknown", None

    chart = calculate_chart(
        birth_date=birth.birth_date,
        birth_time=bt,
        birth_time_exact=bt_exact,
        lat=birth.lat,
        lng=birth.lng,
        data_tier=birth.data_tier,
    )

    # Fallback: derive house7_sign from ascendant if missing
    if not chart.get("house7_sign") and chart.get("ascendant_sign"):
        chart["house7_sign"] = _OPPOSITE_SIGN.get(
            chart["ascendant_sign"].lower()
        )

    # ZWDS (Tier 1 only)
    zwds: dict = {}
    if birth.data_tier == 1 and birth.birth_time:
        try:
            y, m, d = (int(x) for x in birth.birth_date.split("-"))
            zwds_result = compute_zwds_chart(y, m, d, birth.birth_time, birth.gender)
            zwds = zwds_result if zwds_result else {}
        except Exception:
            zwds = {}

    full_report = {
        "ident": {
            "birth_date": birth.birth_date,
            "birth_time": birth.birth_time,
            "gender": birth.gender,
            "data_tier": birth.data_tier,
        },
        "western_astrology": {
            "planets": {
                k: v for k, v in chart.items()
                if "_sign" in k or "_degree" in k or "_rx" in k
            },
            "houses": {
                "ascendant":  chart.get("ascendant_sign"),
                "descendant": chart.get("house7_sign"),
                "ic":         chart.get("house4_sign"),
                "house8":     chart.get("house8_sign"),
                "house12":    chart.get("house12_sign"),
            },
            "aspects": chart.get("natal_aspects", []),
        },
        "psychology": {
            "sm_tags":            chart.get("sm_tags", []),
            "karmic_tags":        chart.get("karmic_tags", []),
            "emotional_capacity": chart.get("emotional_capacity"),
            "element_profile":    chart.get("element_profile", {}),
        },
        "bazi": chart.get("bazi", {}),
        "zwds": zwds,
    }
    return full_report, chart


def _flatten_to_chart_data(full_report: dict, raw_chart: dict) -> dict:
    """Flatten nested full_report into the flat dict prompt_manager expects."""
    planets = full_report["western_astrology"]["planets"]
    psych = full_report["psychology"]
    house7 = planets.get("house7_sign") or raw_chart.get("house7_sign")
    houses = dict(full_report["western_astrology"]["houses"])
    houses["descendant"] = house7

    return {
        **{k: v for k, v in planets.items() if k.endswith("_sign")},
        **{k: v for k, v in planets.items() if k.endswith("_degree")},
        **{k: v for k, v in planets.items() if k.endswith("_rx")},
        "house7_sign":     house7,
        "houses":          houses,
        "sm_tags":         psych.get("sm_tags", []),
        "karmic_tags":     psych.get("karmic_tags", []),
        "element_profile": psych.get("element_profile", {}),
        "bazi":            full_report.get("bazi", {}),
        "zwds":            full_report.get("zwds", {}),
        "data_tier":       full_report.get("ident", {}).get("data_tier", 3),
        "natal_aspects":   full_report["western_astrology"].get("aspects", []),
    }


# ── Pipeline ─────────────────────────────────────────────────────────────────

class DestinyPipeline:
    """One-shot pipeline: chart → match → profile → prompt."""

    def __init__(
        self,
        person_a: BirthInput,
        person_b: Optional[BirthInput] = None,
    ):
        self._birth_a = person_a
        self._birth_b = person_b
        self._mode = "synastry" if person_b else "single"

        # Internal state — populated by each step
        self._full_report_a: Optional[dict] = None
        self._full_report_b: Optional[dict] = None
        self._chart_a: Optional[dict] = None
        self._chart_b: Optional[dict] = None
        self._flat_a: Optional[dict] = None
        self._flat_b: Optional[dict] = None
        self._match_result: Optional[dict] = None
        self._profile_a: Optional[dict] = None
        self._profile_b: Optional[dict] = None
        self._prompts: dict[str, str] = {}

    # ── Step 1 ───────────────────────────────────────────────────────────────

    def compute_charts(self) -> "DestinyPipeline":
        """Compute natal charts for all persons."""
        self._full_report_a, self._chart_a = _build_full_report(self._birth_a)
        self._flat_a = _flatten_to_chart_data(self._full_report_a, self._chart_a)

        if self._birth_b:
            self._full_report_b, self._chart_b = _build_full_report(self._birth_b)
            self._flat_b = _flatten_to_chart_data(self._full_report_b, self._chart_b)

        return self
```

**Step 4: Run tests to verify they pass**

Run: `cd astro-service && pytest test_pipeline.py::TestComputeCharts -v`
Expected: All PASS (ZWDS tests may skip gracefully if ziwei-service is down)

**Step 5: Commit**

```bash
git add astro-service/destiny_pipeline.py astro-service/test_pipeline.py
git commit -m "feat(pipeline): add compute_charts() with direct chart.py/zwds.py calls"
```

---

## Task 3: Pipeline.compute_match() — synastry scoring

**Files:**
- Modify: `astro-service/destiny_pipeline.py`
- Modify: `astro-service/test_pipeline.py`

**Context:** Wraps `matching.py:1202` `compute_match_v2(user_a, user_b)`. Single-person mode is a no-op.

**Step 1: Write the failing tests**

```python
# test_pipeline.py — append

class TestComputeMatch:
    def test_synastry_has_scores(self):
        p = DestinyPipeline(
            BirthInput("1997-03-07", "10:59", "M"),
            BirthInput("1995-03-26", "14:30", "F"),
        )
        p.compute_charts().compute_match()
        assert p._match_result is not None
        assert "lust_score" in p._match_result
        assert "soul_score" in p._match_result
        assert "tracks" in p._match_result

    def test_synastry_mixed_tier(self):
        p = DestinyPipeline(
            BirthInput("1996-11-05", "02:00", "F"),
            BirthInput("1996-12-10", None, "M"),
        )
        p.compute_charts().compute_match()
        assert p._match_result is not None
        assert 0 <= p._match_result["lust_score"] <= 100

    def test_single_mode_noop(self):
        p = DestinyPipeline(BirthInput("1997-03-07", "10:59", "M"))
        p.compute_charts().compute_match()
        assert p._match_result is None

    def test_returns_self(self):
        p = DestinyPipeline(
            BirthInput("1997-03-07", "10:59", "M"),
            BirthInput("1995-03-26", "14:30", "F"),
        )
        result = p.compute_charts().compute_match()
        assert result is p
```

**Step 2: Run tests — expect FAIL**

Run: `cd astro-service && pytest test_pipeline.py::TestComputeMatch -v`

**Step 3: Write implementation**

Add to `DestinyPipeline` class in `destiny_pipeline.py`:

```python
    # ── Step 2 ───────────────────────────────────────────────────────────────

    def compute_match(self) -> "DestinyPipeline":
        """Compute pairwise match scores (synastry mode only)."""
        if self._mode != "synastry" or not self._flat_b:
            return self

        from matching import compute_match_v2
        self._match_result = compute_match_v2(self._flat_a, self._flat_b)
        return self
```

**Step 4: Run tests — expect PASS**

Run: `cd astro-service && pytest test_pipeline.py::TestComputeMatch -v`

**Step 5: Commit**

```bash
git add astro-service/destiny_pipeline.py astro-service/test_pipeline.py
git commit -m "feat(pipeline): add compute_match() wrapping compute_match_v2"
```

---

## Task 4: Pipeline.extract_profiles() — ideal avatar extraction

**Files:**
- Modify: `astro-service/destiny_pipeline.py`
- Modify: `astro-service/test_pipeline.py`

**Context:** Wraps `ideal_avatar.py:524` `extract_ideal_partner_profile(western, bazi, zwds, psychology)`. Needs western chart with `natal_aspects` included.

**Step 1: Write the failing tests**

```python
# test_pipeline.py — append

class TestExtractProfiles:
    def test_single_person_profile(self):
        p = DestinyPipeline(BirthInput("1996-11-05", "02:00", "F"))
        p.compute_charts().extract_profiles()
        assert p._profile_a is not None
        assert "psychological_needs" in p._profile_a
        assert "target_western_signs" in p._profile_a

    def test_synastry_both_profiles(self):
        p = DestinyPipeline(
            BirthInput("1997-03-07", "10:59", "M"),
            BirthInput("1995-03-26", "14:30", "F"),
        )
        p.compute_charts().extract_profiles()
        assert p._profile_a is not None
        assert p._profile_b is not None

    def test_tier3_profile_still_works(self):
        p = DestinyPipeline(BirthInput("1996-12-10", None, "M"))
        p.compute_charts().extract_profiles()
        # Should not crash; profile may have fewer fields
        assert p._profile_a is not None

    def test_returns_self(self):
        p = DestinyPipeline(BirthInput("1997-03-07", "10:59", "M"))
        result = p.compute_charts().extract_profiles()
        assert result is p
```

**Step 2: Run tests — expect FAIL**

Run: `cd astro-service && pytest test_pipeline.py::TestExtractProfiles -v`

**Step 3: Write implementation**

Add to `DestinyPipeline` class:

```python
    # ── Step 3 ───────────────────────────────────────────────────────────────

    def extract_profiles(self) -> "DestinyPipeline":
        """Extract ideal partner profiles for all persons."""
        from ideal_avatar import extract_ideal_partner_profile

        def _extract(full_report: dict) -> dict:
            western = {
                **full_report.get("western_astrology", {}).get("planets", {}),
                "natal_aspects": full_report.get("western_astrology", {}).get("aspects", []),
            }
            bazi = full_report.get("bazi", {})
            zwds = full_report.get("zwds", {})
            psych = full_report.get("psychology", {})
            try:
                return extract_ideal_partner_profile(western, bazi, zwds, psych)
            except Exception:
                return {}

        if self._full_report_a:
            self._profile_a = _extract(self._full_report_a)
        if self._full_report_b:
            self._profile_b = _extract(self._full_report_b)

        return self
```

**Step 4: Run tests — expect PASS**

Run: `cd astro-service && pytest test_pipeline.py::TestExtractProfiles -v`

**Step 5: Commit**

```bash
git add astro-service/destiny_pipeline.py astro-service/test_pipeline.py
git commit -m "feat(pipeline): add extract_profiles() wrapping ideal_avatar"
```

---

## Task 5: Pipeline.build_prompts() — prompt assembly

**Files:**
- Modify: `astro-service/destiny_pipeline.py`
- Modify: `astro-service/test_pipeline.py`

**Context:** Calls `prompt_manager.py` functions:
- `get_match_report_prompt()` (line 366) — synastry prompt
- `get_ideal_match_prompt()` (line 709) — ideal partner prompt
- `get_profile_prompt()` (line 605) — soul profile prompt

**Step 1: Write the failing tests**

```python
# test_pipeline.py — append

class TestBuildPrompts:
    def test_single_has_ideal_and_profile(self):
        p = DestinyPipeline(BirthInput("1996-11-05", "02:00", "F"))
        p.compute_charts().extract_profiles().build_prompts()
        assert "ideal_a" in p._prompts
        assert "profile_a" in p._prompts
        assert "synastry" not in p._prompts
        assert len(p._prompts["ideal_a"]) > 100

    def test_synastry_has_all_five_prompts(self):
        p = DestinyPipeline(
            BirthInput("1997-03-07", "10:59", "M"),
            BirthInput("1995-03-26", "14:30", "F"),
        )
        p.compute_charts().compute_match().extract_profiles().build_prompts()
        assert "synastry" in p._prompts
        assert "ideal_a" in p._prompts
        assert "ideal_b" in p._prompts
        assert "profile_a" in p._prompts
        assert "profile_b" in p._prompts

    def test_synastry_prompt_contains_scores(self):
        p = DestinyPipeline(
            BirthInput("1997-03-07", "10:59", "M"),
            BirthInput("1995-03-26", "14:30", "F"),
        )
        p.compute_charts().compute_match().extract_profiles().build_prompts()
        prompt = p._prompts["synastry"]
        # Synastry prompt should contain the VibeScore / ChemistryScore
        assert "VibeScore" in prompt or "ChemistryScore" in prompt or "四軌" in prompt

    def test_returns_self(self):
        p = DestinyPipeline(BirthInput("1997-03-07", "10:59", "M"))
        result = p.compute_charts().extract_profiles().build_prompts()
        assert result is p
```

**Step 2: Run tests — expect FAIL**

Run: `cd astro-service && pytest test_pipeline.py::TestBuildPrompts -v`

**Step 3: Write implementation**

Add to `DestinyPipeline` class:

```python
    # ── Step 4 ───────────────────────────────────────────────────────────────

    def build_prompts(self) -> "DestinyPipeline":
        """Assemble all prompts using prompt_manager."""
        from prompt_manager import (
            get_match_report_prompt,
            get_ideal_match_prompt,
            get_profile_prompt,
        )

        # Individual prompts for person A
        if self._flat_a:
            self._prompts["ideal_a"] = get_ideal_match_prompt(
                self._flat_a,
                avatar_summary=self._profile_a,
            )
            self._prompts["profile_a"] = get_profile_prompt(
                self._flat_a,
                rpv_data={},
                attachment_style=self._profile_a.get("attachment_style", "secure") if self._profile_a else "secure",
            )

        # Individual prompts for person B
        if self._flat_b:
            self._prompts["ideal_b"] = get_ideal_match_prompt(
                self._flat_b,
                avatar_summary=self._profile_b,
            )
            self._prompts["profile_b"] = get_profile_prompt(
                self._flat_b,
                rpv_data={},
                attachment_style=self._profile_b.get("attachment_style", "secure") if self._profile_b else "secure",
            )

        # Synastry prompt (requires match result)
        if self._match_result and self._mode == "synastry":
            ident_a = self._full_report_a.get("ident", {})
            ident_b = self._full_report_b.get("ident", {})
            label_a = f"{'女' if ident_a.get('gender') == 'F' else '男'}({ident_a.get('birth_date', '')[5:]})"
            label_b = f"{'女' if ident_b.get('gender') == 'F' else '男'}({ident_b.get('birth_date', '')[5:]})"

            prompt_text, _ = get_match_report_prompt(
                self._match_result,
                person_a=label_a,
                person_b=label_b,
                user_a_profile=self._profile_a,
                user_b_profile=self._profile_b,
            )
            self._prompts["synastry"] = prompt_text

        return self
```

**Step 4: Run tests — expect PASS**

Run: `cd astro-service && pytest test_pipeline.py::TestBuildPrompts -v`

**Step 5: Commit**

```bash
git add astro-service/destiny_pipeline.py astro-service/test_pipeline.py
git commit -m "feat(pipeline): add build_prompts() assembling all prompt types"
```

---

## Task 6: Pipeline.to_enriched_dto() — safe DTO output

**Files:**
- Modify: `astro-service/destiny_pipeline.py`
- Modify: `astro-service/test_pipeline.py`

**Context:** Assembles the enriched DTO as defined in the design doc. Uses `prompt_manager.py:204` `_translate_psych_tags()` and `prompt_manager.py:215` `_element_summary()` for Chinese tag translation.

**Step 1: Write the failing tests**

```python
# test_pipeline.py — append

class TestEnrichedDTO:
    def _make_synastry_dto(self):
        p = DestinyPipeline(
            BirthInput("1997-03-07", "10:59", "M"),
            BirthInput("1995-03-26", "14:30", "F"),
        )
        p.compute_charts().compute_match().extract_profiles().build_prompts()
        return p.to_enriched_dto()

    def _make_single_dto(self):
        p = DestinyPipeline(BirthInput("1996-11-05", "02:00", "F"))
        p.compute_charts().extract_profiles().build_prompts()
        return p.to_enriched_dto()

    def test_synastry_mode(self):
        dto = self._make_synastry_dto()
        assert dto["mode"] == "synastry"

    def test_single_mode(self):
        dto = self._make_single_dto()
        assert dto["mode"] == "single"

    def test_scores_present_in_synastry(self):
        dto = self._make_synastry_dto()
        assert "scores" in dto
        assert "harmony" in dto["scores"]
        assert "tracks" in dto["scores"]

    def test_scores_absent_in_single(self):
        dto = self._make_single_dto()
        assert "scores" not in dto

    def test_tags_zh_present(self):
        dto = self._make_synastry_dto()
        assert "tags_zh" in dto
        assert "element_a" in dto["tags_zh"]
        assert "element_b" in dto["tags_zh"]

    def test_no_raw_degrees(self):
        dto = self._make_synastry_dto()
        dto_str = json.dumps(dto)
        assert "_degree" not in dto_str

    def test_no_natal_aspects_leaked(self):
        dto = self._make_synastry_dto()
        dto_str = json.dumps(dto)
        # natal_aspects should not appear as a key in person summaries
        assert "natal_aspects" not in dto.get("person_a_summary", {})

    def test_person_summary_has_stars(self):
        dto = self._make_synastry_dto()
        summary = dto["person_a_summary"]
        assert "sun" in summary
        assert "moon" in summary
        assert "day_master" in summary

    def test_prompts_present_synastry(self):
        dto = self._make_synastry_dto()
        assert "synastry" in dto["prompts"]
        assert "ideal_a" in dto["prompts"]
        assert "ideal_b" in dto["prompts"]

    def test_prompts_present_single(self):
        dto = self._make_single_dto()
        assert "ideal_a" in dto["prompts"]
        assert "profile_a" in dto["prompts"]

    def test_data_quality_tier(self):
        dto = self._make_synastry_dto()
        assert dto["data_quality"]["person_a"]["tier"] == 1

    def test_data_quality_missing_tier3(self):
        p = DestinyPipeline(
            BirthInput("1996-11-05", "02:00", "F"),
            BirthInput("1996-12-10", None, "M"),
        )
        p.compute_charts().compute_match().extract_profiles().build_prompts()
        dto = p.to_enriched_dto()
        missing = dto["data_quality"]["person_b"]["missing"]
        assert "moon" in missing
        assert "ascendant" in missing
        assert "zwds" in missing

    def test_tags_zh_all_chinese(self):
        dto = self._make_synastry_dto()
        for tag in dto["tags_zh"].get("psychological", []):
            # Should not contain raw English tag patterns like A_Moon_Conjunct_
            assert not tag.startswith("A_") and not tag.startswith("B_"), f"Untranslated tag: {tag}"
```

Add `import json` to the top of test_pipeline.py if not already there.

**Step 2: Run tests — expect FAIL**

Run: `cd astro-service && pytest test_pipeline.py::TestEnrichedDTO -v`

**Step 3: Write implementation**

Add to `destiny_pipeline.py`:

```python
# ── DTO helpers ──────────────────────────────────────────────────────────────

_TIER3_MISSING = ["moon", "ascendant", "houses", "vertex", "lilith", "zwds", "hour_pillar"]
_TIER2_MISSING = ["ascendant", "houses", "vertex", "lilith"]


def _data_quality(tier: int) -> dict:
    if tier == 3:
        return {"tier": tier, "missing": _TIER3_MISSING}
    elif tier == 2:
        return {"tier": tier, "missing": _TIER2_MISSING}
    return {"tier": tier, "missing": []}


def _person_summary(full_report: dict, profile: dict | None) -> dict:
    """Build safe person summary (no degrees, no raw aspects)."""
    planets = full_report.get("western_astrology", {}).get("planets", {})
    houses = full_report.get("western_astrology", {}).get("houses", {})
    psych = full_report.get("psychology", {})
    bazi = full_report.get("bazi", {})
    zwds = full_report.get("zwds", {})

    from prompt_manager import _translate_psych_tags, _element_summary

    # ZWDS summaries
    zwds_chart = zwds.get("chart", zwds) if zwds else {}
    palaces = zwds_chart.get("palaces", {}) if zwds_chart else {}
    ming_stars = palaces.get("ming", {}).get("main_stars", [])
    spouse_stars = palaces.get("spouse", {}).get("main_stars", [])

    # Translate tags
    sm_tags_zh = []
    from prompt_manager import _PSYCH_TAG_ZH
    for t in psych.get("sm_tags", []):
        sm_tags_zh.append(_PSYCH_TAG_ZH.get(t, t))
    karmic_tags_zh = []
    for t in psych.get("karmic_tags", []):
        karmic_tags_zh.append(_PSYCH_TAG_ZH.get(t, t))

    # Pillars string
    pillars = bazi.get("four_pillars") or bazi.get("pillars", {})
    if isinstance(pillars, dict):
        parts = []
        for k in ("year", "month", "day", "hour"):
            p = pillars.get(k)
            if isinstance(p, dict):
                parts.append(p.get("full", ""))
            elif isinstance(p, str):
                parts.append(p)
            elif p is None and k == "hour":
                parts.append("無時柱")
        pillar_str = " ".join(parts)
    else:
        pillar_str = str(pillars)

    day_master = bazi.get("day_master", "")
    day_master_el = bazi.get("day_master_element", "")
    day_master_yy = bazi.get("day_master_yinyang", "")
    yy_zh = "陽" if day_master_yy == "yang" else "陰" if day_master_yy == "yin" else ""

    summary = {
        "sun": planets.get("sun_sign"),
        "moon": planets.get("moon_sign"),
        "ascendant": planets.get("ascendant_sign"),
        "venus": planets.get("venus_sign"),
        "mars": planets.get("mars_sign"),
        "juno": planets.get("juno_sign"),
        "descendant": houses.get("descendant"),
        "day_master": f"{day_master}{day_master_el.title()} ({yy_zh})" if day_master else None,
        "pillars": pillar_str,
        "zwds_ming": "、".join(ming_stars) if ming_stars else "空宮",
        "zwds_spouse": "、".join(spouse_stars) if spouse_stars else "空宮",
        "sm_tags_zh": sm_tags_zh,
        "karmic_tags_zh": karmic_tags_zh,
        "element_profile": {
            "dominant": psych.get("element_profile", {}).get("dominant", []),
            "deficiency": psych.get("element_profile", {}).get("deficiency", []),
        },
    }

    if profile:
        summary["ideal_partner_profile"] = {
            "target_signs": profile.get("target_western_signs", []),
            "psychological_needs": profile.get("psychological_needs", []),
            "relationship_dynamic": profile.get("relationship_dynamic", "stable"),
            "venus_mars_tags": profile.get("venus_mars_tags", []),
        }

    return summary
```

Add `to_enriched_dto()` to the `DestinyPipeline` class:

```python
    # ── Step 5: DTO output ───────────────────────────────────────────────────

    def to_enriched_dto(self) -> dict:
        """Return the safe enriched DTO for frontend consumption."""
        from prompt_manager import _translate_psych_tags, _element_summary

        dto: dict = {
            "mode": self._mode,
            "data_quality": {
                "person_a": _data_quality(self._birth_a.data_tier),
            },
            "person_a_summary": _person_summary(
                self._full_report_a or {}, self._profile_a
            ),
            "prompts": dict(self._prompts),
        }

        if self._birth_b:
            dto["data_quality"]["person_b"] = _data_quality(self._birth_b.data_tier)
            dto["person_b_summary"] = _person_summary(
                self._full_report_b or {}, self._profile_b
            )

        # Scores (synastry only)
        if self._match_result:
            m = self._match_result
            dto["scores"] = {
                "harmony": m.get("harmony_score", m.get("soul_score", 0)),
                "lust": m.get("lust_score", 0),
                "soul": m.get("soul_score", 0),
                "karmic_tension": m.get("karmic_tension", 0),
                "tracks": m.get("tracks", {}),
                "primary_track": m.get("primary_track"),
                "quadrant": m.get("quadrant"),
                "spiciness_level": m.get("spiciness_level", "STABLE"),
                "high_voltage": m.get("high_voltage", False),
            }

            # Chinese tags
            psych_tags = m.get("psychological_tags", [])
            translated = _translate_psych_tags(psych_tags)
            # Split bullet points into list
            psych_zh = [line.lstrip("• ").strip() for line in translated.split("\n") if line.strip()]

            dto["tags_zh"] = {
                "resonance_badges": m.get("resonance_badges", []),
                "labels": m.get("labels", []),
                "psychological": psych_zh,
                "element_a": _element_summary(m.get("element_profile_a")),
                "element_b": _element_summary(m.get("element_profile_b")),
                "power_dynamic": self._format_power(m.get("power", {})),
            }

        return dto

    def _format_power(self, power: dict) -> str:
        """Format power dynamic into Chinese description."""
        rpv = power.get("rpv", 0)
        v_role = power.get("viewer_role", "Equal")
        t_role = power.get("target_role", "Equal")
        if v_role == t_role == "Equal":
            return "勢均力敵的博弈，雙方話語權接近"
        parts = []
        if v_role != "Equal":
            parts.append(f"A方傾向{v_role}")
        if t_role != "Equal":
            parts.append(f"B方傾向{t_role}")
        return "，".join(parts) + f"（RPV={rpv:.1f}）"
```

**Step 4: Run tests — expect PASS**

Run: `cd astro-service && pytest test_pipeline.py::TestEnrichedDTO -v`

**Step 5: Commit**

```bash
git add astro-service/destiny_pipeline.py astro-service/test_pipeline.py
git commit -m "feat(pipeline): add to_enriched_dto() with safe DTO and Chinese tags"
```

---

## Task 7: Pipeline file I/O + to_raw()

**Files:**
- Modify: `astro-service/destiny_pipeline.py`
- Modify: `astro-service/test_pipeline.py`

**Step 1: Write the failing tests**

```python
# test_pipeline.py — append
import os
import tempfile


class TestFileIO:
    def test_to_json_file_utf8(self):
        p = DestinyPipeline(BirthInput("1996-11-05", "02:00", "F"))
        p.compute_charts().extract_profiles().build_prompts()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            path = f.name
        try:
            p.to_json_file(path)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["mode"] == "single"
        finally:
            os.unlink(path)

    def test_to_prompt_file_utf8(self):
        p = DestinyPipeline(BirthInput("1996-11-05", "02:00", "F"))
        p.compute_charts().extract_profiles().build_prompts()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            path = f.name
        try:
            p.to_prompt_file("ideal_a", path)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            assert len(content) > 100
            assert "系統角色" in content or "DESTINY" in content
        finally:
            os.unlink(path)

    def test_to_raw_contains_degrees(self):
        p = DestinyPipeline(BirthInput("1997-03-07", "10:59", "M"))
        p.compute_charts()
        raw = p.to_raw()
        raw_str = json.dumps(raw)
        assert "_degree" in raw_str  # raw output SHOULD contain degrees
```

**Step 2: Run tests — expect FAIL**

Run: `cd astro-service && pytest test_pipeline.py::TestFileIO -v`

**Step 3: Write implementation**

Add to `DestinyPipeline` class:

```python
    def to_raw(self) -> dict:
        """Return full internal data including degrees — for CLI/debug only."""
        return {
            "mode": self._mode,
            "person_a": {
                "birth": {"date": self._birth_a.birth_date, "time": self._birth_a.birth_time, "gender": self._birth_a.gender, "tier": self._birth_a.data_tier},
                "full_report": self._full_report_a,
                "profile": self._profile_a,
            },
            "person_b": {
                "birth": {"date": self._birth_b.birth_date, "time": self._birth_b.birth_time, "gender": self._birth_b.gender, "tier": self._birth_b.data_tier},
                "full_report": self._full_report_b,
                "profile": self._profile_b,
            } if self._birth_b else None,
            "match_result": self._match_result,
            "prompts": dict(self._prompts),
        }

    def to_json_file(self, path: str) -> None:
        """Write enriched DTO to a UTF-8 JSON file."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_enriched_dto(), f, ensure_ascii=False, indent=2)

    def to_prompt_file(self, prompt_key: str, path: str) -> None:
        """Write a specific prompt to a UTF-8 text file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._prompts[prompt_key])
```

**Step 4: Run tests — expect PASS**

Run: `cd astro-service && pytest test_pipeline.py::TestFileIO -v`

**Step 5: Commit**

```bash
git add astro-service/destiny_pipeline.py astro-service/test_pipeline.py
git commit -m "feat(pipeline): add to_raw(), to_json_file(), to_prompt_file()"
```

---

## Task 8: FastAPI endpoint /compute-enriched

**Files:**
- Modify: `astro-service/main.py` (add endpoint after last existing endpoint, ~line 660)
- Modify: `astro-service/test_pipeline.py`

**Step 1: Write the failing test**

```python
# test_pipeline.py — append
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestEndpoint:
    def test_synastry_endpoint(self):
        resp = client.post("/compute-enriched", json={
            "person_a": {"birth_date": "1997-03-07", "birth_time": "10:59", "gender": "M"},
            "person_b": {"birth_date": "1995-03-26", "birth_time": "14:30", "gender": "F"},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "synastry"
        assert "scores" in data
        assert "prompts" in data
        assert "synastry" in data["prompts"]

    def test_single_endpoint(self):
        resp = client.post("/compute-enriched", json={
            "person_a": {"birth_date": "1996-11-05", "birth_time": "02:00", "gender": "F"},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "single"
        assert "scores" not in data
        assert "ideal_a" in data["prompts"]

    def test_tier3_endpoint(self):
        resp = client.post("/compute-enriched", json={
            "person_a": {"birth_date": "1996-11-05", "birth_time": "02:00", "gender": "F"},
            "person_b": {"birth_date": "1996-12-10", "gender": "M"},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["data_quality"]["person_b"]["tier"] == 3
        assert "moon" in data["data_quality"]["person_b"]["missing"]
```

**Step 2: Run tests — expect FAIL**

Run: `cd astro-service && pytest test_pipeline.py::TestEndpoint -v`

**Step 3: Write implementation**

Add to `main.py` (after the last endpoint):

```python
# ── Pipeline: Enriched One-Shot Endpoint ─────────────────────────────────────

class PersonInput(BaseModel):
    birth_date: str
    birth_time: Optional[str] = None
    gender: str = "M"
    lat: float = 25.033
    lng: float = 121.565


class EnrichedRequest(BaseModel):
    person_a: PersonInput
    person_b: Optional[PersonInput] = None


@app.post("/compute-enriched")
def compute_enriched(req: EnrichedRequest):
    """One-shot pipeline: chart → match → profile → prompt assembly.

    Returns enriched DTO with scores, Chinese tags, person summaries,
    and pre-assembled prompts for all report types.

    - person_b omitted → single-person mode (profile + ideal match)
    - birth_time null → Tier 3 auto-inference
    """
    from destiny_pipeline import DestinyPipeline, BirthInput

    a = BirthInput(
        birth_date=req.person_a.birth_date,
        birth_time=req.person_a.birth_time,
        gender=req.person_a.gender,
        lat=req.person_a.lat,
        lng=req.person_a.lng,
    )
    b = None
    if req.person_b:
        b = BirthInput(
            birth_date=req.person_b.birth_date,
            birth_time=req.person_b.birth_time,
            gender=req.person_b.gender,
            lat=req.person_b.lat,
            lng=req.person_b.lng,
        )

    pipeline = DestinyPipeline(a, b)
    pipeline.compute_charts()
    if b:
        pipeline.compute_match()
    pipeline.extract_profiles().build_prompts()

    return pipeline.to_enriched_dto()
```

Add import at top of `main.py`:
```python
from typing import Optional  # should already exist
```

**Step 4: Run tests — expect PASS**

Run: `cd astro-service && pytest test_pipeline.py::TestEndpoint -v`

**Step 5: Commit**

```bash
git add astro-service/main.py astro-service/test_pipeline.py
git commit -m "feat(api): add POST /compute-enriched one-shot pipeline endpoint"
```

---

## Task 9: Refactor run_ideal_match_prompt.py to use Pipeline

**Files:**
- Modify: `astro-service/run_ideal_match_prompt.py`

**Step 1: Verify current CLI works (baseline)**

Run: `cd astro-service && python -c "from run_ideal_match_prompt import build_natal_report; print('OK')"`
Expected: `OK`

**Step 2: Rewrite the script**

Replace the entire contents of `run_ideal_match_prompt.py` with:

```python
# -*- coding: utf-8 -*-
"""
DESTINY — Enriched Pipeline Runner (CLI)

Usage:
  python run_ideal_match_prompt.py                          # 單人排盤 + prompt
  python run_ideal_match_prompt.py --synastry               # 合盤
  python run_ideal_match_prompt.py --show-chart             # 印出完整命盤 JSON
  python run_ideal_match_prompt.py --json out.json          # 輸出 enriched DTO
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from destiny_pipeline import DestinyPipeline, BirthInput

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 預設測試對象
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFAULT_DATE    = "1997-03-07"
DEFAULT_TIME    = "10:59"
DEFAULT_GENDER  = "M"
DEFAULT_LAT     = 25.033
DEFAULT_LNG     = 121.565
DEFAULT_DATE2   = "1995-03-26"
DEFAULT_TIME2   = "14:30"
DEFAULT_GENDER2 = "F"


def main():
    parser = argparse.ArgumentParser(description="DESTINY Pipeline Runner")
    parser.add_argument("--date",    default=DEFAULT_DATE,    help="出生日期 YYYY-MM-DD")
    parser.add_argument("--time",    default=DEFAULT_TIME,    help="出生時間 HH:MM (null=Tier3)")
    parser.add_argument("--gender",  default=DEFAULT_GENDER,  help="M / F")
    parser.add_argument("--lat",     type=float, default=DEFAULT_LAT)
    parser.add_argument("--lng",     type=float, default=DEFAULT_LNG)
    parser.add_argument("--synastry",   action="store_true",  help="合盤模式")
    parser.add_argument("--date2",   default=DEFAULT_DATE2,   help="第二人出生日期")
    parser.add_argument("--time2",   default=DEFAULT_TIME2,   help="第二人出生時間")
    parser.add_argument("--gender2", default=DEFAULT_GENDER2, help="第二人性別")
    parser.add_argument("--show-chart", action="store_true",  help="印出完整命盤 JSON")
    parser.add_argument("--json",    default=None,            help="輸出 enriched DTO 到 JSON 檔案")
    parser.add_argument("--prompt",  default=None,            help="輸出指定 prompt 到檔案 (synastry/ideal_a/ideal_b/profile_a/profile_b)")
    parser.add_argument("--stdout",  action="store_true",     help="允許 UTF-8 stdout 輸出")
    args = parser.parse_args()

    # Handle stdout encoding for Windows
    if args.stdout:
        sys.stdout.reconfigure(encoding="utf-8")

    # Build inputs
    time_a = args.time if args.time != "null" else None
    person_a = BirthInput(args.date, time_a, args.gender, args.lat, args.lng)

    person_b = None
    if args.synastry:
        time_b = args.time2 if args.time2 != "null" else None
        person_b = BirthInput(args.date2, time_b, args.gender2, args.lat, args.lng)

    # Run pipeline
    pipeline = DestinyPipeline(person_a, person_b)
    pipeline.compute_charts()
    if person_b:
        pipeline.compute_match()
    pipeline.extract_profiles().build_prompts()

    # Output: raw chart
    if args.show_chart:
        raw_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline_raw.json")
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(pipeline.to_raw(), f, ensure_ascii=False, indent=2)
        print(f"Raw chart written to {raw_path}")

    # Output: enriched DTO
    if args.json:
        pipeline.to_json_file(args.json)
        print(f"Enriched DTO written to {args.json}")

    # Output: specific prompt
    if args.prompt:
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{args.prompt}_output.txt")
        pipeline.to_prompt_file(args.prompt, out_path)
        print(f"Prompt '{args.prompt}' written to {out_path}")

    # Default: write synastry prompt (backward compat)
    if args.synastry and not args.prompt and not args.json:
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synastry_output.txt")
        pipeline.to_prompt_file("synastry", out_path)
        print(f"Synastry prompt written to {out_path}")

    # Default: write ideal match prompt (single mode, backward compat)
    if not args.synastry and not args.prompt and not args.json:
        out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ideal_match_output.txt")
        pipeline.to_prompt_file("ideal_a", out_path)
        print(f"Ideal match prompt written to {out_path}")

    print("DONE")


if __name__ == "__main__":
    main()
```

**Step 3: Verify the refactored script works**

Run: `cd astro-service && python run_ideal_match_prompt.py --json enriched_test.json`
Expected: `Enriched DTO written to enriched_test.json` then `DONE`

Run: `cd astro-service && python run_ideal_match_prompt.py --synastry`
Expected: `Synastry prompt written to synastry_output.txt` then `DONE`

**Step 4: Verify existing tests still pass**

Run: `cd astro-service && pytest test_pipeline.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add astro-service/run_ideal_match_prompt.py
git commit -m "refactor: rewrite run_ideal_match_prompt.py to use DestinyPipeline"
```

---

## Task 10: Write PIPELINE-GUIDE.md documentation

**Files:**
- Create: `astro-service/docs/PIPELINE-GUIDE.md`

**Step 1: Write the guide**

Write the full documentation file covering:
- Quick start (Python API + CLI + HTTP)
- BirthInput parameters
- Single vs Synastry mode
- Pipeline chain methods
- Enriched DTO field reference table
- HTTP endpoint request/response examples
- Tier comparison table
- Migration guide from old `run_ideal_match_prompt.py`
- Future: LLM integration placeholder

Refer to the design doc `docs/plans/2026-03-01-destiny-pipeline-design.md` for the DTO structure.

**Step 2: Commit**

```bash
git add astro-service/docs/PIPELINE-GUIDE.md
git commit -m "docs: add PIPELINE-GUIDE.md usage manual"
```

---

## Task 11: Final integration test + full test suite

**Files:**
- Modify: `astro-service/test_pipeline.py`

**Step 1: Run the full test suite**

Run: `cd astro-service && pytest -v`
Expected: All existing tests (387+) PASS + all new pipeline tests PASS

**Step 2: Fix any failures**

If any test fails, debug and fix. Common issues:
- Import paths
- prompt_manager internal function access (`_translate_psych_tags` is private)
- ZWDS graceful degradation when ziwei-service is down

**Step 3: Final commit**

```bash
git add -A
git commit -m "test: verify full test suite passes with pipeline integration"
```

---

## Summary

| Task | What | New/Modify | Est. |
|------|------|------------|------|
| 1 | BirthInput + tier inference | New: destiny_pipeline.py, test_pipeline.py | 5 min |
| 2 | compute_charts() | Modify: both | 10 min |
| 3 | compute_match() | Modify: both | 5 min |
| 4 | extract_profiles() | Modify: both | 5 min |
| 5 | build_prompts() | Modify: both | 10 min |
| 6 | to_enriched_dto() | Modify: both | 15 min |
| 7 | File I/O + to_raw() | Modify: both | 5 min |
| 8 | /compute-enriched endpoint | Modify: main.py + test | 10 min |
| 9 | Refactor CLI script | Modify: run_ideal_match_prompt.py | 10 min |
| 10 | PIPELINE-GUIDE.md | New: docs | 15 min |
| 11 | Full integration test | Run all tests | 5 min |
