"""
Tests for DESTINY natal chart calculator.
Uses known birth data to verify Swiss Ephemeris calculations.
"""

from chart import calculate_chart, longitude_to_sign
from bazi import calculate_bazi, analyze_element_relation, HEAVENLY_STEMS, STEM_ELEMENTS, EARTHLY_BRANCHES


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
