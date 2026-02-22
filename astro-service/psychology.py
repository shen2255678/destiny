"""
DESTINY — Psychology Layer
Extracts psychological tags from a natal chart dict.

Three public functions:
  - extract_sm_dynamics(chart)        -> List[str]
  - extract_critical_degrees(chart)   -> List[str]
  - compute_element_profile(chart)    -> dict
"""

from __future__ import annotations

from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Aspect helpers
# ---------------------------------------------------------------------------

_ORB = 8.0  # degrees, used for all aspect checks


def _dist(a: float, b: float) -> float:
    """Shortest arc between two ecliptic longitudes (0–360)."""
    diff = abs(a - b) % 360.0
    return min(diff, 360.0 - diff)


def _has_aspect(a: Optional[float], b: Optional[float], aspect_type: str) -> bool:
    """Return True if planets at degrees *a* and *b* form the requested aspect.

    aspect_type values: "conjunction", "trine", "square", "opposition"
    Missing degrees (None) silently return False.
    """
    if a is None or b is None:
        return False

    diff = _dist(a, b)

    if aspect_type == "conjunction":
        return diff <= _ORB
    elif aspect_type == "trine":
        return abs(diff - 120.0) <= _ORB
    elif aspect_type == "square":
        return abs(diff - 90.0) <= _ORB
    elif aspect_type == "opposition":
        return abs(diff - 180.0) <= _ORB
    return False


def _in_tension(a: Optional[float], b: Optional[float]) -> bool:
    """Conjunction OR square OR opposition (tension aspects)."""
    return (
        _has_aspect(a, b, "conjunction")
        or _has_aspect(a, b, "square")
        or _has_aspect(a, b, "opposition")
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_sm_dynamics(chart: dict) -> List[str]:
    """Detect latent S/M role tags from natal chart aspect degrees.

    Tags and their triggers (orb = 8° for all):
      Natural_Dom   — sun OR mars conjunct/trine pluto
      Daddy_Dom     — saturn conjunct/trine sun
      Sadist_Dom    — mars square/opposition pluto
      Anxious_Sub   — moon in tension (conj/sq/opp) with pluto OR neptune
      Brat_Sub      — mercury in tension with mars
      Service_Sub   — venus_sign in {taurus, virgo, capricorn}
      Masochist_Sub — mars in tension or conjunction with neptune
    """
    tags: List[str] = []

    sun = chart.get("sun_degree")
    moon = chart.get("moon_degree")
    mercury = chart.get("mercury_degree")
    venus_sign = (chart.get("venus_sign") or "").lower()
    mars = chart.get("mars_degree")
    saturn = chart.get("saturn_degree")
    neptune = chart.get("neptune_degree")
    pluto = chart.get("pluto_degree")

    # Natural_Dom: sun OR mars conjunct/trine pluto
    if (
        _has_aspect(sun, pluto, "conjunction")
        or _has_aspect(sun, pluto, "trine")
        or _has_aspect(mars, pluto, "conjunction")
        or _has_aspect(mars, pluto, "trine")
    ):
        tags.append("Natural_Dom")

    # Daddy_Dom: saturn conjunct/trine sun
    if _has_aspect(saturn, sun, "conjunction") or _has_aspect(saturn, sun, "trine"):
        tags.append("Daddy_Dom")

    # Sadist_Dom: mars square/opposition pluto
    if _has_aspect(mars, pluto, "square") or _has_aspect(mars, pluto, "opposition"):
        tags.append("Sadist_Dom")

    # Anxious_Sub: moon in tension with pluto OR neptune
    if _in_tension(moon, pluto) or _in_tension(moon, neptune):
        tags.append("Anxious_Sub")

    # Brat_Sub: mercury in tension with mars
    if _in_tension(mercury, mars):
        tags.append("Brat_Sub")

    # Service_Sub: venus_sign in earth signs
    if venus_sign in {"taurus", "virgo", "capricorn"}:
        tags.append("Service_Sub")

    # Masochist_Sub: mars in tension with neptune (tension includes conjunction)
    if _in_tension(mars, neptune):
        tags.append("Masochist_Sub")

    return tags


def extract_critical_degrees(chart: dict, is_exact_time: bool = False) -> List[str]:
    """Detect 0° and 29° karmic degree markers in personal planets.

    Always checked: sun, mercury, venus, mars
    Only when is_exact_time=True: moon, asc

    Rules:
      degree % 30 >= 29.0  →  Karmic_Crisis_{POINT}
      degree % 30 <  1.0   →  Blind_Impulse_{POINT}
    """
    tags: List[str] = []

    # Base points always checked
    base_points = ["sun", "mercury", "venus", "mars"]
    # Extra points only for exact birth time (Tier 1)
    exact_points = ["moon", "asc"]

    points = base_points + (exact_points if is_exact_time else [])

    for point in points:
        if point == "asc":
            # Handle both key naming conventions
            degree = chart.get("asc_degree") or chart.get("ascendant_degree")
        else:
            degree = chart.get(f"{point}_degree")

        if degree is None:
            continue

        position_in_sign = degree % 30.0

        if position_in_sign >= 29.0:
            tags.append(f"Karmic_Crisis_{point.upper()}")
        elif position_in_sign < 1.0:
            tags.append(f"Blind_Impulse_{point.upper()}")

    return tags


# ---------------------------------------------------------------------------
# Element profile
# ---------------------------------------------------------------------------

_ELEMENT_MAP: Dict[str, str] = {
    # Fire
    "aries": "Fire", "leo": "Fire", "sagittarius": "Fire",
    # Earth
    "taurus": "Earth", "virgo": "Earth", "capricorn": "Earth",
    # Air
    "gemini": "Air", "libra": "Air", "aquarius": "Air",
    # Water
    "cancer": "Water", "scorpio": "Water", "pisces": "Water",
}

_PLANETS = [
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
]

_ELEMENTS = ["Fire", "Earth", "Air", "Water"]


def compute_element_profile(chart: dict) -> dict:
    """Count 10 core planets across the 4 Western elements.

    Returns:
      {
        "counts":     {"Fire": int, "Earth": int, "Air": int, "Water": int},
        "deficiency": [elements with count <= 1],
        "dominant":   [elements with count >= 4],
      }
    """
    counts: Dict[str, int] = {e: 0 for e in _ELEMENTS}

    for planet in _PLANETS:
        sign = chart.get(f"{planet}_sign")
        if sign is None:
            continue
        element = _ELEMENT_MAP.get(sign.lower())
        if element is None:
            continue
        counts[element] += 1

    deficiency = [e for e in _ELEMENTS if counts[e] <= 1]
    dominant = [e for e in _ELEMENTS if counts[e] >= 4]

    return {"counts": counts, "deficiency": deficiency, "dominant": dominant}
