# -*- coding: utf-8 -*-
"""
DESTINY — Ideal Partner Avatar Profiler (Sprint 4)

Reverse-engineers a single person's natal chart into "ideal partner" trait tags
for the recommendation system's first-pass DB filtering.

Three-layer extraction:
  Rule 1: Western Astrology — DSC, Venus, Mars, natal hard aspects
  Rule 2: BaZi (八字)        — Day Master complement + Day Branch 偏印
  Rule 3: ZWDS (紫微斗數)    — Spouse palace stars, sha-stars, empty palace

Public API:
    extract_ideal_partner_profile(western_chart, bazi_chart, zwds_chart) -> dict
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from bazi import GENERATION_CYCLE

# ── Sign helpers ─────────────────────────────────────────────────────────────

SIGNS: List[str] = [
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
]

_SIGN_INDEX: Dict[str, int] = {s: i for i, s in enumerate(SIGNS)}


def _safe_sign(chart: dict, key: str) -> Optional[str]:
    """Return lowercase sign string or None."""
    val = chart.get(key)
    if val and isinstance(val, str):
        v = val.strip().lower()
        return v if v in _SIGN_INDEX else None
    return None


def _sign_diff(sign_a: Optional[str], sign_b: Optional[str]) -> Optional[int]:
    """Minimum sign distance (0-6) between two signs. None if missing."""
    if not sign_a or not sign_b:
        return None
    idx_a = _SIGN_INDEX.get(sign_a)
    idx_b = _SIGN_INDEX.get(sign_b)
    if idx_a is None or idx_b is None:
        return None
    diff = abs(idx_a - idx_b)
    return min(diff, 12 - diff)


def _is_hard_aspect_signs(sign_a: Optional[str], sign_b: Optional[str]) -> bool:
    """True when signs are in square (3 apart) or opposition (6 apart)."""
    diff = _sign_diff(sign_a, sign_b)
    return diff in (3, 6)


# ── BaZi constants ──────────────────────────────────────────────────────────

# Day branches → 偏印 (Indirect Resource) attraction tendency.
# 巳亥丑未 are the four seasonal transition branches, associated with
# unconventional thinking.
_PIAN_YIN_BRANCHES = frozenset(["巳", "亥", "丑", "未"])
_INDIRECT_RESOURCE_NEED = "容易被古怪、有獨特邏輯的人吸引"


# ── ZWDS constants ──────────────────────────────────────────────────────────

# 14 main stars for empty palace detection (化 suffixes stripped)
_ZWDS_MAIN_14 = frozenset([
    "紫微", "天機", "太陽", "武曲", "天同", "廉貞", "天府",
    "太陰", "貪狼", "巨門", "天相", "天梁", "七殺", "破軍",
])

# Star group classification
SPOUSE_STAR_GROUPS: Dict[str, List[str]] = {
    "殺破狼":   ["七殺", "破軍", "貪狼"],
    "紫府日":   ["紫微", "天府", "太陽"],
    "機月同梁": ["天機", "太陰", "天同", "天梁"],
    "武廉巨相": ["武曲", "廉貞", "巨門", "天相"],
}

GROUP_TAGS: Dict[str, List[str]] = {
    "殺破狼":   ["感情波動大", "喜歡充滿魅力與挑戰性的對象"],
    "紫府日":   ["喜歡氣場強大、能帶領自己的人", "慕強心理"],
    "機月同梁": ["渴望溫柔陪伴", "喜歡知性、情緒穩定的人"],
    "武廉巨相": ["務實導向", "重視對方能力與社會價值"],
}

# Reverse lookup: star → group name
_STAR_TO_GROUP: Dict[str, str] = {}
for _group, _stars in SPOUSE_STAR_GROUPS.items():
    for _star in _stars:
        _STAR_TO_GROUP[_star] = _group

# Six sha-stars → unconscious desire patterns
AFFLICTION_STAR_MAP: Dict[str, Dict] = {
    "擎羊": {"tags": ["氣場強", "直接不扭捏"], "needs": "潛意識容易被強勢、有野性的人吸引", "dynamic": "high_voltage"},
    "火星": {"tags": ["氣場強", "直接不扭捏"], "needs": "潛意識容易被強勢、有野性的人吸引", "dynamic": "high_voltage"},
    "陀羅": {"tags": ["心思深沉", "宿命感"], "needs": "感情中帶有強烈執念，容易吸引帶有宿命感的對象", "dynamic": "high_voltage"},
    "鈴星": {"tags": ["心思深沉", "宿命感"], "needs": "感情中帶有強烈執念，容易吸引帶有宿命感的對象", "dynamic": "high_voltage"},
    "地空": {"tags": ["靈魂共鳴", "非傳統關係"], "needs": "不愛世俗常規，追求極致靈魂交流", "dynamic": "high_voltage"},
    "地劫": {"tags": ["靈魂共鳴", "非傳統關係"], "needs": "不愛世俗常規，追求極致靈魂交流", "dynamic": "high_voltage"},
}

# Hard natal aspects that trigger high-voltage flag
_HARD_ASPECT_TYPES = frozenset(["conjunction", "square", "opposition"])
_VOLATILE_PLANETS = frozenset(["pluto", "uranus", "chiron"])


# ── Hua stripping ────────────────────────────────────────────────────────────

def _strip_hua(star: str) -> str:
    """Strip 四化 suffix: '天府化科' → '天府'."""
    for suffix in ("化祿", "化權", "化科", "化忌"):
        if star.endswith(suffix):
            return star[: -len(suffix)]
    return star


# ── Rule 1: Western Astrology ────────────────────────────────────────────────

def _extract_western(
    chart: dict,
    target_signs: List[str],
    psych_needs: List[str],
) -> bool:
    """Populate target_signs; return True if high-voltage detected."""
    high_voltage = False

    # 1a. Descendant (DSC / house7_sign) — highest priority
    dsc = _safe_sign(chart, "house7_sign") or _safe_sign(chart, "descendant_sign")
    if dsc:
        target_signs.append(dsc.capitalize())

    # 1b. Venus sign — aesthetic preference
    venus = _safe_sign(chart, "venus_sign")
    if venus:
        cap = venus.capitalize()
        if cap not in target_signs:
            target_signs.append(cap)

    # 1c. Mars sign — desire
    mars = _safe_sign(chart, "mars_sign")
    if mars:
        cap = mars.capitalize()
        if cap not in target_signs:
            target_signs.append(cap)

    # 1d. High-voltage detection via natal_aspects (degree-level)
    #     Venus or Moon hard-aspecting Pluto/Uranus/Chiron
    natal_aspects = chart.get("natal_aspects", [])
    for asp in natal_aspects:
        if asp.get("aspect") not in _HARD_ASPECT_TYPES:
            continue
        pair = {asp.get("a", ""), asp.get("b", "")}
        inner_hit = pair & {"venus", "moon"}
        outer_hit = pair & _VOLATILE_PLANETS
        if inner_hit and outer_hit:
            high_voltage = True
            break

    # 1e. Fallback: sign-level hard aspect check (when natal_aspects missing)
    if not high_voltage and not natal_aspects:
        venus_s = _safe_sign(chart, "venus_sign")
        moon_s = _safe_sign(chart, "moon_sign")
        for outer_key in ("pluto_sign", "uranus_sign", "chiron_sign"):
            outer_s = _safe_sign(chart, outer_key)
            if venus_s and _is_hard_aspect_signs(venus_s, outer_s):
                high_voltage = True
                break
            if moon_s and _is_hard_aspect_signs(moon_s, outer_s):
                high_voltage = True
                break

    if high_voltage:
        psych_needs.append("潛意識被高波動、非常規的對象吸引")

    return high_voltage


# ── Rule 2: BaZi ─────────────────────────────────────────────────────────────

def _extract_bazi(
    chart: dict,
    target_elements: List[str],
    psych_needs: List[str],
) -> None:
    """Populate target_bazi_elements and psychological_needs."""
    # Chinese element name map
    _CN = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}

    day_master_element = chart.get("day_master_element", "")
    if day_master_element and day_master_element in GENERATION_CYCLE:
        # A generates B → complementary fire for wood, etc.
        generates = GENERATION_CYCLE[day_master_element]
        cn_gen = _CN.get(generates, generates)
        if cn_gen not in target_elements:
            target_elements.append(cn_gen)

        # What generates A? → what nurtures day master
        generated_by = next(
            (k for k, v in GENERATION_CYCLE.items() if v == day_master_element),
            None,
        )
        if generated_by:
            cn_by = _CN.get(generated_by, generated_by)
            if cn_by not in target_elements:
                target_elements.append(cn_by)

    # Day Branch 偏印 check (Chinese characters from bazi output)
    day_branch = chart.get("bazi_day_branch", "")
    if not day_branch:
        pillars = chart.get("four_pillars", {})
        day_pillar = pillars.get("day") or {}
        if isinstance(day_pillar, dict):
            day_branch = day_pillar.get("branch", "")

    if day_branch and day_branch in _PIAN_YIN_BRANCHES:
        if _INDIRECT_RESOURCE_NEED not in psych_needs:
            psych_needs.append(_INDIRECT_RESOURCE_NEED)


# ── Rule 3: ZWDS ──────────────────────────────────────────────────────────────

def _extract_zwds(
    chart: dict,
    zwds_tags: List[str],
    psych_needs: List[str],
) -> bool:
    """Populate zwds_partner_tags; return True if high-voltage detected.

    ZWDS structure expected:
      { "palaces": { "spouse": { "main_stars": [...], "malevolent_stars": [...] },
                     "career": { "main_stars": [...], ... } } }
    """
    high_voltage = False
    seen_tags: set = set(zwds_tags)

    palaces = chart.get("palaces", {})
    spouse = palaces.get("spouse") or {}
    raw_main = spouse.get("main_stars") or []

    # Detect true empty palace
    real_main = [s for s in raw_main if _strip_hua(s) in _ZWDS_MAIN_14]
    is_empty = spouse.get("is_empty", False) or len(real_main) == 0

    if is_empty:
        # Empty palace → borrow from career (官祿宮)
        career = palaces.get("career") or {}
        borrowed = career.get("main_stars") or []
        real_main = [s for s in borrowed if _strip_hua(s) in _ZWDS_MAIN_14]
        psych_needs.append("感情觀較具彈性，容易受環境或伴侶狀態影響")

    # Main star → group tags
    for star in real_main:
        base = _strip_hua(star)
        group = _STAR_TO_GROUP.get(base)
        if group:
            for tag in GROUP_TAGS.get(group, []):
                if tag not in seen_tags:
                    zwds_tags.append(tag)
                    seen_tags.add(tag)

    # Sha-stars (malevolent_stars)
    malevolent = spouse.get("malevolent_stars") or []
    for star in malevolent:
        info = AFFLICTION_STAR_MAP.get(star)
        if info:
            if info["dynamic"] == "high_voltage":
                high_voltage = True
            for tag in info["tags"]:
                if tag not in seen_tags:
                    zwds_tags.append(tag)
                    seen_tags.add(tag)
            if info["needs"] not in psych_needs:
                psych_needs.append(info["needs"])

    return high_voltage


# ── Public API ────────────────────────────────────────────────────────────────

def extract_ideal_partner_profile(
    western_chart: dict,
    bazi_chart: dict,
    zwds_chart: dict,
) -> dict:
    """Extract an ideal partner profile from three chart sources.

    Parameters
    ----------
    western_chart : dict
        Output of /calculate-chart.  May be ``{}`` for Tier 3 degradation.
    bazi_chart : dict
        BaZi dict (``chart_data["bazi"]``).  May be ``{}``.
    zwds_chart : dict
        ZWDS dict (output of compute_zwds_chart).  May be ``None`` or ``{}``.

    Returns
    -------
    dict
        target_western_signs   : List[str]
        target_bazi_elements   : List[str]
        relationship_dynamic   : str   ("stable" | "high_voltage")
        psychological_needs    : List[str]
        zwds_partner_tags      : List[str]
        karmic_match_required  : bool
    """
    western_chart = western_chart or {}
    bazi_chart = bazi_chart or {}
    zwds_chart = zwds_chart or {}

    target_signs:   List[str] = []
    target_elems:   List[str] = []
    psych_needs:    List[str] = []
    zwds_tags:      List[str] = []

    # Rule 1 — Western
    western_hv = _extract_western(western_chart, target_signs, psych_needs)

    # Rule 2 — BaZi
    _extract_bazi(bazi_chart, target_elems, psych_needs)

    # Rule 3 — ZWDS (never crash)
    zwds_hv = False
    if zwds_chart:
        try:
            zwds_hv = _extract_zwds(zwds_chart, zwds_tags, psych_needs)
        except Exception:
            pass

    # Aggregate dynamic
    dynamic = "high_voltage" if (western_hv or zwds_hv) else "stable"

    # Karmic flag: BOTH Western AND ZWDS must independently trigger high_voltage
    karmic = western_hv and zwds_hv

    return {
        "target_western_signs":  target_signs,
        "target_bazi_elements":  target_elems,
        "relationship_dynamic":  dynamic,
        "psychological_needs":   psych_needs,
        "zwds_partner_tags":     zwds_tags,
        "karmic_match_required": karmic,
    }
