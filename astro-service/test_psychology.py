"""Tests for psychology.py — per-user tag extraction."""
import pytest
from psychology import extract_sm_dynamics, extract_critical_degrees, compute_element_profile, extract_retrograde_karma


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

def test_element_profile_all_fire_weighted():
    # Even without Moon (no exact time), all fire signs get fire scores
    chart = {
        "sun_sign": "aries",        # fire, 3.0
        "mercury_sign": "sagittarius",  # fire, 2.0
        "venus_sign": "aries",      # fire, 2.0
        "mars_sign": "leo",         # fire, 2.0
        "jupiter_sign": "sagittarius",  # fire, 1.0
        "saturn_sign": "aries",     # fire, 1.0
    }
    profile = compute_element_profile(chart, is_exact_time=False)
    assert profile["scores"]["Fire"] == 11.0   # 3+2+2+2+1+1 without moon/asc
    assert profile["scores"]["Earth"] == 0.0
    assert "Fire" in profile["dominant"]   # 11 >= 7
    assert "Earth" in profile["deficiency"]  # 0 <= 1

def test_element_profile_mixed():
    # Without exact time: sun(3)+mars(2)=5 fire, jupiter(1)=1 earth, mercury(2)+saturn(1)=3 air, venus(2)=2 water
    chart = {
        "sun_sign": "aries",        # fire, 3.0
        "moon_sign": "taurus",       # earth -- excluded (no exact time)
        "mercury_sign": "gemini",    # air, 2.0
        "venus_sign": "cancer",      # water, 2.0
        "mars_sign": "leo",          # fire, 2.0
        "jupiter_sign": "virgo",     # earth, 1.0
        "saturn_sign": "libra",      # air, 1.0
        "uranus_sign": "scorpio",    # excluded
        "neptune_sign": "sagittarius", # excluded
        "pluto_sign": "capricorn",   # excluded
    }
    profile = compute_element_profile(chart, is_exact_time=False)
    assert profile["scores"]["Fire"] == 5.0   # sun(3)+mars(2)
    assert profile["scores"]["Earth"] == 1.0  # jupiter(1)
    assert profile["scores"]["Air"] == 3.0    # mercury(2)+saturn(1)
    assert profile["scores"]["Water"] == 2.0  # venus(2)
    assert "Earth" in profile["deficiency"]   # 1.0 <= 1.0
    assert profile["dominant"] == []          # nothing >= 7

def test_element_profile_missing_planets_graceful():
    chart = {"sun_sign": "aries"}  # only sun known, weight=3.0
    profile = compute_element_profile(chart, is_exact_time=False)
    assert profile["scores"]["Fire"] == 3.0
    assert "Earth" in profile["deficiency"]
    assert "Air" in profile["deficiency"]
    assert "Water" in profile["deficiency"]

def test_element_profile_unknown_sign_ignored():
    chart = {"sun_sign": "aries", "moon_sign": None}
    profile = compute_element_profile(chart, is_exact_time=False)
    assert profile["scores"]["Fire"] == 3.0  # only sun counted (moon=None)


def test_element_profile_moon_counted_with_exact_time():
    chart = {"sun_sign": "aries", "moon_sign": "leo"}  # both fire
    profile_inexact = compute_element_profile(chart, is_exact_time=False)
    profile_exact   = compute_element_profile(chart, is_exact_time=True)
    assert profile_inexact["scores"]["Fire"] == 3.0   # only sun (moon excluded)
    assert profile_exact["scores"]["Fire"] == 6.0     # sun(3)+moon(3)


def test_element_profile_dominant_requires_score_7():
    # Sun(3) + Moon(3) = 6 -- NOT dominant
    chart = {"sun_sign": "aries", "moon_sign": "leo"}
    profile = compute_element_profile(chart, is_exact_time=True)
    assert profile["dominant"] == []   # 6 < 7

    # Sun(3) + Moon(3) + Mercury(2) = 8 -- dominant
    chart2 = {"sun_sign": "aries", "moon_sign": "leo", "mercury_sign": "sagittarius"}
    profile2 = compute_element_profile(chart2, is_exact_time=True)
    assert "Fire" in profile2["dominant"]


# -- extract_retrograde_karma --------------------------------------------------

def test_retrograde_venus_tag():
    chart = {"venus_rx": True}
    tags = extract_retrograde_karma(chart)
    assert "Karmic_Love_Venus_Rx" in tags


def test_retrograde_mars_tag():
    chart = {"mars_rx": True}
    tags = extract_retrograde_karma(chart)
    assert "Suppressed_Anger_Mars_Rx" in tags


def test_retrograde_mercury_tag():
    chart = {"mercury_rx": True}
    tags = extract_retrograde_karma(chart)
    assert "Internal_Dialogue_Mercury_Rx" in tags


def test_retrograde_no_rx_no_tags():
    chart = {"venus_rx": False, "mars_rx": False, "mercury_rx": False}
    tags = extract_retrograde_karma(chart)
    assert tags == []


def test_retrograde_missing_keys_no_error():
    tags = extract_retrograde_karma({})
    assert tags == []
