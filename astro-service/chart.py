"""
DESTINY — Natal Chart Calculator
Uses Swiss Ephemeris (pyswisseph) to compute planetary positions and zodiac signs.

Data Tier behaviour:
  Tier 1 (Gold)  : precise birth time → all 6 signs + ascendant
  Tier 2 (Silver): fuzzy time slot    → all planets but Moon is approximate, no ascendant
  Tier 3 (Bronze): date only (noon)   → Sun/Venus/Mars/Saturn only, Moon & ascendant = null
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

import swisseph as swe

# ── Zodiac constants ────────────────────────────────────────────────

SIGNS = [
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
]

ELEMENT_MAP = {
    "aries": "fire",    "leo": "fire",       "sagittarius": "fire",
    "taurus": "earth",  "virgo": "earth",    "capricorn": "earth",
    "gemini": "air",    "libra": "air",      "aquarius": "air",
    "cancer": "water",  "scorpio": "water",  "pisces": "water",
}

# Planet IDs in swisseph
PLANETS = {
    "sun":    swe.SUN,
    "moon":   swe.MOON,
    "venus":  swe.VENUS,
    "mars":   swe.MARS,
    "saturn": swe.SATURN,
}

# Fuzzy time-slot mid-points (local time hours)
FUZZY_HOURS = {
    "morning":   9.0,
    "afternoon": 14.0,
    "evening":   20.0,
}


# ── Helpers ─────────────────────────────────────────────────────────

def longitude_to_sign(longitude: float) -> str:
    """Convert ecliptic longitude (0-360) to zodiac sign name."""
    index = int(longitude // 30) % 12
    return SIGNS[index]


def _resolve_hour(birth_time: str | None, birth_time_exact: str | None, data_tier: int) -> float:
    """Return decimal hour (UT approximation) for the calculation.

    For simplicity we treat the birth time as UTC+8 (Taiwan) and convert
    to UT by subtracting 8 hours. A production version would use proper
    timezone lookup, but for MVP this is sufficient since all users are
    in Taiwan.
    """
    local_hour = 12.0  # default noon for tier 3

    if data_tier == 1 and birth_time_exact:
        parts = birth_time_exact.split(":")
        local_hour = int(parts[0]) + int(parts[1]) / 60.0
    elif data_tier == 2 and birth_time and birth_time in FUZZY_HOURS:
        local_hour = FUZZY_HOURS[birth_time]

    # Convert Taiwan local time (UTC+8) to UT
    ut_hour = local_hour - 8.0
    return ut_hour


# ── Main calculation ────────────────────────────────────────────────

def calculate_chart(
    birth_date: str,
    birth_time: str | None = None,
    birth_time_exact: str | None = None,
    lat: float = 25.033,
    lng: float = 121.565,
    data_tier: int = 3,
) -> dict:
    """Calculate natal chart and return zodiac sign positions.

    Parameters
    ----------
    birth_date : str       ISO date, e.g. "1995-06-15"
    birth_time : str|None  "precise", "morning", "afternoon", "evening", "unknown"
    birth_time_exact : str|None  "HH:MM" when birth_time == "precise"
    lat, lng : float       Birth location coordinates
    data_tier : int        1 (gold), 2 (silver), 3 (bronze)

    Returns
    -------
    dict with keys: sun_sign, moon_sign, venus_sign, mars_sign,
                    saturn_sign, ascendant_sign, element_primary, data_tier
    """
    dt = datetime.strptime(birth_date, "%Y-%m-%d")
    ut_hour = _resolve_hour(birth_time, birth_time_exact, data_tier)

    # Julian Day Number (UT)
    jd = swe.julday(dt.year, dt.month, dt.day, ut_hour)

    # ── Planetary positions ──────────────────────────────────────
    result: dict[str, str | int | None] = {"data_tier": data_tier}

    for name, planet_id in PLANETS.items():
        # swe.calc_ut returns (longitude, latitude, distance, speed_lon, speed_lat, speed_dist)
        pos, _ret_flag = swe.calc_ut(jd, planet_id)
        sign = longitude_to_sign(pos[0])
        result[f"{name}_sign"] = sign

    # ── Tier-based restrictions ──────────────────────────────────
    if data_tier == 3:
        # Bronze: Moon is unreliable without time, Ascendant impossible
        result["moon_sign"] = None

    if data_tier >= 2:
        # Silver & Bronze: no Ascendant (requires precise time)
        result["ascendant_sign"] = None
    else:
        # Tier 1 (Gold): calculate Ascendant via house cusps
        cusps, ascmc = swe.houses(jd, lat, lng, b"P")
        asc_longitude = ascmc[0]  # ascmc[0] = Ascendant
        result["ascendant_sign"] = longitude_to_sign(asc_longitude)

    # ── Element from Sun sign ────────────────────────────────────
    sun_sign = result.get("sun_sign")
    result["element_primary"] = ELEMENT_MAP.get(sun_sign) if sun_sign else None

    # ── BaZi (八字四柱) ────────────────────────────────────────
    from bazi import calculate_bazi
    bazi = calculate_bazi(
        birth_date=birth_date,
        birth_time=birth_time,
        birth_time_exact=birth_time_exact,
        lat=lat,
        lng=lng,
        data_tier=data_tier,
    )
    result["bazi"] = bazi

    return result
