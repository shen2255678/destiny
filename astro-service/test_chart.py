"""
Tests for DESTINY natal chart calculator.
Uses known birth data to verify Swiss Ephemeris calculations.
"""

from chart import calculate_chart, longitude_to_sign


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
