"""Tests for psychology.py — per-user tag extraction."""
import pytest
from psychology import extract_sm_dynamics, extract_critical_degrees, compute_element_profile


def _chart(**kwargs):
    return {k: v for k, v in kwargs.items()}


def test_sm_natural_dom_sun_pluto_conjunction():
    chart = _chart(sun_degree=10.0, pluto_degree=14.0)
    tags = extract_sm_dynamics(chart)
    assert "Natural_Dom" in tags

def test_sm_natural_dom_mars_pluto_trine():
    chart = _chart(mars_degree=10.0, pluto_degree=130.0)
    tags = extract_sm_dynamics(chart)
    assert "Natural_Dom" in tags

def test_sm_sadist_dom_mars_pluto_square():
    chart = _chart(mars_degree=10.0, pluto_degree=100.0)
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

def test_critical_karmic_venus_29_degree():
    # 269.5 % 30 = 29.5 → Karmic_Crisis
    chart = _chart(venus_degree=269.5)
    tags = extract_critical_degrees(chart, is_exact_time=False)
    assert "Karmic_Crisis_VENUS" in tags

def test_critical_blind_sun_0_degree():
    chart = _chart(sun_degree=0.5)
    tags = extract_critical_degrees(chart, is_exact_time=False)
    assert "Blind_Impulse_SUN" in tags

def test_critical_moon_excluded_tier23():
    chart = _chart(moon_degree=269.5)
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
    chart = _chart(sun_degree=91.0)  # 91 % 30 = 1.0, not < 1.0 and not >= 29.0
    tags = extract_critical_degrees(chart, is_exact_time=False)
    assert "Blind_Impulse_SUN" not in tags
    assert "Karmic_Crisis_SUN" not in tags

def test_critical_no_degrees_no_tags():
    tags = extract_critical_degrees({}, is_exact_time=True)
    assert tags == []

def test_element_profile_all_fire():
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
        "sun_sign": "aries", "moon_sign": "taurus", "mercury_sign": "gemini",
        "venus_sign": "cancer", "mars_sign": "leo", "jupiter_sign": "virgo",
        "saturn_sign": "libra", "uranus_sign": "scorpio",
        "neptune_sign": "sagittarius", "pluto_sign": "capricorn",
    }
    profile = compute_element_profile(chart)
    assert profile["counts"] == {"Fire": 3, "Earth": 3, "Air": 2, "Water": 2}
    assert profile["deficiency"] == []
    assert profile["dominant"] == []

def test_element_profile_missing_planets_graceful():
    chart = {"sun_sign": "aries"}
    profile = compute_element_profile(chart)
    assert profile["counts"]["Fire"] == 1
    assert "Earth" in profile["deficiency"]
    assert "Air" in profile["deficiency"]
    assert "Water" in profile["deficiency"]

def test_element_profile_unknown_sign_ignored():
    chart = {"sun_sign": "aries", "moon_sign": None}
    profile = compute_element_profile(chart)
    assert profile["counts"]["Fire"] == 1
