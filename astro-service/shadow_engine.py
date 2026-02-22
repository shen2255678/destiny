"""
DESTINY Shadow & Wound Engine + Attachment Dynamics
Pairwise match-time modifier functions for compute_match_v2().
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple


def _dist(a, b):
    if a is None or b is None:
        return None
    d = abs(a - b)
    return min(d, 360.0 - d)


def _conj(a, b, orb=8.0):
    d = _dist(a, b)
    return d is not None and d <= orb


def _tension(a, b, orb=8.0):
    d = _dist(a, b)
    if d is None:
        return False
    return d <= orb or abs(d - 90.0) <= orb or abs(d - 180.0) <= orb


def _harmony(a, b, orb=8.0):
    d = _dist(a, b)
    if d is None:
        return False
    return d <= orb or abs(d - 120.0) <= orb


def _in_house(planet_deg, cusp_deg, next_cusp_deg):
    if planet_deg is None or cusp_deg is None or next_cusp_deg is None:
        return False
    house_size = (next_cusp_deg - cusp_deg) % 360.0
    planet_rel = (planet_deg - cusp_deg) % 360.0
    return planet_rel < house_size


def compute_shadow_and_wound(chart_a, chart_b):
    result = {
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

    if _conj(chiron_a, moon_b):
        result["soul_mod"] += 25.0
        result["shadow_tags"].append("A_Heals_B_Moon")
    if _conj(chiron_b, moon_a):
        result["soul_mod"] += 25.0
        result["shadow_tags"].append("B_Heals_A_Moon")
    if chiron_a is not None and mars_b is not None:
        d = _dist(chiron_a, mars_b)
        if d is not None and (abs(d - 90.0) <= 8.0 or abs(d - 180.0) <= 8.0):
            result["lust_mod"] += 15.0
            result["high_voltage"] = True
            result["shadow_tags"].append("B_Triggers_A_Wound")
    if chiron_b is not None and mars_a is not None:
        d = _dist(chiron_b, mars_a)
        if d is not None and (abs(d - 90.0) <= 8.0 or abs(d - 180.0) <= 8.0):
            result["lust_mod"] += 15.0
            result["high_voltage"] = True
            result["shadow_tags"].append("A_Triggers_B_Wound")
    a_in_b12 = _in_house(sun_a, h12_b, asc_b) or _in_house(mars_a, h12_b, asc_b)
    if a_in_b12:
        result["soul_mod"] += 20.0
        result["high_voltage"] = True
        result["shadow_tags"].append("A_Illuminates_B_Shadow")
    b_in_a12 = _in_house(sun_b, h12_a, asc_a) or _in_house(mars_b, h12_a, asc_a)
    if b_in_a12:
        result["soul_mod"] += 20.0
        result["high_voltage"] = True
        result["shadow_tags"].append("B_Illuminates_A_Shadow")
    if a_in_b12 and b_in_a12:
        result["soul_mod"] += 40.0
        result["shadow_tags"].append("Mutual_Shadow_Integration")
    return result


def compute_dynamic_attachment(base_att_a, base_att_b, chart_a, chart_b):
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
    if _tension(moon_a, uranus_b):
        dyn_a = "anxious"
    elif _tension(moon_a, saturn_b) or _conj(moon_a, saturn_b):
        dyn_a = "avoidant"
    elif _harmony(moon_a, jupiter_b) or _harmony(moon_a, venus_b):
        dyn_a = "secure"
    if _tension(moon_b, uranus_a):
        dyn_b = "anxious"
    elif _tension(moon_b, saturn_a) or _conj(moon_b, saturn_a):
        dyn_b = "avoidant"
    elif _harmony(moon_b, jupiter_a) or _harmony(moon_b, venus_a):
        dyn_b = "secure"
    return dyn_a, dyn_b


def compute_attachment_dynamics(att_a, att_b):
    _alias = {"disorganized": "fearful"}
    a = _alias.get((att_a or "secure").lower(), (att_a or "secure").lower())
    b = _alias.get((att_b or "secure").lower(), (att_b or "secure").lower())
    pair = tuple(sorted([a, b]))
    result = {
        "soul_mod": 0.0,
        "partner_mod": 0.0,
        "lust_mod": 0.0,
        "high_voltage": False,
        "trap_tag": None,
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
    elif "secure" in pair:
        result.update(soul_mod=10.0, partner_mod=10.0, trap_tag="Healing_Anchor")
    return result


_FULFILLMENT_PER_MATCH = 15.0
_FULFILLMENT_CAP       = 30.0


def compute_elemental_fulfillment(profile_a, profile_b):
    def_a = set(profile_a.get("deficiency") or [])
    dom_b = set(profile_b.get("dominant")   or [])
    def_b = set(profile_b.get("deficiency") or [])
    dom_a = set(profile_a.get("dominant")   or [])
    matches = len(def_a & dom_b) + len(def_b & dom_a)
    bonus   = matches * _FULFILLMENT_PER_MATCH
    return min(bonus, _FULFILLMENT_CAP)
