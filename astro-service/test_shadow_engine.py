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
