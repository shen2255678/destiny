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


def _conj(a, b, orb=5.0):
    d = _dist(a, b)
    return d is not None and d <= orb


def _tension(a, b, orb=5.0):
    d = _dist(a, b)
    if d is None:
        return False
    return d <= orb or abs(d - 90.0) <= orb or abs(d - 180.0) <= orb


def _harmony(a, b, orb=5.0):
    d = _dist(a, b)
    if d is None:
        return False
    return d <= orb or abs(d - 120.0) <= orb


# Orb for Chiron wound triggers (conjunction or opposition only)
_CHIRON_ORB = 5.0

# Orb for Vertex (命運之門) and Lilith (禁忌之戀) triggers (conjunction only)
_VERTEX_LILITH_ORB = 3.0

# Planets checked against partner's Vertex (fate/soul trigger — not volatile; no high_voltage)
_VERTEX_PLANETS = [("Sun", "sun_degree"), ("Moon", "moon_degree"), ("Venus", "venus_degree")]
# Planets checked against partner's Lilith (taboo lust trigger; sets high_voltage)
_LILITH_PLANETS = [("Venus", "venus_degree"), ("Mars", "mars_degree")]


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
        "partner_mod": 0.0,
        "high_voltage": False,
        "shadow_tags": [],
    }
    chiron_a = chart_a.get("chiron_degree")
    chiron_b = chart_b.get("chiron_degree")
    lilith_a = chart_a.get("lilith_degree")
    lilith_b = chart_b.get("lilith_degree")
    vertex_a = chart_a.get("vertex_degree")
    vertex_b = chart_b.get("vertex_degree")
    h12_a    = chart_a.get("house12_degree")
    asc_a    = chart_a.get("ascendant_degree")
    h12_b    = chart_b.get("house12_degree")
    asc_b    = chart_b.get("ascendant_degree")

    # Personal planets: Sun/Moon/Venus/Mars
    planets_a = [
        ("Sun",   chart_a.get("sun_degree")),
        ("Moon",  chart_a.get("moon_degree")),
        ("Venus", chart_a.get("venus_degree")),
        ("Mars",  chart_a.get("mars_degree")),
    ]
    planets_b = [
        ("Sun",   chart_b.get("sun_degree")),
        ("Moon",  chart_b.get("moon_degree")),
        ("Venus", chart_b.get("venus_degree")),
        ("Mars",  chart_b.get("mars_degree")),
    ]

    # A's personal planets conjunct/oppose B's Chiron → wound trigger
    if chiron_b is not None:
        for p_name, p_deg in planets_a:
            d = _dist(p_deg, chiron_b)
            if d is not None and (d <= _CHIRON_ORB or abs(d - 180.0) <= _CHIRON_ORB):
                result["soul_mod"] += 15.0
                if p_name == "Mars":
                    result["lust_mod"] += 10.0
                result["high_voltage"] = True
                result["shadow_tags"].append(f"A_{p_name}_Triggers_B_Chiron")

    # B's personal planets conjunct/oppose A's Chiron → wound trigger
    if chiron_a is not None:
        for p_name, p_deg in planets_b:
            d = _dist(p_deg, chiron_a)
            if d is not None and (d <= _CHIRON_ORB or abs(d - 180.0) <= _CHIRON_ORB):
                result["soul_mod"] += 15.0
                if p_name == "Mars":
                    result["lust_mod"] += 10.0
                result["high_voltage"] = True
                result["shadow_tags"].append(f"B_{p_name}_Triggers_A_Chiron")

    # Moon-Pluto cross-aspect (靈魂深淵 / 執念侵蝕): Pluto conjunct/square/oppose Moon
    # A's Pluto forming a hard aspect to B's Moon → obsession + soul erosion + HIGH_VOLTAGE
    _PLUTO_MOON_ORB = 5.0
    pluto_a = chart_a.get("pluto_degree")
    pluto_b = chart_b.get("pluto_degree")
    moon_deg_a = chart_a.get("moon_degree")
    moon_deg_b = chart_b.get("moon_degree")
    if pluto_a is not None and moon_deg_b is not None:
        d = _dist(pluto_a, moon_deg_b)
        if d is not None and (d <= _PLUTO_MOON_ORB or abs(d - 90.0) <= _PLUTO_MOON_ORB or abs(d - 180.0) <= _PLUTO_MOON_ORB):
            result["soul_mod"] += 15.0
            result["lust_mod"] += 10.0
            result["high_voltage"] = True
            result["shadow_tags"].append("A_Pluto_Wounds_B_Moon")
    if pluto_b is not None and moon_deg_a is not None:
        d = _dist(pluto_b, moon_deg_a)
        if d is not None and (d <= _PLUTO_MOON_ORB or abs(d - 90.0) <= _PLUTO_MOON_ORB or abs(d - 180.0) <= _PLUTO_MOON_ORB):
            result["soul_mod"] += 15.0
            result["lust_mod"] += 10.0
            result["high_voltage"] = True
            result["shadow_tags"].append("B_Pluto_Wounds_A_Moon")

    # Saturn-Moon cross-aspect (壓抑型依賴): Saturn conjunct/square/oppose Moon
    # A's Saturn forming a hard aspect to B's Moon → karmic emotional suppression.
    # Saturn restricts and structures B's emotional expression; creates dependency
    # through control but undermines long-term partner satisfaction.
    # soul_mod +10 (karmic bond), partner_mod -15 (emotional suppression penalty).
    # Not high_voltage — this is cold structural pressure, not explosive.
    _SATURN_MOON_ORB = 5.0
    saturn_a = chart_a.get("saturn_degree")
    saturn_b = chart_b.get("saturn_degree")
    if saturn_a is not None and moon_deg_b is not None:
        d = _dist(saturn_a, moon_deg_b)
        if d is not None and (d <= _SATURN_MOON_ORB or abs(d - 90.0) <= _SATURN_MOON_ORB or abs(d - 180.0) <= _SATURN_MOON_ORB):
            result["soul_mod"]    += 10.0
            result["partner_mod"] -= 15.0
            result["shadow_tags"].append("A_Saturn_Suppresses_B_Moon")
    if saturn_b is not None and moon_deg_a is not None:
        d = _dist(saturn_b, moon_deg_a)
        if d is not None and (d <= _SATURN_MOON_ORB or abs(d - 90.0) <= _SATURN_MOON_ORB or abs(d - 180.0) <= _SATURN_MOON_ORB):
            result["soul_mod"]    += 10.0
            result["partner_mod"] -= 15.0
            result["shadow_tags"].append("B_Saturn_Suppresses_A_Moon")

    # Vertex triggers (命運之門): Sun/Moon/Venus conjunction only, soul_mod +25 each
    if vertex_b is not None:
        for p_name, p_key in _VERTEX_PLANETS:
            d = _dist(chart_a.get(p_key), vertex_b)
            if d is not None and d <= _VERTEX_LILITH_ORB:
                result["soul_mod"] += 25.0
                result["shadow_tags"].append(f"A_{p_name}_Conjunct_Vertex")
    if vertex_a is not None:
        for p_name, p_key in _VERTEX_PLANETS:
            d = _dist(chart_b.get(p_key), vertex_a)
            if d is not None and d <= _VERTEX_LILITH_ORB:
                result["soul_mod"] += 25.0
                result["shadow_tags"].append(f"B_{p_name}_Conjunct_Vertex")

    # Lilith triggers (禁忌之戀): Venus/Mars conjunction only, lust_mod +25 + high_voltage
    if lilith_b is not None:
        for p_name, p_key in _LILITH_PLANETS:
            d = _dist(chart_a.get(p_key), lilith_b)
            if d is not None and d <= _VERTEX_LILITH_ORB:
                result["lust_mod"] += 25.0
                result["high_voltage"] = True
                result["shadow_tags"].append(f"A_{p_name}_Conjunct_Lilith")
    if lilith_a is not None:
        for p_name, p_key in _LILITH_PLANETS:
            d = _dist(chart_b.get(p_key), lilith_a)
            if d is not None and d <= _VERTEX_LILITH_ORB:
                result["lust_mod"] += 25.0
                result["high_voltage"] = True
                result["shadow_tags"].append(f"B_{p_name}_Conjunct_Lilith")

    a_in_b12 = _in_house(chart_a.get("sun_degree"), h12_b, asc_b) or _in_house(chart_a.get("mars_degree"), h12_b, asc_b)
    if a_in_b12:
        result["soul_mod"] += 20.0
        result["high_voltage"] = True
        result["shadow_tags"].append("A_Illuminates_B_Shadow")
    b_in_a12 = _in_house(chart_b.get("sun_degree"), h12_a, asc_a) or _in_house(chart_b.get("mars_degree"), h12_a, asc_a)
    if b_in_a12:
        result["soul_mod"] += 20.0
        result["high_voltage"] = True
        result["shadow_tags"].append("B_Illuminates_A_Shadow")
    if a_in_b12 and b_in_a12:
        result["soul_mod"] += 40.0
        result["shadow_tags"].append("Mutual_Shadow_Integration")

    # ── Lunar Node triggers (南北交點) ──────────────────────────────────────
    # South Node conjunction: karmic debt pull → soul_mod +20, high_voltage
    # North Node conjunction: soul growth direction → soul_mod +20, no high_voltage
    _NODE_ORB = 3.0
    _NODE_PLANETS = [("Sun", "sun_degree"), ("Moon", "moon_degree"),
                     ("Venus", "venus_degree"), ("Mars", "mars_degree")]

    south_node_b = chart_b.get("south_node_degree")
    north_node_b = chart_b.get("north_node_degree")
    if south_node_b is not None:
        for p_name, p_key in _NODE_PLANETS:
            d = _dist(chart_a.get(p_key), south_node_b)
            if d is not None and d <= _NODE_ORB:
                result["soul_mod"] += 20.0
                result["high_voltage"] = True
                result["shadow_tags"].append(f"A_{p_name}_Conjunct_SouthNode")
    if north_node_b is not None:
        for p_name, p_key in _NODE_PLANETS:
            d = _dist(chart_a.get(p_key), north_node_b)
            if d is not None and d <= _NODE_ORB:
                result["soul_mod"] += 20.0
                result["shadow_tags"].append(f"A_{p_name}_Conjunct_NorthNode")

    south_node_a = chart_a.get("south_node_degree")
    north_node_a = chart_a.get("north_node_degree")
    if south_node_a is not None:
        for p_name, p_key in _NODE_PLANETS:
            d = _dist(chart_b.get(p_key), south_node_a)
            if d is not None and d <= _NODE_ORB:
                result["soul_mod"] += 20.0
                result["high_voltage"] = True
                result["shadow_tags"].append(f"B_{p_name}_Conjunct_SouthNode")
    if north_node_a is not None:
        for p_name, p_key in _NODE_PLANETS:
            d = _dist(chart_b.get(p_key), north_node_a)
            if d is not None and d <= _NODE_ORB:
                result["soul_mod"] += 20.0
                result["shadow_tags"].append(f"B_{p_name}_Conjunct_NorthNode")

    # ── 7th House Overlay (第七宮正緣指標) ─────────────────────────────────
    # Descendant = Ascendant + 180°.  When A's Sun/Moon/Venus conjuncts
    # B's Descendant (orb 5°), it signals a strong marriage/partnership bond.
    _DSC_ORB = 5.0
    _DSC_PLANETS = [("Sun", "sun_degree"), ("Moon", "moon_degree"),
                    ("Venus", "venus_degree")]

    if asc_b is not None:
        dsc_b = (asc_b + 180.0) % 360.0
        for p_name, p_key in _DSC_PLANETS:
            d = _dist(chart_a.get(p_key), dsc_b)
            if d is not None and d <= _DSC_ORB:
                result["partner_mod"] += 20.0
                result["soul_mod"] += 10.0
                result["shadow_tags"].append(f"A_{p_name}_Conjunct_Descendant")

    if asc_a is not None:
        dsc_a = (asc_a + 180.0) % 360.0
        for p_name, p_key in _DSC_PLANETS:
            d = _dist(chart_b.get(p_key), dsc_a)
            if d is not None and d <= _DSC_ORB:
                result["partner_mod"] += 20.0
                result["soul_mod"] += 10.0
                result["shadow_tags"].append(f"B_{p_name}_Conjunct_Descendant")

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
