"""
DESTINY — BaZi (八字四柱) Calculator
Computes the Four Pillars of Destiny from birth date/time.

Core output for matching:
  - Day Master (日主): the Heavenly Stem of the Day Pillar
  - Element (五行): wood/fire/earth/metal/water
  - Four Pillars: year, month, day, hour pillars

Matching dynamics:
  相生 (Generation): nurturing, harmonious → Wood→Fire→Earth→Metal→Water→Wood
  相剋 (Restriction): tension, power dynamics → Wood→Earth, Earth→Water, Water→Fire, Fire→Metal, Metal→Wood
  比和 (Same): rivalry or camaraderie
"""

from __future__ import annotations

import math
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

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

# ── Constants ───────────────────────────────────────────────────────

HEAVENLY_STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

STEM_ELEMENTS = {
    "甲": "wood", "乙": "wood",
    "丙": "fire", "丁": "fire",
    "戊": "earth", "己": "earth",
    "庚": "metal", "辛": "metal",
    "壬": "water", "癸": "water",
}

STEM_YINYANG = {
    "甲": "yang", "乙": "yin",
    "丙": "yang", "丁": "yin",
    "戊": "yang", "己": "yin",
    "庚": "yang", "辛": "yin",
    "壬": "yang", "癸": "yin",
}

BRANCH_ELEMENTS = {
    "子": "water", "丑": "earth", "寅": "wood", "卯": "wood",
    "辰": "earth", "巳": "fire",  "午": "fire",  "未": "earth",
    "申": "metal", "酉": "metal", "戌": "earth", "亥": "water",
}

# Element personality descriptions
ELEMENT_PROFILES = {
    "wood": {"cn": "木", "trait": "growth", "desc": "成長型、仁慈但固執。需要成長空間，無法忍受停滯。"},
    "fire": {"cn": "火", "trait": "expansion", "desc": "擴散型、熱情但急躁。關係中的發光體，情緒來去快。"},
    "earth": {"cn": "土", "trait": "containment", "desc": "包容型、穩重但被動。提供安全感，但反應較慢。"},
    "metal": {"cn": "金", "trait": "decisiveness", "desc": "決斷型、講義氣但尖銳。界線分明，追求效率與秩序。"},
    "water": {"cn": "水", "trait": "flow", "desc": "流動型、聰明但多變。情感細膩，善於溝通與適應。"},
}

# Generation cycle (相生): A generates B
GENERATION_CYCLE = {
    "wood": "fire",   # 木生火
    "fire": "earth",  # 火生土
    "earth": "metal", # 土生金
    "metal": "water", # 金生水
    "water": "wood",  # 水生木
}

# Restriction cycle (相剋): A restricts B
RESTRICTION_CYCLE = {
    "wood": "earth",  # 木剋土
    "earth": "water", # 土剋水
    "water": "fire",  # 水剋火
    "fire": "metal",  # 火剋金
    "metal": "wood",  # 金剋木
}

# 五虎遁月法: Year Stem → starting Month Stem for month 1 (寅月)
MONTH_STEM_START = {
    0: 2, 1: 4, 2: 6, 3: 8, 4: 0,  # 甲→丙, 乙→戊, 丙→庚, 丁→壬, 戊→甲
    5: 2, 6: 4, 7: 6, 8: 8, 9: 0,  # 己→丙, 庚→戊, 辛→庚, 壬→壬, 癸→甲
}

# 五鼠遁時法: Day Stem → starting Hour Stem for hour 0 (子時)
HOUR_STEM_START = {
    0: 0, 1: 2, 2: 4, 3: 6, 4: 8,  # 甲→甲, 乙→丙, 丙→戊, 丁→庚, 戊→壬
    5: 0, 6: 2, 7: 4, 8: 6, 9: 8,  # 己→甲, 庚→丙, 辛→戊, 壬→庚, 癸→壬
}

# Solar term longitudes for month boundaries (節氣)
# Each month starts at a specific solar longitude
# Month 1 (寅) starts at 立春 (315°), Month 2 (卯) at 驚蟄 (345°), etc.
MONTH_START_LONGITUDES = [
    315,  # Month 1  寅月 - 立春
    345,  # Month 2  卯月 - 驚蟄
    15,   # Month 3  辰月 - 清明
    45,   # Month 4  巳月 - 立夏
    75,   # Month 5  午月 - 芒種
    105,  # Month 6  未月 - 小暑
    135,  # Month 7  申月 - 立秋
    165,  # Month 8  酉月 - 白露
    195,  # Month 9  戌月 - 寒露
    225,  # Month 10 亥月 - 立冬
    255,  # Month 11 子月 - 大雪
    285,  # Month 12 丑月 - 小寒
]


# ── True Solar Time (真太陽時) ──────────────────────────────────────

def _equation_of_time(jd: float) -> float:
    """Calculate the Equation of Time (in minutes).

    Uses the Spencer (1971) formula based on day-of-year angle.
    EoT = apparent_solar_time - mean_solar_time.
    """
    # Get approximate day of year from JD
    # J2000.0 = 2451545.0 = 2000-01-01 12:00 UT
    n = jd - 2451545.0
    # Fractional year in radians
    # B = (360/365.24) * (day_of_year - 81) degrees
    # We compute day_of_year from JD
    year = int((n + 0.5) / 365.25) + 2000
    jd_jan1 = swe.julday(year, 1, 1, 0.0)
    day_of_year = jd - jd_jan1 + 1

    b = math.radians((360.0 / 365.24) * (day_of_year - 81))

    # Spencer formula for EoT (minutes)
    eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)

    return eot  # minutes


def clock_to_solar_time(
    clock_hour: float,
    lng: float,
    jd: float,
    standard_meridian: float = 120.0,
) -> float:
    """Convert clock time to true solar time (真太陽時).

    Parameters
    ----------
    clock_hour : float     Local clock time in hours (e.g. 10.983 for 10:59)
    lng : float            Birth location longitude
    jd : float             Julian Day for EoT calculation
    standard_meridian : float  Standard meridian for timezone (120°E for UTC+8)

    Returns
    -------
    float : True solar time in hours
    """
    # Longitude correction: 4 minutes per degree east of standard meridian
    lng_correction_min = (lng - standard_meridian) * 4.0

    # Equation of Time correction
    eot_min = _equation_of_time(jd)

    # Total correction in hours
    correction_hours = (lng_correction_min + eot_min) / 60.0

    solar_hour = clock_hour + correction_hours
    return solar_hour


# ── Pillar Calculations ─────────────────────────────────────────────

def _get_chinese_year(jd: float, year: int) -> int:
    """Determine the Chinese year based on whether date is before/after 立春.

    The Chinese year starts at 立春 (lichun, Sun at 315°). If the date is
    before lichun of the given Gregorian year, the Chinese year is year - 1.
    """
    # Find approximate JD of lichun for this Gregorian year
    # Lichun is around Feb 3-5. Check Sun's longitude at Jan 1 vs target 315°.
    # Simple approach: calculate Sun longitude at the birth JD
    sun_pos, _ = swe.calc_ut(jd, swe.SUN)
    sun_lng = sun_pos[0]

    # If we're in Jan-Feb and Sun hasn't reached 315° yet, it's previous Chinese year
    if year > 0:
        # Check: is the date before lichun of this year?
        # Lichun = Sun at 315°. If month is Jan or early Feb, check longitude.
        # Sun at 315° is around Feb 3-5. Before that, sun_lng is ~280-314.
        # After lichun, sun_lng is 315+.
        # But longitude wraps: 315° in Aquarius, going to 345° (Pisces), then 0° (Aries)...
        # So before lichun in Jan: sun_lng is roughly 280-314
        # After lichun in Feb+: sun_lng >= 315 (or wraps past 360 to 0+)
        dt_approx = datetime(year, 1, 1)
        jd_jan1 = swe.julday(year, 1, 1, 0.0)
        jd_mar1 = swe.julday(year, 3, 1, 0.0)

        if jd < jd_mar1:
            # We're in Jan-Feb range, need to check if before lichun
            # Find lichun by checking when Sun crosses 315°
            if sun_lng < 315 and sun_lng >= 270:
                return year - 1

    return year


def _solar_month(jd: float) -> int:
    """Determine the Chinese solar month (1-12) from Sun's longitude.

    Returns month index 0-11 (0=寅月, 1=卯月, ... 11=丑月).
    """
    sun_pos, _ = swe.calc_ut(jd, swe.SUN)
    sun_lng = sun_pos[0]  # 0-360

    # Determine which month segment the Sun is in
    for i in range(12):
        start = MONTH_START_LONGITUDES[i]
        end = MONTH_START_LONGITUDES[(i + 1) % 12]

        if start < end:
            if start <= sun_lng < end:
                return i
        else:
            # Wraps around 360→0 (e.g., 315 to 345, or 345 to 15)
            if sun_lng >= start or sun_lng < end:
                return i

    return 0  # fallback


def _hour_branch_index(local_hour: float) -> int:
    """Convert local hour (0-24) to earthly branch index (0-11).

    子時 23:00-01:00 = 0, 丑時 01:00-03:00 = 1, ..., 亥時 21:00-23:00 = 11
    """
    # Shift by 1 hour so 23:00 maps to index 0
    shifted = (local_hour + 1) % 24
    return int(shifted // 2)


def calculate_year_pillar(chinese_year: int) -> Tuple[int, int]:
    """Return (stem_index, branch_index) for the year pillar."""
    stem = (chinese_year - 4) % 10
    branch = (chinese_year - 4) % 12
    return stem, branch


def calculate_month_pillar(year_stem: int, month_index: int) -> Tuple[int, int]:
    """Return (stem_index, branch_index) for the month pillar.

    month_index: 0=寅月(Month 1), 1=卯月, ..., 11=丑月
    """
    branch = (month_index + 2) % 12  # 寅=2, 卯=3, ..., 丑=1
    start_stem = MONTH_STEM_START[year_stem]
    stem = (start_stem + month_index) % 10
    return stem, branch


def calculate_day_pillar(jd: float) -> Tuple[int, int]:
    """Return (stem_index, branch_index) for the day pillar.

    Uses Julian Day Number with calibrated offset.
    Verified: 1997-03-07 = 戊申日 (stem=4, branch=8).
    """
    jd_int = int(jd + 0.5)  # Round to nearest day (JD starts at noon)
    stem = (jd_int + 9) % 10
    branch = (jd_int + 1) % 12
    return stem, branch


def calculate_hour_pillar(day_stem: int, hour_branch_idx: int) -> Tuple[int, int]:
    """Return (stem_index, branch_index) for the hour pillar."""
    start_stem = HOUR_STEM_START[day_stem]
    stem = (start_stem + hour_branch_idx) % 10
    return stem, branch_idx_to_branch(hour_branch_idx)


def branch_idx_to_branch(idx: int) -> int:
    """Identity — branch index IS the branch position."""
    return idx


def pillar_to_str(stem_idx: int, branch_idx: int) -> str:
    """Convert stem/branch indices to Chinese characters."""
    return HEAVENLY_STEMS[stem_idx] + EARTHLY_BRANCHES[branch_idx]


# ── Main Calculation ────────────────────────────────────────────────

def calculate_bazi(
    birth_date: str,
    birth_time: Optional[str] = None,
    birth_time_exact: Optional[str] = None,
    lat: float = 25.033,
    lng: float = 121.565,
    data_tier: int = 3,
) -> Dict:
    """Calculate BaZi Four Pillars from birth data.

    Parameters
    ----------
    birth_date : str       "YYYY-MM-DD"
    birth_time : str|None  "precise"/"morning"/"afternoon"/"evening"/"unknown"
    birth_time_exact : str|None  "HH:MM"
    lat, lng : float       Birth coordinates (for potential future timezone calc)
    data_tier : int        1/2/3

    Returns
    -------
    dict with keys:
      day_master: str (甲-癸)
      day_master_element: str (wood/fire/earth/metal/water)
      day_master_yinyang: str (yin/yang)
      element_profile: dict (cn, trait, desc)
      four_pillars: { year, month, day, hour }
      hour_known: bool
    """
    dt = datetime.strptime(birth_date, "%Y-%m-%d")

    # Determine local clock hour for hour pillar
    clock_hour = 12.0  # default noon
    hour_known = False
    if data_tier == 1 and birth_time_exact:
        parts = birth_time_exact.split(":")
        clock_hour = int(parts[0]) + int(parts[1]) / 60.0
        hour_known = True
    elif data_tier == 2 and birth_time:
        fuzzy_map = {"morning": 9.0, "afternoon": 14.0, "evening": 20.0}
        if birth_time in fuzzy_map:
            clock_hour = fuzzy_map[birth_time]
            hour_known = True

    # UT for astronomical calculations (Taiwan = UTC+8)
    ut_hour = clock_hour - 8.0
    jd = swe.julday(dt.year, dt.month, dt.day, ut_hour)

    # Convert clock time to true solar time (真太陽時)
    local_hour = clock_to_solar_time(clock_hour, lng, jd) if hour_known else clock_hour

    # ── Year Pillar ──
    chinese_year = _get_chinese_year(jd, dt.year)
    year_stem, year_branch = calculate_year_pillar(chinese_year)

    # ── Month Pillar ──
    month_index = _solar_month(jd)
    month_stem, month_branch = calculate_month_pillar(year_stem, month_index)

    # ── Day Pillar ──
    # Use local noon (12:00 Taiwan = UT 04:00) so early-morning births (00:00–07:59 local)
    # don't cross the UTC date boundary and land on the wrong calendar day.
    jd_local_noon = swe.julday(dt.year, dt.month, dt.day, 4.0)
    day_stem, day_branch = calculate_day_pillar(jd_local_noon)

    # ── Hour Pillar ──
    hour_branch_idx = _hour_branch_index(local_hour)
    hour_stem_start = HOUR_STEM_START[day_stem]
    hour_stem = (hour_stem_start + hour_branch_idx) % 10
    hour_branch = hour_branch_idx

    # ── Day Master (日主) ──
    day_master = HEAVENLY_STEMS[day_stem]
    day_master_element = STEM_ELEMENTS[day_master]
    day_master_yinyang = STEM_YINYANG[day_master]

    # Build result
    pillars = {
        "year": {
            "stem": HEAVENLY_STEMS[year_stem],
            "branch": EARTHLY_BRANCHES[year_branch],
            "full": pillar_to_str(year_stem, year_branch),
        },
        "month": {
            "stem": HEAVENLY_STEMS[month_stem],
            "branch": EARTHLY_BRANCHES[month_branch],
            "full": pillar_to_str(month_stem, month_branch),
        },
        "day": {
            "stem": HEAVENLY_STEMS[day_stem],
            "branch": EARTHLY_BRANCHES[day_branch],
            "full": pillar_to_str(day_stem, day_branch),
        },
    }

    if hour_known:
        pillars["hour"] = {
            "stem": HEAVENLY_STEMS[hour_stem],
            "branch": EARTHLY_BRANCHES[hour_branch],
            "full": pillar_to_str(hour_stem, hour_branch),
        }
    else:
        pillars["hour"] = None

    return {
        "day_master": day_master,
        "day_master_element": day_master_element,
        "day_master_yinyang": day_master_yinyang,
        "element_profile": ELEMENT_PROFILES[day_master_element],
        "four_pillars": pillars,
        "hour_known": hour_known,
    }


# ── Relationship Dynamics (for matching) ────────────────────────────

def analyze_element_relation(element_a: str, element_b: str) -> Dict:
    """Analyze the Five-Element relationship between two people.

    Returns the dynamic from A's perspective towards B.
    """
    if element_a == element_b:
        return {
            "relation": "same",
            "relation_cn": "比和",
            "dynamic": "parallel",
            "description": "同元素，亦敵亦友。彼此理解但容易競爭。",
            "harmony_score": 0.6,
        }

    if GENERATION_CYCLE[element_a] == element_b:
        return {
            "relation": "a_generates_b",
            "relation_cn": f"{ELEMENT_PROFILES[element_a]['cn']}生{ELEMENT_PROFILES[element_b]['cn']}",
            "dynamic": "nurturing",
            "description": f"A（{ELEMENT_PROFILES[element_a]['cn']}）滋養 B（{ELEMENT_PROFILES[element_b]['cn']}）。A 較付出照顧，B 較受寵。",
            "harmony_score": 0.85,
        }

    if GENERATION_CYCLE[element_b] == element_a:
        return {
            "relation": "b_generates_a",
            "relation_cn": f"{ELEMENT_PROFILES[element_b]['cn']}生{ELEMENT_PROFILES[element_a]['cn']}",
            "dynamic": "being_nurtured",
            "description": f"B（{ELEMENT_PROFILES[element_b]['cn']}）滋養 A（{ELEMENT_PROFILES[element_a]['cn']}）。B 較付出照顧，A 較受寵。",
            "harmony_score": 0.85,
        }

    if RESTRICTION_CYCLE[element_a] == element_b:
        return {
            "relation": "a_restricts_b",
            "relation_cn": f"{ELEMENT_PROFILES[element_a]['cn']}剋{ELEMENT_PROFILES[element_b]['cn']}",
            "dynamic": "controlling",
            "description": f"A（{ELEMENT_PROFILES[element_a]['cn']}）剋 B（{ELEMENT_PROFILES[element_b]['cn']}）。高張力吸引，A 掌權。B 需妥協否則劇烈衝突。",
            "harmony_score": 0.5,
        }

    if RESTRICTION_CYCLE[element_b] == element_a:
        return {
            "relation": "b_restricts_a",
            "relation_cn": f"{ELEMENT_PROFILES[element_b]['cn']}剋{ELEMENT_PROFILES[element_a]['cn']}",
            "dynamic": "being_controlled",
            "description": f"B（{ELEMENT_PROFILES[element_b]['cn']}）剋 A（{ELEMENT_PROFILES[element_a]['cn']}）。高張力吸引，B 掌權。A 需妥協否則劇烈衝突。",
            "harmony_score": 0.5,
        }

    # Should not reach here with 5 elements
    return {"relation": "unknown", "harmony_score": 0.5}
