"""
DESTINY — Natal Chart Calculator
Uses Swiss Ephemeris (pyswisseph) to compute planetary positions and zodiac signs.

Data Tier behaviour:
  Tier 1 (Gold)  : precise birth time → all 6 signs + ascendant
  Tier 2 (Silver): fuzzy time slot    → all planets but Moon is approximate, no ascendant
  Tier 3 (Bronze): date only (noon)   → Sun/Venus/Mars/Saturn only, Moon & ascendant = null
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Optional

import swisseph as swe

def _resolve_ephe_path() -> str:
    """Return an ASCII-safe path to the ephemeris directory.

    pyswisseph passes the path to a C library that cannot handle non-ASCII
    characters on Windows. If the repo lives inside a directory whose path
    contains Unicode characters (e.g. Chinese), we copy the small .se1 files
    to a stable ASCII temp location and use that instead.
    """
    ephe_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ephe")
    try:
        ephe_src.encode("ascii")
        return ephe_src  # All-ASCII — use directly
    except UnicodeEncodeError:
        pass

    # Path contains non-ASCII characters; copy files to an ASCII temp location.
    import shutil, tempfile, atexit

    dest = os.path.join(tempfile.gettempdir(), "destiny_swe_ephe")
    os.makedirs(dest, exist_ok=True)

    for fname in os.listdir(ephe_src):
        src_file = os.path.join(ephe_src, fname)
        dst_file = os.path.join(dest, fname)
        if not os.path.exists(dst_file):
            shutil.copy2(src_file, dst_file)

    return dest


_EPHE_DIR = _resolve_ephe_path()
swe.set_ephe_path(_EPHE_DIR)

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
    "sun":     swe.SUN,
    "moon":    swe.MOON,
    "mercury": swe.MERCURY,
    "venus":   swe.VENUS,
    "mars":    swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn":  swe.SATURN,
    "uranus":  swe.URANUS,   # 天王星 — generational (7 yr/sign); used for uniqueness scores
    "neptune": swe.NEPTUNE,  # 海王星 — generational (14 yr/sign); used for spiritual resonance
    "pluto":   swe.PLUTO,
}

# Asteroid IDs (requires seas_18.se1 in ./ephe/)
ASTEROIDS = {
    "chiron": swe.CHIRON,
    "juno":   swe.AST_OFFSET + 3,
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


# ── Emotional Capacity ──────────────────────────────────────────────

def compute_emotional_capacity(chart_data: dict, zwds_data: Optional[dict] = None) -> int:
    """Compute emotional capacity score (0-100).

    Derived automatically from the natal chart and ZWDS chart.
    A higher score means the person can absorb emotional stress without
    overloading; a lower score signals vulnerability to emotional drainage.

    Rules (base = 50):
    - Stellium in house 4/8/12 (≥3 planets in same sign as any of these houses,
      whole-sign approximation): -15 (only for Tier 1 with house signs available)
    - Moon-Pluto square (3) or opposition (6): -20
    - Moon-Saturn trine (4) or sextile (2): +15
    - ZWDS empty life palace: -10
    - ZWDS karma palace (福德宮): -10 for each malevolent star (擎羊/陀羅/火星/鈴星/天空/地劫)
      and -10 for each 化忌 in karma palace main/auspicious stars
    - ZWDS life palace has 紫微 or 天府: +20

    Returns int clamped to [0, 100].
    """
    SIGN_INDEX_LOCAL = {
        "aries": 0, "taurus": 1, "gemini": 2, "cancer": 3,
        "leo": 4, "virgo": 5, "libra": 6, "scorpio": 7,
        "sagittarius": 8, "capricorn": 9, "aquarius": 10, "pisces": 11,
    }

    capacity = 50

    # ── Rule 1: Stellium in 4th/8th/12th house (Tier 1 only) ──────────
    planet_signs = [
        chart_data.get("sun_sign"), chart_data.get("moon_sign"),
        chart_data.get("mercury_sign"), chart_data.get("venus_sign"),
        chart_data.get("mars_sign"), chart_data.get("jupiter_sign"),
        chart_data.get("saturn_sign"), chart_data.get("pluto_sign"),
    ]
    for house_sign_key in ("house4_sign", "house8_sign", "house12_sign"):
        h_sign = chart_data.get(house_sign_key)
        if h_sign:
            count = sum(1 for ps in planet_signs if ps == h_sign)
            if count >= 3:
                capacity -= 15
                break  # only penalize once even if multiple houses have stellium

    # ── Rule 2: Moon-Pluto hard aspects ────────────────────────────────
    moon_sign = chart_data.get("moon_sign")
    pluto_sign = chart_data.get("pluto_sign")
    if moon_sign and pluto_sign and moon_sign in SIGN_INDEX_LOCAL and pluto_sign in SIGN_INDEX_LOCAL:
        # Signs are 0-indexed 0-11; abs() gives values in [0,11]. % 12 is a no-op but
        # kept for consistency with matching.py. Fold to [0,6] for aspect distance.
        dist = abs(SIGN_INDEX_LOCAL[moon_sign] - SIGN_INDEX_LOCAL[pluto_sign]) % 12
        if dist > 6:
            dist = 12 - dist
        if dist in (3, 6):  # square or opposition
            capacity -= 20

    # ── Rule 3: Moon-Saturn harmonious aspects ──────────────────────────
    saturn_sign = chart_data.get("saturn_sign")
    if moon_sign and saturn_sign and moon_sign in SIGN_INDEX_LOCAL and saturn_sign in SIGN_INDEX_LOCAL:
        # Signs are 0-indexed 0-11; abs() gives values in [0,11]. % 12 is a no-op but
        # kept for consistency with matching.py. Fold to [0,6] for aspect distance.
        dist = abs(SIGN_INDEX_LOCAL[moon_sign] - SIGN_INDEX_LOCAL[saturn_sign]) % 12
        if dist > 6:
            dist = 12 - dist
        if dist in (2, 4):  # sextile or trine
            capacity += 15

    # ── Rules 4-6: ZWDS (only when zwds_data available) ────────────────
    if zwds_data:
        palaces = zwds_data.get("palaces", {})

        # Rule 4: Empty life palace (命宮)
        ming_palace = palaces.get("ming", {})
        if ming_palace.get("is_empty"):
            capacity -= 10

        # Rule 5: Karma palace (福德宮) malevolent stars + 化忌
        karma_palace = palaces.get("karma", {})
        SHA_STARS = {"擎羊", "陀羅", "火星", "鈴星", "天空", "地劫"}

        for star in karma_palace.get("malevolent_stars", []):
            if star in SHA_STARS:
                capacity -= 10

        for star in karma_palace.get("main_stars", []) + karma_palace.get("auspicious_stars", []):
            if "化忌" in star:
                capacity -= 10

        # Rule 6: Life palace has 紫微 or 天府
        for star in ming_palace.get("main_stars", []):
            if "紫微" in star or "天府" in star:
                capacity += 20
                break  # only once

    return max(0, min(100, capacity))


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
        result[f"{name}_degree"] = round(pos[0], 2)  # absolute ecliptic longitude 0-360

    # ── Asteroids (Chiron, Juno) ─────────────────────────────────
    for name, asteroid_id in ASTEROIDS.items():
        try:
            pos, _ret = swe.calc_ut(jd, asteroid_id)
            result[f"{name}_sign"] = longitude_to_sign(pos[0])
            result[f"{name}_degree"] = round(pos[0], 2)
        except Exception:
            result[f"{name}_sign"] = None  # ephe file missing — degrade gracefully
            result[f"{name}_degree"] = None

    # ── Tier-based restrictions ──────────────────────────────────
    if data_tier == 3:
        # Bronze: Moon is unreliable without time
        result["moon_sign"] = None
        result["moon_degree"] = None

    if data_tier >= 2:
        # Silver & Bronze: no Ascendant, no House cusps (requires precise time)
        result["ascendant_sign"] = None
        result["ascendant_degree"] = None
        result["house4_sign"] = None
        result["house4_degree"] = None
        result["house8_sign"] = None
        result["house8_degree"] = None
        result["house12_sign"] = None
        result["house12_degree"] = None
    else:
        # Tier 1 (Gold): calculate Ascendant + House 4/8/12 via Placidus cusps
        cusps, ascmc = swe.houses(jd, lat, lng, b"P")
        result["ascendant_sign"] = longitude_to_sign(ascmc[0])
        result["ascendant_degree"] = round(ascmc[0], 2)
        # pyswisseph swe.houses() returns a 12-element tuple, 0-indexed: cusps[0]=H1 … cusps[11]=H12
        result["house4_sign"] = longitude_to_sign(cusps[3])
        result["house4_degree"] = round(cusps[3], 2)
        result["house8_sign"] = longitude_to_sign(cusps[7])
        result["house8_degree"] = round(cusps[7], 2)
        result["house12_sign"] = longitude_to_sign(cusps[11])
        result["house12_degree"] = round(cusps[11], 2)

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

    # ── Emotional Capacity (心理情緒容量) ───────────────────────
    # Computed from Western chart aspects only (ZWDS rules require zwds_data,
    # which is computed separately by compute_zwds_chart in main.py).
    # Callers with ZWDS data should call compute_emotional_capacity(chart_data, zwds_data)
    # separately and update this field after computing the ZWDS chart.
    result["emotional_capacity"] = compute_emotional_capacity(result)

    return result
