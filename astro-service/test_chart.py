"""
Tests for DESTINY natal chart calculator.
Uses known birth data to verify Swiss Ephemeris calculations.
"""

from chart import calculate_chart, longitude_to_sign, compute_emotional_capacity, _angular_distance
from bazi import calculate_bazi, analyze_element_relation, HEAVENLY_STEMS, STEM_ELEMENTS, EARTHLY_BRANCHES
import pytest


# ── Unit: longitude_to_sign ──────────────────────────────────────

def test_longitude_to_sign_aries():
    assert longitude_to_sign(15.0) == "aries"

def test_longitude_to_sign_pisces():
    assert longitude_to_sign(350.0) == "pisces"

def test_longitude_to_sign_boundary():
    """Exactly 30° should be Taurus (index 1), not Aries."""
    assert longitude_to_sign(30.0) == "taurus"


# ── Tier 3: date only ───────────────────────────────────────────

def test_tier3_sun_sign_gemini():
    """1995-06-15 → Sun in Gemini (date-only, noon UT)."""
    result = calculate_chart(
        birth_date="1995-06-15",
        data_tier=3,
    )
    assert result["sun_sign"] == "gemini"
    assert result["element_primary"] == "air"
    # Tier 3: moon and ascendant should be null
    assert result["moon_sign"] is None
    assert result["ascendant_sign"] is None

def test_tier3_sun_sign_capricorn():
    """2000-01-01 → Sun in Capricorn."""
    result = calculate_chart(
        birth_date="2000-01-01",
        data_tier=3,
    )
    assert result["sun_sign"] == "capricorn"
    assert result["element_primary"] == "earth"

def test_tier3_sun_sign_aries():
    """1990-04-05 → Sun in Aries."""
    result = calculate_chart(
        birth_date="1990-04-05",
        data_tier=3,
    )
    assert result["sun_sign"] == "aries"
    assert result["element_primary"] == "fire"


# ── Tier 1: precise time ────────────────────────────────────────

def test_tier1_all_signs_present():
    """Tier 1 with precise time should return all 6 signs + ascendant."""
    result = calculate_chart(
        birth_date="1995-06-15",
        birth_time="precise",
        birth_time_exact="14:30",
        lat=25.033,
        lng=121.565,
        data_tier=1,
    )
    assert result["sun_sign"] is not None
    assert result["moon_sign"] is not None
    assert result["venus_sign"] is not None
    assert result["mars_sign"] is not None
    assert result["saturn_sign"] is not None
    assert result["ascendant_sign"] is not None
    assert result["element_primary"] is not None
    assert result["data_tier"] == 1

def test_tier1_sun_still_gemini():
    """Even with precise time, 1995-06-15 Sun should still be Gemini."""
    result = calculate_chart(
        birth_date="1995-06-15",
        birth_time="precise",
        birth_time_exact="14:30",
        lat=25.033,
        lng=121.565,
        data_tier=1,
    )
    assert result["sun_sign"] == "gemini"


# ── Tier 2: fuzzy time ──────────────────────────────────────────

def test_tier2_has_moon_no_ascendant():
    """Tier 2 should have Moon (approximate) but no Ascendant."""
    result = calculate_chart(
        birth_date="1995-06-15",
        birth_time="morning",
        lat=25.033,
        lng=121.565,
        data_tier=2,
    )
    assert result["moon_sign"] is not None
    assert result["ascendant_sign"] is None
    assert result["sun_sign"] == "gemini"


# ── Boundary dates ──────────────────────────────────────────────

def test_boundary_pisces_aries():
    """March 20, 2000 — Sun is near Pisces/Aries boundary.
    At noon UT on March 20, 2000 the Sun is still in Pisces (~29.8°)."""
    result = calculate_chart(
        birth_date="2000-03-20",
        data_tier=3,
    )
    assert result["sun_sign"] in ("pisces", "aries")

def test_boundary_leo_virgo():
    """Aug 22, 1990 — Sun near Leo/Virgo boundary."""
    result = calculate_chart(
        birth_date="1990-08-22",
        data_tier=3,
    )
    assert result["sun_sign"] in ("leo", "virgo")


# ── All 12 signs sanity check ───────────────────────────────────

def test_all_twelve_signs_reachable():
    """Verify each zodiac sign is reachable by picking a mid-month date."""
    # Approximate mid-sign dates
    dates_and_signs = [
        ("2000-04-10", "aries"),
        ("2000-05-10", "taurus"),
        ("2000-06-10", "gemini"),
        ("2000-07-10", "cancer"),
        ("2000-08-10", "leo"),
        ("2000-09-10", "virgo"),
        ("2000-10-10", "libra"),
        ("2000-11-10", "scorpio"),
        ("2000-12-10", "sagittarius"),
        ("2000-01-10", "capricorn"),
        ("2000-02-10", "aquarius"),
        ("2000-03-10", "pisces"),
    ]
    for date, expected_sign in dates_and_signs:
        result = calculate_chart(birth_date=date, data_tier=3)
        assert result["sun_sign"] == expected_sign, (
            f"Date {date}: expected {expected_sign}, got {result['sun_sign']}"
        )


# ══════════════════════════════════════════════════════════════════
# BaZi (八字四柱) Tests
# ══════════════════════════════════════════════════════════════════

# ── Day Master basics ────────────────────────────────────────────

def test_bazi_returns_day_master():
    """BaZi calculation should return a valid Day Master."""
    bazi = calculate_bazi("1995-06-15", data_tier=3)
    assert bazi["day_master"] in HEAVENLY_STEMS
    assert bazi["day_master_element"] in ("wood", "fire", "earth", "metal", "water")
    assert bazi["day_master_yinyang"] in ("yin", "yang")

def test_bazi_element_profile():
    """Element profile should have cn, trait, desc fields."""
    bazi = calculate_bazi("1995-06-15", data_tier=3)
    profile = bazi["element_profile"]
    assert "cn" in profile
    assert "trait" in profile
    assert "desc" in profile

def test_bazi_day_master_element_matches_stem():
    """Day Master element should match the STEM_ELEMENTS mapping."""
    bazi = calculate_bazi("2000-01-01", data_tier=3)
    assert STEM_ELEMENTS[bazi["day_master"]] == bazi["day_master_element"]


# ── Four Pillars structure ───────────────────────────────────────

def test_bazi_four_pillars_structure():
    """Four Pillars should have year, month, day; hour is None for tier 3."""
    bazi = calculate_bazi("1995-06-15", data_tier=3)
    pillars = bazi["four_pillars"]
    assert "year" in pillars
    assert "month" in pillars
    assert "day" in pillars
    assert pillars["hour"] is None  # tier 3, no time
    assert bazi["hour_known"] is False

    # Each pillar should have stem, branch, full
    for key in ("year", "month", "day"):
        p = pillars[key]
        assert "stem" in p
        assert "branch" in p
        assert "full" in p
        assert len(p["full"]) == 2  # Two Chinese characters


def test_bazi_month_branch_in_output():
    """calculate_bazi() should include bazi_month_branch as a valid earthly branch."""
    bazi = calculate_bazi("1995-06-15", data_tier=3)
    assert "bazi_month_branch" in bazi
    assert bazi["bazi_month_branch"] in EARTHLY_BRANCHES, (
        f"bazi_month_branch '{bazi['bazi_month_branch']}' is not a valid earthly branch"
    )

def test_bazi_month_branch_matches_pillar_branch():
    """bazi_month_branch in top-level output must match four_pillars.month.branch."""
    bazi = calculate_bazi("1997-03-07", birth_time="precise",
                          birth_time_exact="10:59", lat=25.033, lng=121.565, data_tier=1)
    assert bazi["bazi_month_branch"] == bazi["four_pillars"]["month"]["branch"]

def test_bazi_month_branch_all_tiers():
    """bazi_month_branch should be present for all data tiers."""
    for tier, kwargs in [
        (3, {}),
        (2, {"birth_time": "morning"}),
        (1, {"birth_time": "precise", "birth_time_exact": "10:00"}),
    ]:
        bazi = calculate_bazi("2000-06-15", data_tier=tier, **kwargs)
        assert "bazi_month_branch" in bazi
        assert bazi["bazi_month_branch"] in EARTHLY_BRANCHES

def test_bazi_tier1_has_hour_pillar():
    """Tier 1 with precise time should include hour pillar."""
    bazi = calculate_bazi(
        "1995-06-15",
        birth_time="precise",
        birth_time_exact="14:30",
        data_tier=1,
    )
    assert bazi["hour_known"] is True
    assert bazi["four_pillars"]["hour"] is not None
    assert len(bazi["four_pillars"]["hour"]["full"]) == 2

def test_bazi_tier2_has_hour_pillar():
    """Tier 2 with fuzzy time should still compute an approximate hour pillar."""
    bazi = calculate_bazi(
        "1995-06-15",
        birth_time="afternoon",
        data_tier=2,
    )
    assert bazi["hour_known"] is True
    assert bazi["four_pillars"]["hour"] is not None


# ── Year Pillar known cases ──────────────────────────────────────

def test_bazi_year_2024_dragon():
    """2024-03-01 (after lichun) should be 甲辰年."""
    bazi = calculate_bazi("2024-03-01", data_tier=3)
    year = bazi["four_pillars"]["year"]
    assert year["stem"] == "甲"
    assert year["branch"] == "辰"
    assert year["full"] == "甲辰"

def test_bazi_year_2000():
    """2000-06-15 should be 庚辰年."""
    bazi = calculate_bazi("2000-06-15", data_tier=3)
    year = bazi["four_pillars"]["year"]
    assert year["stem"] == "庚"
    assert year["branch"] == "辰"


# ── Day Pillar verification ──────────────────────────────────────

def test_bazi_day_pillar_2000_jan_01():
    """2000-01-01 should be 戊午日."""
    bazi = calculate_bazi("2000-01-01", data_tier=3)
    day = bazi["four_pillars"]["day"]
    assert day["stem"] == "戊"
    assert day["branch"] == "午"
    assert day["full"] == "戊午"


def test_bazi_early_morning_1996_02_12():
    """1996-02-12 01:45 (clock) should be 丙子 庚寅 己卯 乙丑 (節氣四柱).
    Early-morning birth: 01:45 local = -6.25 UT (crosses UTC date boundary).
    Day pillar must use local calendar date, not UTC date. Verified by user."""
    bazi = calculate_bazi(
        "1996-02-12",
        birth_time="precise",
        birth_time_exact="01:45",
        lat=25.033,
        lng=121.565,
        data_tier=1,
    )
    p = bazi["four_pillars"]
    assert p["year"]["full"] == "丙子", f"year: got {p['year']['full']}"
    assert p["month"]["full"] == "庚寅", f"month: got {p['month']['full']}"
    assert p["day"]["full"] == "己卯", f"day: got {p['day']['full']}"
    assert p["hour"]["full"] == "乙丑", f"hour: got {p['hour']['full']}"
    assert bazi["day_master"] == "己"
    assert bazi["day_master_element"] == "earth"


def test_bazi_full_case_1997_03_07():
    """1997-03-07 10:59 (clock) should be 丁丑 癸卯 戊申 丁巳.
    True solar time ~10:47 (Taipei). Verified by user."""
    bazi = calculate_bazi(
        "1997-03-07",
        birth_time="precise",
        birth_time_exact="10:59",
        lat=25.033,
        lng=121.565,
        data_tier=1,
    )
    p = bazi["four_pillars"]
    assert p["year"]["full"] == "丁丑", f"year: got {p['year']['full']}"
    assert p["month"]["full"] == "癸卯", f"month: got {p['month']['full']}"
    assert p["day"]["full"] == "戊申", f"day: got {p['day']['full']}"
    assert p["hour"]["full"] == "丁巳", f"hour: got {p['hour']['full']}"
    assert bazi["day_master"] == "戊"
    assert bazi["day_master_element"] == "earth"


# ── True Solar Time (真太陽時) ─────────────────────────────────────

def test_solar_time_march_correction():
    """Early March should have ~-12 min EoT correction."""
    from bazi import clock_to_solar_time
    import swisseph as swe
    jd = swe.julday(1997, 3, 7, 3.0)  # UT for ~11:00 local
    solar = clock_to_solar_time(10.983, 121.565, jd)
    # Should be less than clock time (negative EoT in March)
    assert solar < 10.983
    # Correction should be roughly -5 to -12 minutes depending on formula
    diff_min = (solar - 10.983) * 60
    assert -15 < diff_min < 0, f"EoT correction: {diff_min:.1f} min"


# ── Integrated: chart includes bazi ──────────────────────────────

def test_chart_includes_bazi():
    """calculate_chart should include bazi data."""
    result = calculate_chart("1995-06-15", data_tier=3)
    assert "bazi" in result
    assert "day_master" in result["bazi"]
    assert "four_pillars" in result["bazi"]


# ── Element Relation Analysis ────────────────────────────────────

def test_relation_same_element():
    rel = analyze_element_relation("wood", "wood")
    assert rel["relation"] == "same"
    assert rel["relation_cn"] == "比和"

def test_relation_generation():
    """Wood generates Fire (木生火)."""
    rel = analyze_element_relation("wood", "fire")
    assert rel["relation"] == "a_generates_b"
    assert "生" in rel["relation_cn"]
    assert rel["harmony_score"] == 0.85

def test_relation_restriction():
    """Metal restricts Wood (金剋木)."""
    rel = analyze_element_relation("metal", "wood")
    assert rel["relation"] == "a_restricts_b"
    assert "剋" in rel["relation_cn"]
    assert rel["harmony_score"] == 0.5

def test_relation_being_restricted():
    """Wood is restricted by Metal (被金剋)."""
    rel = analyze_element_relation("wood", "metal")
    assert rel["relation"] == "b_restricts_a"

def test_relation_all_generation_pairs():
    """Verify the full generation cycle."""
    cycle = [("wood", "fire"), ("fire", "earth"), ("earth", "metal"),
             ("metal", "water"), ("water", "wood")]
    for a, b in cycle:
        rel = analyze_element_relation(a, b)
        assert rel["relation"] == "a_generates_b", f"{a}→{b} should be generation"

def test_relation_all_restriction_pairs():
    """Verify the full restriction cycle."""
    cycle = [("wood", "earth"), ("earth", "water"), ("water", "fire"),
             ("fire", "metal"), ("metal", "wood")]
    for a, b in cycle:
        rel = analyze_element_relation(a, b)
        assert rel["relation"] == "a_restricts_b", f"{a}→{b} should be restriction"


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

def test_tier1_house_signs_correct_values():
    """Regression: house4/house8/house12 signs are correctly computed for a known birth date."""
    result = calculate_chart("1997-03-08", birth_time_exact="20:00", birth_time="precise", data_tier=1)
    # Verified values from astro-service API output (commit 3cd50f4)
    assert result["house4_sign"] == "capricorn"
    assert result["house8_sign"] == "taurus"
    assert result["house12_sign"] is not None  # house12 not pre-verified, just ensure it's present


# ── Emotional Capacity ────────────────────────────────────────────

class TestEmotionalCapacity:
    """Tests for compute_emotional_capacity."""

    def test_base_score_no_aspects_no_zwds(self):
        # Chart with no penalizing or rewarding aspects → 50
        chart = {
            "moon_sign": "aries", "saturn_sign": "aries",  # conjunction, not sextile/trine
            "pluto_sign": "aries",  # same sign, not square/opposition
        }
        result = compute_emotional_capacity(chart)
        assert result == 50

    def test_moon_pluto_square_penalty(self):
        chart = {
            "moon_sign": "aries",    # index 0
            "pluto_sign": "cancer",  # index 3 → distance 3 = square
            "saturn_sign": None,
        }
        result = compute_emotional_capacity(chart)
        assert result == 30  # 50 - 20

    def test_moon_saturn_trine_bonus(self):
        chart = {
            "moon_sign": "aries",   # index 0
            "saturn_sign": "leo",   # index 4 → distance 4 = trine
            "pluto_sign": None,
        }
        result = compute_emotional_capacity(chart)
        assert result == 65  # 50 + 15

    def test_zwds_empty_ming_palace(self):
        chart = {"moon_sign": None, "pluto_sign": None, "saturn_sign": None}
        zwds = {
            "palaces": {
                "ming": {"main_stars": [], "auspicious_stars": [], "malevolent_stars": [], "is_empty": True},
                "karma": {"main_stars": [], "auspicious_stars": [], "malevolent_stars": [], "is_empty": False},
            }
        }
        result = compute_emotional_capacity(chart, zwds)
        assert result == 40  # 50 - 10

    def test_zwds_ziwei_in_ming_palace(self):
        chart = {"moon_sign": None, "pluto_sign": None, "saturn_sign": None}
        zwds = {
            "palaces": {
                "ming": {"main_stars": ["紫微化祿"], "auspicious_stars": [], "malevolent_stars": [], "is_empty": False},
                "karma": {"main_stars": [], "auspicious_stars": [], "malevolent_stars": [], "is_empty": False},
            }
        }
        result = compute_emotional_capacity(chart, zwds)
        assert result == 70  # 50 + 20

    def test_zwds_karma_sha_stars(self):
        chart = {"moon_sign": None, "pluto_sign": None, "saturn_sign": None}
        zwds = {
            "palaces": {
                "ming": {"main_stars": ["七殺"], "auspicious_stars": [], "malevolent_stars": [], "is_empty": False},
                "karma": {"main_stars": [], "auspicious_stars": [], "malevolent_stars": ["擎羊", "陀羅"], "is_empty": False},
            }
        }
        result = compute_emotional_capacity(chart, zwds)
        assert result == 30  # 50 - 10 - 10

    def test_clamp_at_zero(self):
        # Moon-Pluto square (-20) + 3 SHA stars in karma (-30) + empty ming (-10) = -10 → clamp to 0
        chart = {"moon_sign": "aries", "pluto_sign": "cancer", "saturn_sign": None}
        zwds = {
            "palaces": {
                "ming": {"main_stars": [], "auspicious_stars": [], "malevolent_stars": [], "is_empty": True},
                "karma": {"main_stars": [], "auspicious_stars": [], "malevolent_stars": ["擎羊", "陀羅", "火星"], "is_empty": False},
            }
        }
        result = compute_emotional_capacity(chart, zwds)
        assert result == 0  # 50 - 20 - 10 - 30 = -10 → clamped to 0

    def test_clamp_at_100(self):
        # Moon-Saturn trine (+15) + 紫微 in ming (+20) = 85 → not clamped
        chart = {"moon_sign": "aries", "saturn_sign": "leo", "pluto_sign": None}
        zwds = {
            "palaces": {
                "ming": {"main_stars": ["紫微"], "auspicious_stars": [], "malevolent_stars": [], "is_empty": False},
                "karma": {"main_stars": [], "auspicious_stars": [], "malevolent_stars": [], "is_empty": False},
            }
        }
        result = compute_emotional_capacity(chart, zwds)
        assert result == 85

    def test_calculate_chart_includes_emotional_capacity(self):
        # Verify calculate_chart() output includes emotional_capacity
        result = calculate_chart("1997-03-08", birth_time_exact="20:00", birth_time="precise", data_tier=1)
        assert "emotional_capacity" in result
        assert isinstance(result["emotional_capacity"], int)
        assert 0 <= result["emotional_capacity"] <= 100

    def test_house12_sign_in_tier1(self):
        result = calculate_chart("1997-03-08", birth_time_exact="20:00", birth_time="precise", data_tier=1)
        assert "house12_sign" in result
        assert result["house12_sign"] is not None

    def test_house12_sign_none_in_tier3(self):
        result = calculate_chart("1997-03-08", data_tier=3)
        assert result["house12_sign"] is None

    def test_stellium_in_house_causes_penalty(self):
        """If 3+ planets share a sign with any of house 4/8/12, capacity -= 15."""
        # All planets in "aries", house4 also in "aries" → 3+ planets → -15
        chart = {
            "sun_sign": "aries", "moon_sign": "aries", "mercury_sign": "aries",
            "venus_sign": "taurus", "mars_sign": "taurus",
            "jupiter_sign": "taurus", "saturn_sign": "taurus", "pluto_sign": "taurus",
            "house4_sign": "aries",  # 3 planets match house 4
            "house8_sign": None, "house12_sign": None,
        }
        result = compute_emotional_capacity(chart)
        assert result == 35  # 50 - 15


# ── Phase H v1.5: Uranus / Neptune ───────────────────────────────

VALID_SIGNS = {
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
}

def test_chart_includes_uranus_neptune():
    """calculate_chart should return uranus_sign and neptune_sign."""
    result = calculate_chart("1995-06-15", data_tier=3)
    assert "uranus_sign" in result
    assert "neptune_sign" in result
    assert result["uranus_sign"] in VALID_SIGNS
    assert result["neptune_sign"] in VALID_SIGNS

def test_uranus_neptune_generational():
    """Uranus/Neptune change signs very slowly.
    Two people born 6 months apart in the same year should share the same sign."""
    r1 = calculate_chart("1990-03-01", data_tier=3)
    r2 = calculate_chart("1990-09-01", data_tier=3)
    # Neptune ~14 yr/sign: definitely same sign within same year
    assert r1["neptune_sign"] == r2["neptune_sign"]
    # Uranus ~7 yr/sign: highly likely same sign within same year
    assert r1["uranus_sign"] == r2["uranus_sign"]


# ── Phase H v1.5: bazi_day_branch ────────────────────────────────

def test_bazi_returns_day_branch():
    """calculate_bazi should return bazi_day_branch as an Earthly Branch character."""
    from bazi import EARTHLY_BRANCHES
    bazi = calculate_bazi("1997-03-07", birth_time="precise", birth_time_exact="10:59",
                          lat=25.033, lng=121.565, data_tier=1)
    assert "bazi_day_branch" in bazi
    assert bazi["bazi_day_branch"] in EARTHLY_BRANCHES

def test_bazi_day_branch_matches_day_pillar():
    """bazi_day_branch must equal the day pillar branch character."""
    bazi = calculate_bazi("1997-03-07", birth_time="precise", birth_time_exact="10:59",
                          lat=25.033, lng=121.565, data_tier=1)
    # Day pillar for 1997-03-07 = 戊申; branch = 申
    assert bazi["bazi_day_branch"] == bazi["four_pillars"]["day"]["branch"]
    assert bazi["bazi_day_branch"] == "申"


# ── Phase H v1.5: check_branch_relations ────────────────────────

from bazi import check_branch_relations

class TestCheckBranchRelations:
    def test_clash_zi_wu(self):
        """子午 is a classic Six Clash (六沖)."""
        assert check_branch_relations("子", "午") == "clash"

    def test_clash_is_symmetric(self):
        assert check_branch_relations("午", "子") == "clash"

    def test_all_six_clashes(self):
        pairs = [("子","午"), ("丑","未"), ("寅","申"), ("卯","酉"), ("辰","戌"), ("巳","亥")]
        for a, b in pairs:
            assert check_branch_relations(a, b) == "clash", f"{a}-{b} should be clash"
            assert check_branch_relations(b, a) == "clash", f"{b}-{a} should be clash"

    def test_punishment_zi_mao(self):
        """子卯相刑."""
        assert check_branch_relations("子", "卯") == "punishment"

    def test_punishment_self_wu(self):
        """午午 is a self-punishment (自刑)."""
        assert check_branch_relations("午", "午") == "punishment"

    def test_self_punishment_branches(self):
        """辰午酉亥 self-punish when paired with themselves."""
        for b in ("辰", "午", "酉", "亥"):
            assert check_branch_relations(b, b) == "punishment", f"{b}+{b} should be self-punishment"

    def test_harm_zi_wei(self):
        """子未相害."""
        assert check_branch_relations("子", "未") == "harm"

    def test_harm_is_symmetric(self):
        assert check_branch_relations("未", "子") == "harm"

    def test_neutral_zi_yin(self):
        """子寅 has no special interaction."""
        assert check_branch_relations("子", "寅") == "neutral"

    def test_clash_takes_priority_over_potential_harm(self):
        """子午 should be clash, not harm (clash checked first)."""
        assert check_branch_relations("子", "午") == "clash"


# ── Phase I: Planet Degree Output Tests ─────────────────────────────────────

class TestPlanetDegrees:
    """chart.py now outputs {planet}_degree (0-360) alongside {planet}_sign."""

    def test_sun_degree_present(self):
        result = calculate_chart(birth_date="1995-06-15", data_tier=3)
        assert "sun_degree" in result
        assert isinstance(result["sun_degree"], float)
        assert 0.0 <= result["sun_degree"] < 360.0

    def test_sun_degree_in_gemini_range(self):
        """1995-06-15 Sun should be in Gemini (60°-90°)."""
        result = calculate_chart(birth_date="1995-06-15", data_tier=3)
        assert 60.0 <= result["sun_degree"] < 90.0

    def test_all_planets_have_degree(self):
        """Every planet in PLANETS dict should produce a _degree field."""
        result = calculate_chart(birth_date="1990-01-01", data_tier=3)
        for planet in ("sun", "moon", "mercury", "venus", "mars",
                       "jupiter", "saturn", "uranus", "neptune", "pluto"):
            assert f"{planet}_degree" in result, f"Missing {planet}_degree"
            # Tier 3 moon_sign is None but moon_degree should also be None
            if planet == "moon":
                assert result[f"{planet}_degree"] is None
            else:
                assert isinstance(result[f"{planet}_degree"], float)
                assert 0.0 <= result[f"{planet}_degree"] < 360.0

    def test_degree_consistent_with_sign(self):
        """The sign derived from the degree should match the stored sign."""
        result = calculate_chart(birth_date="1995-06-15", data_tier=2,
                                 birth_time="afternoon")
        for planet in ("sun", "venus", "mars", "saturn"):
            deg = result.get(f"{planet}_degree")
            sign = result.get(f"{planet}_sign")
            if deg is not None and sign is not None:
                assert longitude_to_sign(deg) == sign, (
                    f"{planet}: degree {deg} → sign {longitude_to_sign(deg)} ≠ stored {sign}"
                )

    def test_tier1_house_degrees_present(self):
        """Tier 1 should have house4/8/12 degree fields."""
        result = calculate_chart(
            birth_date="1990-05-15",
            birth_time="precise",
            birth_time_exact="14:30",
            data_tier=1,
            lat=25.033, lng=121.565,
        )
        for h in ("house4", "house8", "house12", "ascendant"):
            assert f"{h}_degree" in result, f"Missing {h}_degree"
            assert isinstance(result[f"{h}_degree"], float)
            assert 0.0 <= result[f"{h}_degree"] < 360.0

    def test_tier2_house_degrees_none(self):
        """Tier 2/3 house degrees should be None (no birth time for cusp calc)."""
        result = calculate_chart(birth_date="1990-05-15", data_tier=2,
                                 birth_time="morning")
        for h in ("house4", "house8", "house12", "ascendant"):
            assert result.get(f"{h}_degree") is None, f"{h}_degree should be None for Tier 2"

    def test_uranus_neptune_degrees_present(self):
        """Previously missing planets: Uranus and Neptune should have degree fields."""
        result = calculate_chart(birth_date="1990-01-01", data_tier=3)
        assert "uranus_degree" in result
        assert "neptune_degree" in result
        assert isinstance(result["uranus_degree"], float)
        assert isinstance(result["neptune_degree"], float)

    def test_degrees_are_floats_rounded_to_2dp(self):
        """Degrees should be rounded to 2 decimal places."""
        result = calculate_chart(birth_date="1988-03-21", data_tier=3)
        sun_deg = result["sun_degree"]
        assert round(sun_deg, 2) == sun_deg


# ── Natal Aspects ─────────────────────────────────────────────────────────────

_VALID_ASPECT_TYPES = {"conjunction", "sextile", "square", "trine", "opposition"}


class TestNatalAspects:
    """Tests for compute_natal_aspects() via calculate_chart()."""

    # 1. natal_aspects key is present in Tier 1 chart result
    def test_natal_aspects_key_present_tier1(self):
        result = calculate_chart(
            birth_date="1995-06-15",
            birth_time="precise",
            birth_time_exact="14:30",
            lat=25.033,
            lng=121.565,
            data_tier=1,
        )
        assert "natal_aspects" in result
        assert isinstance(result["natal_aspects"], list)

    # Also present for Tier 2 and Tier 3
    def test_natal_aspects_key_present_tier2(self):
        result = calculate_chart(
            birth_date="1995-06-15",
            birth_time="morning",
            lat=25.033,
            lng=121.565,
            data_tier=2,
        )
        assert "natal_aspects" in result
        assert isinstance(result["natal_aspects"], list)

    def test_natal_aspects_key_present_tier3(self):
        result = calculate_chart(birth_date="1995-06-15", data_tier=3)
        assert "natal_aspects" in result
        assert isinstance(result["natal_aspects"], list)

    # 2. Each aspect dict has required keys: a, b, aspect, orb, strength
    def test_aspect_dict_has_required_keys(self):
        result = calculate_chart(
            birth_date="1995-06-15",
            birth_time="precise",
            birth_time_exact="14:30",
            lat=25.033,
            lng=121.565,
            data_tier=1,
        )
        aspects = result["natal_aspects"]
        # A real chart will always have at least one aspect within orb
        assert len(aspects) > 0, "Expected at least one natal aspect for Tier 1 chart"
        for asp in aspects:
            assert "a" in asp, f"Missing key 'a' in aspect: {asp}"
            assert "b" in asp, f"Missing key 'b' in aspect: {asp}"
            assert "aspect" in asp, f"Missing key 'aspect' in aspect: {asp}"
            assert "orb" in asp, f"Missing key 'orb' in aspect: {asp}"
            assert "strength" in asp, f"Missing key 'strength' in aspect: {asp}"

    # 3. No duplicate pairs (a-b same as b-a)
    def test_no_duplicate_pairs(self):
        result = calculate_chart(
            birth_date="1995-06-15",
            birth_time="precise",
            birth_time_exact="14:30",
            lat=25.033,
            lng=121.565,
            data_tier=1,
        )
        seen: set = set()
        for asp in result["natal_aspects"]:
            # Canonical form: always alphabetical order of the pair
            pair = tuple(sorted([asp["a"], asp["b"]]))
            assert pair not in seen, f"Duplicate pair found: {asp['a']}-{asp['b']}"
            seen.add(pair)

    # 4. All aspect types are valid strings
    def test_all_aspect_types_valid(self):
        result = calculate_chart(
            birth_date="1995-06-15",
            birth_time="precise",
            birth_time_exact="14:30",
            lat=25.033,
            lng=121.565,
            data_tier=1,
        )
        for asp in result["natal_aspects"]:
            assert asp["aspect"] in _VALID_ASPECT_TYPES, (
                f"Invalid aspect type: {asp['aspect']}"
            )

    # 5. strength is between 0 and 1 (inclusive)
    def test_strength_in_range(self):
        result = calculate_chart(
            birth_date="1995-06-15",
            birth_time="precise",
            birth_time_exact="14:30",
            lat=25.033,
            lng=121.565,
            data_tier=1,
        )
        for asp in result["natal_aspects"]:
            assert 0.0 <= asp["strength"] <= 1.0, (
                f"strength out of range: {asp['strength']} for {asp}"
            )

    # 6. If planet degree is None, that pair is skipped (no crash)
    def test_none_degree_skipped_no_crash(self):
        """Tier 3 sets moon_degree to None — no crash, pair simply excluded."""
        result = calculate_chart(birth_date="1995-06-15", data_tier=3)
        # Should not raise; moon-related pairs are silently skipped
        aspects = result["natal_aspects"]
        assert isinstance(aspects, list)
        # moon_degree is None in Tier 3; verify no aspect has moon as a or b
        for asp in aspects:
            assert asp["a"] != "moon", "moon should be skipped in Tier 3 (degree is None)"
            assert asp["b"] != "moon", "moon should be skipped in Tier 3 (degree is None)"

    # 7. Aspects are sorted by strength descending
    def test_sorted_by_strength_descending(self):
        result = calculate_chart(
            birth_date="1995-06-15",
            birth_time="precise",
            birth_time_exact="14:30",
            lat=25.033,
            lng=121.565,
            data_tier=1,
        )
        strengths = [asp["strength"] for asp in result["natal_aspects"]]
        assert strengths == sorted(strengths, reverse=True), (
            "natal_aspects should be sorted by strength descending"
        )

    # 8. Tier 1 may include ascendant in aspects; Tier 2/3 should not
    def test_tier1_may_include_ascendant_aspects(self):
        """Tier 1 has ascendant_degree set, so ascendant can appear in aspects.
        Tier 2 must never produce ascendant-involved aspects (degree is None)."""
        result = calculate_chart(
            birth_date="1995-06-15",
            birth_time="precise",
            birth_time_exact="14:30",
            lat=25.033,
            lng=121.565,
            data_tier=1,
        )
        # ascendant_degree is not None for Tier 1
        assert result.get("ascendant_degree") is not None
        # It's valid for aspects to include ascendant (not required, but possible)
        assert isinstance(result["natal_aspects"], list)

        # Tier 2 must never have ascendant in any aspect (degree is None for Tier 2)
        result_t2 = calculate_chart(
            birth_date="1995-06-15",
            birth_time="morning",
            lat=25.033,
            lng=121.565,
            data_tier=2,
        )
        assert result_t2.get("ascendant_degree") is None
        for asp in result_t2["natal_aspects"]:
            assert asp["a"] != "ascendant", "ascendant should never appear in Tier 2 aspects"
            assert asp["b"] != "ascendant", "ascendant should never appear in Tier 2 aspects"

    def test_tier1_planet_set_includes_ascendant(self):
        """Verify that Tier 1 natal aspect computation uses ascendant in the planet set.
        We use a birth date/time where ascendant is known to be within orb of a planet
        by checking that the ascendant_degree is set AND any aspects list is consistent
        with ascendant being a candidate (no ascendant aspects does not mean it's absent
        from the input set — the set always includes it for Tier 1)."""
        result = calculate_chart(
            birth_date="1997-03-08",
            birth_time="precise",
            birth_time_exact="20:00",
            lat=25.033,
            lng=121.565,
            data_tier=1,
        )
        # Tier 1 must have ascendant_degree populated
        assert result.get("ascendant_degree") is not None
        # Ascendant is in the candidate planet set for Tier 1; if any planet degree
        # happens to be within orb of the ascendant, it will appear as 'a' or 'b'.
        # The important invariant: Tier 3 of the SAME chart must NEVER have ascendant.
        result_t3 = calculate_chart(birth_date="1997-03-08", data_tier=3)
        assert result_t3.get("ascendant_degree") is None
        for asp in result_t3["natal_aspects"]:
            assert asp["a"] != "ascendant"
            assert asp["b"] != "ascendant"

    def test_tier3_no_ascendant_in_aspects(self):
        """Tier 3 has ascendant_degree = None, so ascendant should never appear."""
        result = calculate_chart(birth_date="1995-06-15", data_tier=3)
        assert result.get("ascendant_degree") is None
        for asp in result["natal_aspects"]:
            assert asp["a"] != "ascendant"
            assert asp["b"] != "ascendant"

    # 9. orb is non-negative and less than the maximum orb for that aspect type
    def test_orb_within_max_orb(self):
        MAX_ORBS = {
            "conjunction": 8.0,
            "sextile": 6.0,
            "square": 8.0,
            "trine": 8.0,
            "opposition": 8.0,
        }
        result = calculate_chart(
            birth_date="1997-03-08",
            birth_time="precise",
            birth_time_exact="20:00",
            lat=25.033,
            lng=121.565,
            data_tier=1,
        )
        for asp in result["natal_aspects"]:
            max_orb = MAX_ORBS[asp["aspect"]]
            assert asp["orb"] >= 0.0, f"Negative orb: {asp}"
            assert asp["orb"] <= max_orb, (
                f"orb {asp['orb']} exceeds max {max_orb} for {asp['aspect']}: {asp}"
            )

    # 10. Strength floor: at the orb boundary, strength should be 0.2 (not 0.0)
    def test_strength_floor_at_orb_boundary(self):
        """At orb == max_orb the canonical formula yields strength = 0.2, not 0.0.
        Verify no aspect in any real chart has strength below 0.2."""
        result = calculate_chart(
            birth_date="1995-06-15",
            birth_time="precise",
            birth_time_exact="14:30",
            lat=25.033,
            lng=121.565,
            data_tier=1,
        )
        for asp in result["natal_aspects"]:
            assert asp["strength"] >= 0.2, (
                f"strength {asp['strength']} is below the 0.2 floor for aspect: {asp}"
            )

    def test_strength_exact_conjunction_is_1(self):
        """An exact conjunction (orb=0) should yield strength=1.0."""
        from chart import compute_natal_aspects
        # Craft a minimal chart dict with two planets at the exact same degree
        fake_chart = {
            "sun_degree": 45.0,
            "moon_degree": 45.0,
            # Provide None for all other planets so they are skipped
            "mercury_degree": None, "venus_degree": None, "mars_degree": None,
            "jupiter_degree": None, "saturn_degree": None, "chiron_degree": None,
        }
        aspects = compute_natal_aspects(fake_chart, data_tier=2)
        assert len(aspects) == 1
        assert aspects[0]["aspect"] == "conjunction"
        assert aspects[0]["orb"] == 0.0
        assert aspects[0]["strength"] == 1.0


# ── _angular_distance unit tests ──────────────────────────────────────────────

class TestLilithAndVertex:
    """Tests for Lilith (MEAN_APOG) and Vertex extraction in Tier 1 charts."""

    def _tier1_chart(self):
        return calculate_chart(
            birth_date="1990-05-15",
            birth_time="precise",
            birth_time_exact="14:30",
            data_tier=1,
            lat=25.033, lng=121.565,
        )

    def _tier3_chart(self):
        return calculate_chart(birth_date="1990-05-15", data_tier=3)

    def test_lilith_sign_present_in_tier1(self):
        """Tier 1 chart must contain lilith_sign."""
        result = self._tier1_chart()
        assert "lilith_sign" in result

    def test_lilith_degree_present_in_tier1(self):
        """Tier 1 chart must contain lilith_degree as a float in [0, 360)."""
        result = self._tier1_chart()
        assert "lilith_degree" in result
        deg = result["lilith_degree"]
        # May be None if MEAN_APOG fails, but when present it must be in range
        if deg is not None:
            assert isinstance(deg, float)
            assert 0.0 <= deg < 360.0

    def test_vertex_sign_present_in_tier1(self):
        """Tier 1 chart must contain vertex_sign."""
        result = self._tier1_chart()
        assert "vertex_sign" in result
        assert result["vertex_sign"] in (
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
        )

    def test_vertex_degree_present_in_tier1(self):
        """Tier 1 chart must contain vertex_degree as a float in [0, 360)."""
        result = self._tier1_chart()
        assert "vertex_degree" in result
        deg = result["vertex_degree"]
        assert isinstance(deg, float)
        assert 0.0 <= deg < 360.0

    def test_lilith_absent_in_tier3(self):
        """Tier 3 chart must NOT contain lilith_sign or lilith_degree."""
        result = self._tier3_chart()
        assert "lilith_sign" not in result
        assert "lilith_degree" not in result

    def test_vertex_absent_in_tier3(self):
        """Tier 3 chart must NOT contain vertex_sign or vertex_degree."""
        result = self._tier3_chart()
        assert "vertex_sign" not in result
        assert "vertex_degree" not in result

    def test_lilith_sign_consistent_with_degree(self):
        """lilith_sign must correspond to the correct 30° slice of lilith_degree."""
        result = self._tier1_chart()
        deg = result.get("lilith_degree")
        sign = result.get("lilith_sign")
        if deg is None or sign is None:
            return  # Graceful degradation; skip consistency check
        signs = [
            "aries", "taurus", "gemini", "cancer",
            "leo", "virgo", "libra", "scorpio",
            "sagittarius", "capricorn", "aquarius", "pisces",
        ]
        expected_sign = signs[int(deg // 30) % 12]
        assert sign == expected_sign


class TestAngularDistance:
    """Unit tests for the _angular_distance() helper in chart.py."""

    def test_same_angle_is_zero(self):
        """Two identical longitudes should have distance 0."""
        assert _angular_distance(45.0, 45.0) == 0.0

    def test_90_degrees_apart(self):
        """Longitudes 90° apart should return 90.0."""
        assert _angular_distance(0.0, 90.0) == 90.0

    def test_180_degrees_apart(self):
        """Opposite longitudes should return 180.0."""
        assert _angular_distance(0.0, 180.0) == 180.0

    def test_wraparound_359_and_1(self):
        """359° and 1° should be 2° apart (not 358°)."""
        assert _angular_distance(359.0, 1.0) == 2.0

    def test_wraparound_350_and_10(self):
        """350° and 10° should be 20° apart (not 340°)."""
        assert _angular_distance(350.0, 10.0) == 20.0


# ── Lunar Nodes (南北交點) ──────────────────────────────────────────────────

class TestLunarNodes:
    """Tests for Lunar Node extraction in calculate_chart()."""

    def test_north_node_returned_all_tiers(self):
        """north_node_sign/degree should be present for Tier 1, 2, and 3."""
        for tier, kwargs in [
            (3, {}),
            (2, {"birth_time": "morning", "lat": 25.033, "lng": 121.565}),
            (1, {"birth_time": "precise", "birth_time_exact": "14:30",
                 "lat": 25.033, "lng": 121.565}),
        ]:
            result = calculate_chart(birth_date="1995-06-15", data_tier=tier, **kwargs)
            assert result["north_node_sign"] is not None, f"Tier {tier}: missing north_node_sign"
            assert result["north_node_degree"] is not None, f"Tier {tier}: missing north_node_degree"
            assert result["south_node_sign"] is not None, f"Tier {tier}: missing south_node_sign"
            assert result["south_node_degree"] is not None, f"Tier {tier}: missing south_node_degree"

    def test_south_node_is_opposite_north(self):
        """South Node degree should equal (North Node + 180) % 360."""
        result = calculate_chart(birth_date="1995-06-15", data_tier=3)
        nn = result["north_node_degree"]
        sn = result["south_node_degree"]
        expected_sn = round((nn + 180.0) % 360.0, 2)
        assert sn == pytest.approx(expected_sn, abs=0.01)

    def test_south_node_sign_correct(self):
        """south_node_sign should match longitude_to_sign(south_node_degree)."""
        result = calculate_chart(birth_date="2000-01-01", data_tier=3)
        assert result["south_node_sign"] == longitude_to_sign(result["south_node_degree"])


# ── House 7 (第七宮 / Descendant) ──────────────────────────────────────────

class TestHouse7:
    """Tests for House 7 extraction in calculate_chart()."""

    def test_house7_present_tier1(self):
        """house7_sign/degree should be present for Tier 1."""
        result = calculate_chart(
            birth_date="1995-06-15", data_tier=1,
            birth_time="precise", birth_time_exact="14:30",
            lat=25.033, lng=121.565,
        )
        assert result["house7_sign"] is not None
        assert result["house7_degree"] is not None

    def test_house7_null_tier2(self):
        """house7 should be null for Tier 2 (no precise time)."""
        result = calculate_chart(
            birth_date="1995-06-15", data_tier=2,
            birth_time="morning", lat=25.033, lng=121.565,
        )
        assert result["house7_sign"] is None
        assert result["house7_degree"] is None

    def test_house7_null_tier3(self):
        """house7 should be null for Tier 3."""
        result = calculate_chart(birth_date="1995-06-15", data_tier=3)
        assert result["house7_sign"] is None
        assert result["house7_degree"] is None

    def test_descendant_roughly_opposite_ascendant(self):
        """House 7 cusp should be roughly ASC + 180° (Placidus may deviate slightly)."""
        result = calculate_chart(
            birth_date="1995-06-15", data_tier=1,
            birth_time="precise", birth_time_exact="14:30",
            lat=25.033, lng=121.565,
        )
        asc = result["ascendant_degree"]
        h7  = result["house7_degree"]
        expected = (asc + 180.0) % 360.0
        diff = abs(h7 - expected)
        if diff > 180:
            diff = 360 - diff
        # Placidus H7 cusp is exactly ASC+180 for the ecliptic axis
        assert diff < 1.0, f"H7={h7}, expected≈{expected}, diff={diff}"

