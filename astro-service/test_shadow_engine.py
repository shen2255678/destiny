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
    """B's Moon conjunct A's Chiron (diff=4° ≤ 5°) → B_Moon_Triggers_A_Chiron + soul_mod +15."""
    a = {"chiron_degree": 100.0}
    b = {"moon_degree": 104.0}   # diff=4° < 5° → conjunction
    result = compute_shadow_and_wound(a, b)
    assert result["soul_mod"] >= 15.0
    assert "B_Moon_Triggers_A_Chiron" in result["shadow_tags"]
    assert result["high_voltage"] is True


def test_chiron_heals_moon_bidirectional():
    """Both A's Moon conjunct B's Chiron and B's Moon conjunct A's Chiron → both tags."""
    a = {"chiron_degree": 100.0, "moon_degree": 200.0}
    b = {"chiron_degree": 195.0, "moon_degree": 104.0}
    # B's Moon (104) vs chiron_a (100): diff=4 ≤ 5 → B_Moon_Triggers_A_Chiron
    # A's Moon (200) vs chiron_b (195): diff=5 ≤ 5 → A_Moon_Triggers_B_Chiron
    result = compute_shadow_and_wound(a, b)
    assert "A_Moon_Triggers_B_Chiron" in result["shadow_tags"]
    assert "B_Moon_Triggers_A_Chiron" in result["shadow_tags"]
    assert result["soul_mod"] >= 30.0


def test_chiron_triggers_wound_lust_bonus_and_high_voltage():
    """A's Mars conjunct B's Chiron (diff=0°) → A_Mars_Triggers_B_Chiron + lust_mod +10 + soul_mod +15."""
    a = {"mars_degree": 100.0}
    b = {"chiron_degree": 100.0}   # diff=0° conjunction → trigger
    result = compute_shadow_and_wound(a, b)
    assert result["lust_mod"] >= 10.0
    assert result["soul_mod"] >= 15.0
    assert result["high_voltage"] is True
    assert "A_Mars_Triggers_B_Chiron" in result["shadow_tags"]


def test_12th_house_shadow_a_in_b_12th_requires_tier1():
    # sun_a falls into b's 12th house
    a = {"sun_degree": 200.0}
    b = {"house12_degree": 195.0, "ascendant_degree": 225.0}  # 12th house 195→225
    result = compute_shadow_and_wound(a, b)
    assert "A_Illuminates_B_Shadow" in result["shadow_tags"]
    assert result["high_voltage"] is True
    assert result["soul_mod"] >= 20.0


def test_no_trigger_far_degrees():
    """Chiron at 0° vs Moon at 90° — not a conjunction or opposition (orb=5°) → no trigger."""
    a = {"chiron_degree": 0.0}
    b = {"moon_degree": 90.0}   # 90° apart — not a conjunction or opposition
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
    assert result["partner_mod"] == pytest.approx(-40.0)


def test_chiron_b_triggers_a_wound():
    """B's Mars conjunct A's Chiron (diff=0°) → B_Mars_Triggers_A_Chiron."""
    a = {"chiron_degree": 100.0}
    b = {"mars_degree": 100.0}   # diff=0° conjunction → triggers
    result = compute_shadow_and_wound(a, b)
    assert result["lust_mod"] >= 10.0
    assert result["soul_mod"] >= 15.0
    assert result["high_voltage"] is True
    assert "B_Mars_Triggers_A_Chiron" in result["shadow_tags"]


def test_b_illuminates_a_shadow():
    """Trigger 6: sun_b/mars_b in A's 12th house → B_Illuminates_A_Shadow."""
    a = {"house12_degree": 100.0, "ascendant_degree": 130.0}
    b = {"sun_degree": 115.0}   # 115 falls between 100 and 130
    result = compute_shadow_and_wound(a, b)
    assert "B_Illuminates_A_Shadow" in result["shadow_tags"]
    assert result["high_voltage"] is True
    assert result["soul_mod"] >= 20.0
    assert result["partner_mod"] == pytest.approx(-10.0)


# ── New tests: expanded Chiron triggers (all personal planets) ────────────────

def test_a_sun_triggers_b_chiron_conjunction():
    """A's Sun conjunct B's Chiron (diff=2°) → A_Sun_Triggers_B_Chiron + soul_mod +15."""
    a = {"sun_degree": 50.0}
    b = {"chiron_degree": 52.0}   # diff=2° ≤ 5°
    result = compute_shadow_and_wound(a, b)
    assert "A_Sun_Triggers_B_Chiron" in result["shadow_tags"]
    assert result["soul_mod"] == pytest.approx(15.0)
    assert result["lust_mod"] == pytest.approx(0.0)
    assert result["high_voltage"] is True
    assert result["partner_mod"] == pytest.approx(-10.0)


def test_a_venus_triggers_b_chiron_conjunction():
    """A's Venus conjunct B's Chiron (diff=3°) → A_Venus_Triggers_B_Chiron + soul_mod +15."""
    a = {"venus_degree": 120.0}
    b = {"chiron_degree": 123.0}   # diff=3° ≤ 5°
    result = compute_shadow_and_wound(a, b)
    assert "A_Venus_Triggers_B_Chiron" in result["shadow_tags"]
    assert result["soul_mod"] == pytest.approx(15.0)
    assert result["lust_mod"] == pytest.approx(0.0)
    assert result["high_voltage"] is True
    assert result["partner_mod"] == pytest.approx(-10.0)


def test_a_mars_triggers_b_chiron_adds_lust_mod():
    """A's Mars conjunct B's Chiron → soul_mod +15 AND lust_mod +10."""
    a = {"mars_degree": 0.0}
    b = {"chiron_degree": 0.0}
    result = compute_shadow_and_wound(a, b)
    assert "A_Mars_Triggers_B_Chiron" in result["shadow_tags"]
    assert result["soul_mod"] == pytest.approx(15.0)
    assert result["lust_mod"] == pytest.approx(10.0)
    assert result["high_voltage"] is True
    assert result["partner_mod"] == pytest.approx(-15.0)


def test_a_moon_triggers_b_chiron_no_lust_mod():
    """A's Moon conjunct B's Chiron → soul_mod +15, lust_mod stays 0 (Moon is not Mars)."""
    a = {"moon_degree": 200.0}
    b = {"chiron_degree": 200.0}
    result = compute_shadow_and_wound(a, b)
    assert "A_Moon_Triggers_B_Chiron" in result["shadow_tags"]
    assert result["soul_mod"] == pytest.approx(15.0)
    assert result["lust_mod"] == pytest.approx(0.0)
    assert result["partner_mod"] == pytest.approx(-10.0)


def test_opposition_within_5deg_triggers():
    """A's Moon opposite B's Chiron (diff=180°, within orb=5°) → triggers."""
    a = {"moon_degree": 0.0}
    b = {"chiron_degree": 180.0}   # exact opposition
    result = compute_shadow_and_wound(a, b)
    assert "A_Moon_Triggers_B_Chiron" in result["shadow_tags"]
    assert result["soul_mod"] >= 15.0
    assert result["high_voltage"] is True


def test_opposition_exactly_at_orb_boundary_triggers():
    """A's Sun at 175° vs B's Chiron at 0° → diff=175°, abs(175-180)=5° ≤ 5° → triggers."""
    a = {"sun_degree": 175.0}
    b = {"chiron_degree": 0.0}   # diff=175, abs(175-180)=5 → exactly at boundary
    result = compute_shadow_and_wound(a, b)
    assert "A_Sun_Triggers_B_Chiron" in result["shadow_tags"]


def test_orb_6deg_does_not_trigger():
    """A's Moon at 6° from B's Chiron → strictly outside orb of 5° → no trigger."""
    a = {"moon_degree": 0.0}
    b = {"chiron_degree": 6.0}   # diff=6° > 5°
    result = compute_shadow_and_wound(a, b)
    assert "A_Moon_Triggers_B_Chiron" not in result["shadow_tags"]
    assert result["soul_mod"] == 0.0
    assert result["high_voltage"] is False


def test_square_90deg_does_not_trigger():
    """A's Mars at 90° from B's Chiron → square NOT in new trigger list → no tag."""
    a = {"mars_degree": 0.0}
    b = {"chiron_degree": 90.0}
    result = compute_shadow_and_wound(a, b)
    assert "A_Mars_Triggers_B_Chiron" not in result["shadow_tags"]
    assert result["lust_mod"] == 0.0


def test_b_sun_triggers_a_chiron():
    """B's Sun conjunct A's Chiron → B_Sun_Triggers_A_Chiron."""
    a = {"chiron_degree": 300.0}
    b = {"sun_degree": 302.0}   # diff=2° ≤ 5°
    result = compute_shadow_and_wound(a, b)
    assert "B_Sun_Triggers_A_Chiron" in result["shadow_tags"]
    assert result["soul_mod"] == pytest.approx(15.0)
    assert result["high_voltage"] is True


def test_b_mars_triggers_a_chiron_adds_lust_mod():
    """B's Mars opposite A's Chiron (diff=180°) → B_Mars_Triggers_A_Chiron + lust_mod +10."""
    a = {"chiron_degree": 0.0}
    b = {"mars_degree": 180.0}   # diff=180° exact opposition
    result = compute_shadow_and_wound(a, b)
    assert "B_Mars_Triggers_A_Chiron" in result["shadow_tags"]
    assert result["soul_mod"] == pytest.approx(15.0)
    assert result["lust_mod"] == pytest.approx(10.0)
    assert result["high_voltage"] is True


def test_multiple_planets_all_trigger_independently():
    """All 4 of A's personal planets conjunct B's Chiron → 4 tags, soul_mod=60, lust_mod=10."""
    a = {
        "sun_degree": 50.0,
        "moon_degree": 50.0,
        "venus_degree": 50.0,
        "mars_degree": 50.0,
    }
    b = {"chiron_degree": 50.0}
    result = compute_shadow_and_wound(a, b)
    assert "A_Sun_Triggers_B_Chiron" in result["shadow_tags"]
    assert "A_Moon_Triggers_B_Chiron" in result["shadow_tags"]
    assert "A_Venus_Triggers_B_Chiron" in result["shadow_tags"]
    assert "A_Mars_Triggers_B_Chiron" in result["shadow_tags"]
    # soul_mod: 4 triggers × 15 = 60; lust_mod: Mars only × 10 = 10
    assert result["soul_mod"] == pytest.approx(60.0)
    assert result["lust_mod"] == pytest.approx(10.0)


def test_no_chiron_b_no_trigger_for_a_planets():
    """No chiron_b → A's planets cannot trigger anything."""
    a = {"sun_degree": 50.0, "moon_degree": 50.0, "venus_degree": 50.0, "mars_degree": 50.0}
    b = {}   # no chiron_degree
    result = compute_shadow_and_wound(a, b)
    assert result["soul_mod"] == 0.0
    assert result["lust_mod"] == 0.0
    assert result["shadow_tags"] == []


def test_no_chiron_a_no_trigger_for_b_planets():
    """No chiron_a → B's planets cannot trigger anything."""
    a = {}   # no chiron_degree
    b = {"sun_degree": 50.0, "moon_degree": 50.0, "venus_degree": 50.0, "mars_degree": 50.0}
    result = compute_shadow_and_wound(a, b)
    assert result["soul_mod"] == 0.0
    assert result["lust_mod"] == 0.0
    assert result["shadow_tags"] == []


# ── Moon-Pluto cross-aspect trigger (L-6) ──────────────────────────────────────

def test_pluto_conjunct_moon_triggers_ab():
    """A's Pluto conjunct B's Moon (diff=3° ≤ 5°) → A_Pluto_Wounds_B_Moon + soul +15, lust +10, high_voltage."""
    a = {"pluto_degree": 100.0}
    b = {"moon_degree": 103.0}   # diff=3° → conjunction
    result = compute_shadow_and_wound(a, b)
    assert "A_Pluto_Wounds_B_Moon" in result["shadow_tags"]
    assert result["soul_mod"] == pytest.approx(15.0)
    assert result["lust_mod"] == pytest.approx(10.0)
    assert result["high_voltage"] is True


def test_pluto_conjunct_moon_triggers_ba():
    """B's Pluto conjunct A's Moon (diff=0°) → B_Pluto_Wounds_A_Moon + soul +15, lust +10."""
    a = {"moon_degree": 200.0}
    b = {"pluto_degree": 200.0}   # diff=0° exact conjunction
    result = compute_shadow_and_wound(a, b)
    assert "B_Pluto_Wounds_A_Moon" in result["shadow_tags"]
    assert result["soul_mod"] == pytest.approx(15.0)
    assert result["lust_mod"] == pytest.approx(10.0)
    assert result["high_voltage"] is True


def test_pluto_square_moon_triggers():
    """A's Pluto square B's Moon (diff=90°, ≤ 5° orb) → A_Pluto_Wounds_B_Moon."""
    a = {"pluto_degree": 0.0}
    b = {"moon_degree": 90.0}   # exact square
    result = compute_shadow_and_wound(a, b)
    assert "A_Pluto_Wounds_B_Moon" in result["shadow_tags"]
    assert result["soul_mod"] == pytest.approx(15.0)
    assert result["high_voltage"] is True


def test_pluto_oppose_moon_triggers():
    """A's Pluto oppose B's Moon (diff=180°) → A_Pluto_Wounds_B_Moon."""
    a = {"pluto_degree": 0.0}
    b = {"moon_degree": 180.0}   # exact opposition
    result = compute_shadow_and_wound(a, b)
    assert "A_Pluto_Wounds_B_Moon" in result["shadow_tags"]
    assert result["soul_mod"] == pytest.approx(15.0)
    assert result["high_voltage"] is True


def test_pluto_moon_orb_outside_no_trigger():
    """A's Pluto at 6° from B's Moon (tighter than square/oppose) → no trigger."""
    a = {"pluto_degree": 0.0}
    b = {"moon_degree": 6.0}   # diff=6° > 5° → no conjunction trigger
    result = compute_shadow_and_wound(a, b)
    assert "A_Pluto_Wounds_B_Moon" not in result["shadow_tags"]
    assert result["soul_mod"] == pytest.approx(0.0)


def test_pluto_moon_bidirectional_both_trigger():
    """Both A's Pluto conjunct B's Moon and B's Pluto conjunct A's Moon → both tags, soul_mod=30."""
    a = {"pluto_degree": 100.0, "moon_degree": 200.0}
    b = {"pluto_degree": 203.0, "moon_degree": 102.0}
    result = compute_shadow_and_wound(a, b)
    assert "A_Pluto_Wounds_B_Moon" in result["shadow_tags"]
    assert "B_Pluto_Wounds_A_Moon" in result["shadow_tags"]
    assert result["soul_mod"] == pytest.approx(30.0)
    assert result["lust_mod"] == pytest.approx(20.0)


def test_pluto_moon_missing_pluto_no_trigger():
    """No pluto_degree in chart_a → A_Pluto_Wounds_B_Moon should not trigger."""
    a = {}   # no pluto_degree
    b = {"moon_degree": 100.0}
    result = compute_shadow_and_wound(a, b)
    assert "A_Pluto_Wounds_B_Moon" not in result["shadow_tags"]


def test_pluto_moon_missing_moon_no_trigger():
    """No moon_degree in chart_b → A_Pluto_Wounds_B_Moon should not trigger."""
    a = {"pluto_degree": 100.0}
    b = {}   # no moon_degree
    result = compute_shadow_and_wound(a, b)
    assert "A_Pluto_Wounds_B_Moon" not in result["shadow_tags"]


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
    chart_b = {"uranus_degree": 10.0}    # diff=40° — no aspect (orb 5°)
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


# ── TestVertexLilithTriggers ──────────────────────────────────────────────────

class TestVertexLilithTriggers:
    """Tests for Vertex (命運之門) and Lilith (禁忌之戀) synastry triggers."""

    def test_a_sun_conjunct_vertex_b_triggers_soul_mod(self):
        """A's Sun within 3° of B's Vertex → soul_mod += 25, tag present, no high_voltage."""
        a = {"sun_degree": 100.0}
        b = {"vertex_degree": 102.0}   # diff=2° ≤ 3°
        result = compute_shadow_and_wound(a, b)
        assert result["soul_mod"] == pytest.approx(25.0)
        assert "A_Sun_Conjunct_Vertex" in result["shadow_tags"]
        assert result["high_voltage"] is False
        assert result["lust_mod"] == pytest.approx(0.0)

    def test_a_venus_conjunct_lilith_b_triggers_lust_mod(self):
        """A's Venus within 3° of B's Lilith → lust_mod += 25, high_voltage=True, tag present."""
        a = {"venus_degree": 200.0}
        b = {"lilith_degree": 201.5}   # diff=1.5° ≤ 3°
        result = compute_shadow_and_wound(a, b)
        assert result["lust_mod"] == pytest.approx(25.0)
        assert result["high_voltage"] is True
        assert "A_Venus_Conjunct_Lilith" in result["shadow_tags"]
        assert result["soul_mod"] == pytest.approx(0.0)

    def test_a_mars_conjunct_lilith_b_triggers_lust_mod(self):
        """A's Mars within 3° of B's Lilith → lust_mod += 25, high_voltage=True."""
        a = {"mars_degree": 50.0}
        b = {"lilith_degree": 50.0}   # diff=0° exact conjunction
        result = compute_shadow_and_wound(a, b)
        assert result["lust_mod"] == pytest.approx(25.0)
        assert result["high_voltage"] is True
        assert "A_Mars_Conjunct_Lilith" in result["shadow_tags"]

    def test_vertex_orb_4deg_no_trigger(self):
        """A's Sun 4° from B's Vertex → outside the 3° orb → no Vertex tag triggered."""
        a = {"sun_degree": 100.0}
        b = {"vertex_degree": 104.0}   # diff=4° > 3°
        result = compute_shadow_and_wound(a, b)
        assert "A_Sun_Conjunct_Vertex" not in result["shadow_tags"]
        assert result["soul_mod"] == pytest.approx(0.0)

    def test_lilith_orb_4deg_no_trigger(self):
        """A's Venus 4° from B's Lilith → outside the 3° orb → no Lilith tag triggered."""
        a = {"venus_degree": 100.0}
        b = {"lilith_degree": 104.0}   # diff=4° > 3°
        result = compute_shadow_and_wound(a, b)
        assert "A_Venus_Conjunct_Lilith" not in result["shadow_tags"]
        assert result["lust_mod"] == pytest.approx(0.0)
        assert result["high_voltage"] is False

    def test_mars_does_not_trigger_vertex(self):
        """A's Mars near B's Vertex → Mars is NOT in Vertex planet list → no Vertex tag."""
        a = {"mars_degree": 100.0}
        b = {"vertex_degree": 101.0}   # diff=1° ≤ 3°, but Mars excluded from Vertex
        result = compute_shadow_and_wound(a, b)
        assert "A_Mars_Conjunct_Vertex" not in result["shadow_tags"]
        # No Vertex soul_mod from Mars
        assert result["soul_mod"] == pytest.approx(0.0)

    def test_sun_does_not_trigger_lilith(self):
        """A's Sun near B's Lilith → Sun is NOT in Lilith planet list → no Lilith tag."""
        a = {"sun_degree": 300.0}
        b = {"lilith_degree": 300.5}   # diff=0.5° ≤ 3°, but Sun excluded from Lilith
        result = compute_shadow_and_wound(a, b)
        assert "A_Sun_Conjunct_Lilith" not in result["shadow_tags"]
        assert result["lust_mod"] == pytest.approx(0.0)
        assert result["high_voltage"] is False

    def test_vertex_lilith_bidirectional(self):
        """B's Venus within 3° of A's Lilith → B_Venus_Conjunct_Lilith tag, lust_mod += 25."""
        a = {"lilith_degree": 150.0}
        b = {"venus_degree": 152.0}   # diff=2° ≤ 3°
        result = compute_shadow_and_wound(a, b)
        assert result["lust_mod"] == pytest.approx(25.0)
        assert result["high_voltage"] is True
        assert "B_Venus_Conjunct_Lilith" in result["shadow_tags"]


# ── TestLunarNodeTriggers ─────────────────────────────────────────────────────

class TestLunarNodeTriggers:
    """Tests for Lunar Node (南北交點) synastry triggers."""

    def test_south_node_trigger_high_voltage(self):
        """A's Sun conjunct B's South Node (diff=2° ≤ 3°) → soul_mod +20, high_voltage."""
        a = {"sun_degree": 100.0}
        b = {"south_node_degree": 102.0}
        result = compute_shadow_and_wound(a, b)
        assert result["soul_mod"] >= 20.0
        assert result["high_voltage"] is True
        assert "A_Sun_Conjunct_SouthNode" in result["shadow_tags"]

    def test_north_node_trigger_no_high_voltage(self):
        """A's Moon conjunct B's North Node (diff=1° ≤ 3°) → soul_mod +20, no high_voltage."""
        a = {"moon_degree": 200.0}
        b = {"north_node_degree": 201.0}
        result = compute_shadow_and_wound(a, b)
        assert result["soul_mod"] >= 20.0
        assert result["high_voltage"] is False
        assert "A_Moon_Conjunct_NorthNode" in result["shadow_tags"]

    def test_node_trigger_outside_orb_no_effect(self):
        """A's Venus 5° from B's South Node → outside 3° orb → no trigger."""
        a = {"venus_degree": 100.0}
        b = {"south_node_degree": 105.0}   # diff=5° > 3°
        result = compute_shadow_and_wound(a, b)
        assert "A_Venus_Conjunct_SouthNode" not in result["shadow_tags"]
        assert result["soul_mod"] == pytest.approx(0.0)
        assert result["high_voltage"] is False

    def test_missing_node_skipped_gracefully(self):
        """Missing south_node_degree → no crash, no trigger."""
        a = {"sun_degree": 50.0, "moon_degree": 50.0}
        b = {}   # no node fields
        result = compute_shadow_and_wound(a, b)
        # No node tags should be present
        node_tags = [t for t in result["shadow_tags"] if "Node" in t]
        assert node_tags == []


class TestDescendantOverlay:
    """Tests for 7th House Overlay (Descendant) triggers."""

    def test_sun_conjunct_descendant_triggers(self):
        """A's Sun conjunct B's DSC (= B's ASC + 180°) within 5° → partner_mod + soul_mod."""
        a = {"sun_degree": 190.0}  # close to DSC of B
        b = {"ascendant_degree": 10.0}  # DSC = 190°
        result = compute_shadow_and_wound(a, b)
        assert result["partner_mod"] == 20.0
        assert result["soul_mod"] >= 10.0
        assert "A_Sun_Conjunct_Descendant" in result["shadow_tags"]

    def test_descendant_outside_orb(self):
        """A's Sun 8° from DSC → no trigger (orb = 5°)."""
        a = {"sun_degree": 198.0}  # 8° from DSC=190
        b = {"ascendant_degree": 10.0}
        result = compute_shadow_and_wound(a, b)
        assert result["partner_mod"] == 0.0
        dsc_tags = [t for t in result["shadow_tags"] if "Descendant" in t]
        assert dsc_tags == []

    def test_missing_ascendant_graceful(self):
        """Without ascendant_degree, Descendant overlay is skipped gracefully."""
        a = {"sun_degree": 190.0, "moon_degree": 50.0}
        b = {}  # no ascendant
        result = compute_shadow_and_wound(a, b)
        dsc_tags = [t for t in result["shadow_tags"] if "Descendant" in t]
        assert dsc_tags == []

    def test_partner_mod_always_in_result(self):
        """partner_mod key must exist in result even with empty charts."""
        result = compute_shadow_and_wound({}, {})
        assert "partner_mod" in result
        assert result["partner_mod"] == 0.0


# ── L-9: Saturn-Moon cross-aspect trigger (壓抑型依賴) ───────────────────────

class TestSaturnMoonTrigger:
    """Saturn hard-aspects Moon: conjunction / square / opposition within 5° orb.
    soul_mod +10, partner_mod -15 per trigger. No high_voltage (cold suppression).
    """

    def test_conjunction_a_saturn_b_moon(self):
        """A's Saturn 2° from B's Moon → conjunction trigger: soul +10, partner -15."""
        a = {"saturn_degree": 50.0}
        b = {"moon_degree": 52.0}
        r = compute_shadow_and_wound(a, b)
        assert r["soul_mod"] == pytest.approx(10.0)
        assert r["partner_mod"] == pytest.approx(-15.0)
        assert r["high_voltage"] is False
        assert "A_Saturn_Suppresses_B_Moon" in r["shadow_tags"]

    def test_square_a_saturn_b_moon(self):
        """A's Saturn 90° from B's Moon (diff 3° from square) → triggers."""
        a = {"saturn_degree": 0.0}
        b = {"moon_degree": 93.0}   # 93° from 0° → 3° from square
        r = compute_shadow_and_wound(a, b)
        assert r["soul_mod"] == pytest.approx(10.0)
        assert r["partner_mod"] == pytest.approx(-15.0)
        assert "A_Saturn_Suppresses_B_Moon" in r["shadow_tags"]

    def test_opposition_a_saturn_b_moon(self):
        """A's Saturn 180° from B's Moon (exact opposition) → triggers."""
        a = {"saturn_degree": 10.0}
        b = {"moon_degree": 190.0}
        r = compute_shadow_and_wound(a, b)
        assert r["soul_mod"] == pytest.approx(10.0)
        assert r["partner_mod"] == pytest.approx(-15.0)
        assert "A_Saturn_Suppresses_B_Moon" in r["shadow_tags"]

    def test_bidirectional_b_saturn_a_moon(self):
        """B's Saturn 3° from A's Moon → B_Saturn_Suppresses_A_Moon fires."""
        a = {"moon_degree": 100.0}
        b = {"saturn_degree": 103.0}
        r = compute_shadow_and_wound(a, b)
        assert r["soul_mod"] == pytest.approx(10.0)
        assert r["partner_mod"] == pytest.approx(-15.0)
        assert "B_Saturn_Suppresses_A_Moon" in r["shadow_tags"]

    def test_outside_orb_not_triggered(self):
        """A's Saturn 8° from B's Moon (> 5° orb) → no trigger."""
        a = {"saturn_degree": 0.0}
        b = {"moon_degree": 8.0}
        r = compute_shadow_and_wound(a, b)
        assert r["soul_mod"] == pytest.approx(0.0)
        assert r["partner_mod"] == pytest.approx(0.0)
        assert "A_Saturn_Suppresses_B_Moon" not in r["shadow_tags"]

    def test_missing_saturn_no_trigger(self):
        """Without saturn_degree, trigger is skipped gracefully."""
        a = {}
        b = {"moon_degree": 50.0}
        r = compute_shadow_and_wound(a, b)
        assert r["partner_mod"] == pytest.approx(0.0)
        saturn_tags = [t for t in r["shadow_tags"] if "Saturn" in t]
        assert saturn_tags == []

    def test_missing_moon_no_trigger(self):
        """Without moon_degree, trigger is skipped gracefully."""
        a = {"saturn_degree": 50.0}
        b = {}
        r = compute_shadow_and_wound(a, b)
        assert r["partner_mod"] == pytest.approx(0.0)
        saturn_tags = [t for t in r["shadow_tags"] if "Saturn" in t]
        assert saturn_tags == []


class TestSaturnVenusTrigger:
    """ALGORITHM.md L-7: Saturn-Venus cross-aspect — karmic obligation binding."""

    def test_conjunction_a_saturn_b_venus(self):
        """A's Saturn conjunct B's Venus → soul +8, partner -10, lust -5, tag."""
        a = {"saturn_degree": 50.0}
        b = {"venus_degree": 52.0}   # 2° apart → within 5° orb
        r = compute_shadow_and_wound(a, b)
        assert r["soul_mod"]    == pytest.approx(8.0)
        assert r["partner_mod"] == pytest.approx(-10.0)
        assert r["lust_mod"]    == pytest.approx(-5.0)
        assert "A_Saturn_Binds_B_Venus" in r["shadow_tags"]

    def test_square_a_saturn_b_venus(self):
        """A's Saturn square B's Venus (90° ± 5°) → triggers."""
        a = {"saturn_degree": 0.0}
        b = {"venus_degree": 93.0}   # 3° off square
        r = compute_shadow_and_wound(a, b)
        assert r["soul_mod"]    == pytest.approx(8.0)
        assert "A_Saturn_Binds_B_Venus" in r["shadow_tags"]

    def test_opposition_a_saturn_b_venus(self):
        """A's Saturn oppose B's Venus (180° ± 5°) → triggers."""
        a = {"saturn_degree": 10.0}
        b = {"venus_degree": 188.0}   # 178° apart — diff from 180° = 2°
        r = compute_shadow_and_wound(a, b)
        assert r["soul_mod"]    == pytest.approx(8.0)
        assert "A_Saturn_Binds_B_Venus" in r["shadow_tags"]

    def test_bidirectional_b_saturn_a_venus(self):
        """B's Saturn binds A's Venus → symmetric bidirectional trigger."""
        a = {"venus_degree": 50.0}
        b = {"saturn_degree": 52.0}
        r = compute_shadow_and_wound(a, b)
        assert r["soul_mod"]    == pytest.approx(8.0)
        assert r["partner_mod"] == pytest.approx(-10.0)
        assert r["lust_mod"]    == pytest.approx(-5.0)
        assert "B_Saturn_Binds_A_Venus" in r["shadow_tags"]

    def test_outside_orb_not_triggered(self):
        """6° off conjunction — outside 5° orb — no trigger."""
        a = {"saturn_degree": 0.0}
        b = {"venus_degree": 6.1}
        r = compute_shadow_and_wound(a, b)
        assert r["soul_mod"]    == pytest.approx(0.0)
        assert r["lust_mod"]    == pytest.approx(0.0)
        assert "A_Saturn_Binds_B_Venus" not in r["shadow_tags"]

    def test_missing_venus_no_trigger(self):
        """Without venus_degree, trigger is skipped gracefully."""
        a = {"saturn_degree": 50.0}
        b = {}
        r = compute_shadow_and_wound(a, b)
        venus_tags = [t for t in r["shadow_tags"] if "Venus" in t and "Saturn" in t]
        assert venus_tags == []

    def test_missing_saturn_no_trigger(self):
        """Without saturn_degree, trigger is skipped gracefully."""
        a = {}
        b = {"venus_degree": 50.0}
        r = compute_shadow_and_wound(a, b)
        venus_tags = [t for t in r["shadow_tags"] if "Venus" in t and "Saturn" in t]
        assert venus_tags == []


# ── TestJungianShiftPartnerMod ─────────────────────────────────────────────────

class TestJungianShiftPartnerMod:
    """Sprint 1: Jungian Shift — partner_mod deductions on karmic triggers.

    High-tension triggers add soul/lust bonuses but must also subtract partner_mod
    to reflect the daily friction cost of high-voltage relationships.
    """

    def test_chiron_nonmars_partner_mod(self):
        """Non-Mars planet (Sun) conjunct Chiron → partner_mod == -10."""
        a = {"sun_degree": 50.0}
        b = {"chiron_degree": 50.0}   # exact conjunction
        r = compute_shadow_and_wound(a, b)
        assert "A_Sun_Triggers_B_Chiron" in r["shadow_tags"]
        assert r["partner_mod"] == pytest.approx(-10.0)

    def test_chiron_mars_partner_mod(self):
        """Mars conjunct Chiron → partner_mod == -15 (higher penalty for Mars volatility)."""
        a = {"mars_degree": 100.0}
        b = {"chiron_degree": 100.0}   # exact conjunction
        r = compute_shadow_and_wound(a, b)
        assert "A_Mars_Triggers_B_Chiron" in r["shadow_tags"]
        assert r["partner_mod"] == pytest.approx(-15.0)

    def test_south_node_partner_mod(self):
        """Sun conjunct South Node → partner_mod == -15 (karmic debt pull)."""
        a = {"sun_degree": 200.0}
        b = {"south_node_degree": 201.0}   # 1° diff ≤ 3° orb
        r = compute_shadow_and_wound(a, b)
        assert "A_Sun_Conjunct_SouthNode" in r["shadow_tags"]
        assert r["partner_mod"] == pytest.approx(-15.0)

    def test_12th_house_single_direction_partner_mod(self):
        """One-directional 12th house overlay (A's Sun in B's 12th) → partner_mod == -10."""
        a = {"sun_degree": 200.0}
        b = {"house12_degree": 195.0, "ascendant_degree": 225.0}   # 12th: 195→225
        r = compute_shadow_and_wound(a, b)
        assert "A_Illuminates_B_Shadow" in r["shadow_tags"]
        assert "Mutual_Shadow_Integration" not in r["shadow_tags"]
        assert r["partner_mod"] == pytest.approx(-10.0)

    def test_mutual_shadow_partner_mod(self):
        """Both-directional 12th overlay → partner_mod == -10 + -10 + -20 == -40."""
        # A's sun at 200° is in B's 12th (193→223); B's sun at 195° is in A's 12th (188→218)
        a = {"sun_degree": 200.0, "house12_degree": 188.0, "ascendant_degree": 218.0}
        b = {"sun_degree": 195.0, "house12_degree": 193.0, "ascendant_degree": 223.0}
        r = compute_shadow_and_wound(a, b)
        assert "A_Illuminates_B_Shadow" in r["shadow_tags"]
        assert "B_Illuminates_A_Shadow" in r["shadow_tags"]
        assert "Mutual_Shadow_Integration" in r["shadow_tags"]
        assert r["partner_mod"] == pytest.approx(-40.0)

    def test_lilith_partner_mod(self):
        """Venus conjunct Lilith → partner_mod == -10 (taboo lust friction cost)."""
        a = {"venus_degree": 300.0}
        b = {"lilith_degree": 300.0}   # exact conjunction
        r = compute_shadow_and_wound(a, b)
        assert "A_Venus_Conjunct_Lilith" in r["shadow_tags"]
        assert r["partner_mod"] == pytest.approx(-10.0)


# ── compute_attachment_dynamics: fearful-avoidant alias ──────────────────────

def test_fearful_avoidant_alias_gives_chaotic_oscillation():
    """'fearful-avoidant' must be aliased to 'fearful' → Chaotic_Oscillation."""
    from shadow_engine import compute_attachment_dynamics
    r = compute_attachment_dynamics("fearful-avoidant", "anxious")
    assert r["trap_tag"] == "Chaotic_Oscillation"
    assert r["high_voltage"] is True


def test_fearful_avoidant_same_as_fearful():
    """'fearful-avoidant' and 'fearful' must produce identical results."""
    from shadow_engine import compute_attachment_dynamics
    r_hyphen = compute_attachment_dynamics("fearful-avoidant", "avoidant")
    r_direct = compute_attachment_dynamics("fearful", "avoidant")
    assert r_hyphen["trap_tag"] == r_direct["trap_tag"]
    assert r_hyphen["high_voltage"] == r_direct["high_voltage"]


# ── Ascendant Magnetism triggers ──────────────────────────────────────────────

def test_mars_a_activates_asc_b_conjunction():
    """A's Mars conjunct B's ASC (1°) → A_Mars_Activates_B_Ascendant + lust_mod +5."""
    a = {"mars_degree": 100.0}
    b = {"ascendant_degree": 101.0}   # diff=1°, strength=0.80 >= 0.75
    r = compute_shadow_and_wound(a, b)
    assert "A_Mars_Activates_B_Ascendant" in r["shadow_tags"]
    assert r["lust_mod"] >= 5.0


def test_mars_a_activates_asc_b_square():
    """A's Mars square B's ASC (91°) → triggers tension aspect."""
    a = {"mars_degree": 100.0}
    b = {"ascendant_degree": 191.0}   # |91-90|=1°, strength=0.80
    r = compute_shadow_and_wound(a, b)
    assert "A_Mars_Activates_B_Ascendant" in r["shadow_tags"]


def test_mars_a_no_tag_at_exact_orb_boundary():
    """A's Mars exactly 5° from B's ASC → strength=0.0 < threshold → no tag."""
    a = {"mars_degree": 100.0}
    b = {"ascendant_degree": 105.0}   # diff=5°, strength=1-(5/5)=0.0
    r = compute_shadow_and_wound(a, b)
    assert "A_Mars_Activates_B_Ascendant" not in r["shadow_tags"]


def test_venus_a_matches_asc_b_conjunction():
    """A's Venus conjunct B's ASC (0.5°) → A_Venus_Matches_B_Ascendant + lust_mod +3."""
    a = {"venus_degree": 200.0}
    b = {"ascendant_degree": 200.5}   # strength=0.90
    r = compute_shadow_and_wound(a, b)
    assert "A_Venus_Matches_B_Ascendant" in r["shadow_tags"]
    assert r["lust_mod"] >= 3.0


def test_venus_b_matches_asc_a_trine():
    """B's Venus trine A's ASC (119°) → B_Venus_Matches_A_Ascendant."""
    a = {"ascendant_degree": 169.0}
    b = {"venus_degree": 50.0}        # |119-120|=1°, strength=0.80
    r = compute_shadow_and_wound(a, b)
    assert "B_Venus_Matches_A_Ascendant" in r["shadow_tags"]


def test_asc_magnetism_bidirectional_independent():
    """Both A_Mars→B_ASC and B_Venus→A_ASC fire simultaneously."""
    a = {"mars_degree": 100.0, "ascendant_degree": 300.0}
    b = {"ascendant_degree": 101.0, "venus_degree": 299.5}
    r = compute_shadow_and_wound(a, b)
    assert "A_Mars_Activates_B_Ascendant" in r["shadow_tags"]
    assert "B_Venus_Matches_A_Ascendant" in r["shadow_tags"]
    assert r["lust_mod"] >= 8.0   # 5.0 + 3.0


def test_asc_magnetism_missing_degrees_no_crash():
    """No degrees provided → no tags, no crash."""
    r = compute_shadow_and_wound({}, {})
    assert "A_Mars_Activates_B_Ascendant" not in r["shadow_tags"]
    assert "B_Mars_Activates_A_Ascendant" not in r["shadow_tags"]
