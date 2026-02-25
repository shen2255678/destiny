# -*- coding: utf-8 -*-
"""
DESTINY — Ideal Partner Avatar Profiler (Sprint 4/6/8)

Reverse-engineers a single person's natal chart into "ideal partner" trait tags
for the recommendation system's first-pass DB filtering.

Five-layer extraction:
  Rule 1: Western Astrology — DSC, Venus, Mars, natal hard aspects
  Rule 1.5: Classical Astrology (V3) — dignity states, dispositor chain, natal mutual reception
  Rule 2: BaZi (八字)        — Day Master complement + Day Branch 偏印
  Rule 3: ZWDS (紫微斗數)    — Spouse palace stars, sha-stars, empty palace
  Rule 4: Ten Gods (十神)    — psychological needs from bazi ten gods
  Rule 5: Psychology merge   — attachment_style, venus/mars tags, favorable_elements

Public API:
    extract_ideal_partner_profile(western_chart, bazi_chart, zwds_chart, psychology_data) -> dict
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from bazi import GENERATION_CYCLE, compute_ten_gods, evaluate_day_master_strength
from psychology import (
    evaluate_planet_dignity,
    find_dispositor_chain,
)

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


# ── Ten Gods psychology mapping (Sprint 6) ───────────────────────────────────

_TEN_GOD_PSYCHOLOGY: Dict[str, Dict[str, Any]] = {
    "正印": {"need": "極度需要穩定與承諾；偏好溫和、具備長輩般包容力", "dynamic": "stable"},
    "偏印": {"need": "極度缺乏安全感，防備心重；需要極致偏愛", "dynamic": "high_voltage"},
    "正官": {"need": "重視對方社會價值與人品；需要體面、情緒穩定的伴侶", "dynamic": "stable"},
    "七殺": {"need": "外表強勢但內在渴望被征服；需要勢均力敵的對手", "dynamic": "high_voltage"},
    "正財": {"need": "感情觀極度務實；偏好生活規律、願意實質付出的對象", "dynamic": "stable"},
    "偏財": {"need": "追求戀愛的樂趣與新鮮感；容易被幽默不黏人的人吸引", "dynamic": None},
    "食神": {"need": "追求純粹快樂、無壓力的相處；需要懂生活脾氣好的伴侶", "dynamic": "stable"},
    "傷官": {"need": "討厭世俗管束與愚笨；容易被才華洋溢具獨特魅力的人吸引", "dynamic": "high_voltage"},
    "比肩": {"need": "感情觀如兄弟般平等；需要懂得分寸感給予獨立空間", "dynamic": None},
    "劫財": {"need": "感情容易充滿戲劇性與競爭感；需要極高情緒價值", "dynamic": "high_voltage"},
}

# Gods that are "high voltage" type
_HV_GODS = frozenset(["七殺", "偏印", "傷官", "劫財"])

# Conflict detection pairs
_CONFLICT_PAIRS = [
    (frozenset(["傷官", "正官"]), "內在充滿矛盾：理智渴望穩定，但潛意識被不穩定的人吸引"),
    (frozenset(["偏印", "食神"]), "容易有突發性憂鬱；極度需要情緒穩定、能提供安全感的伴侶"),
]

# Venus sign → aesthetic/romantic tag
_VENUS_SIGN_TAGS: Dict[str, str] = {
    "aries": "喜歡直接主動、帶有衝勁的人",
    "taurus": "重視感官享受、穩定與美感",
    "gemini": "容易被聰明健談、帶有知性魅力的人吸引",
    "cancer": "需要對方給予家庭般的溫暖與歸屬感",
    "leo": "被自信耀眼、懂得讚美自己的人吸引",
    "virgo": "重視對方的品格與生活細節",
    "libra": "追求優雅和諧，偏好社交能力強的伴侶",
    "scorpio": "審美帶有強烈神秘色彩，渴望深層連結",
    "sagittarius": "喜歡自由奔放、有冒險精神的對象",
    "capricorn": "偏好穩重有野心、腳踏實地的人",
    "aquarius": "被獨立思考、不隨波逐流的人吸引",
    "pisces": "容易被浪漫溫柔、具藝術氣質的人吸引",
}

# Mars sign → desire/passion tag
_MARS_SIGN_TAGS: Dict[str, str] = {
    "aries": "快速燃燒型，追求激情與征服",
    "taurus": "慢熱但持久，重視身體層面的連結",
    "gemini": "注重言語挑逗，心智刺激就是春藥",
    "cancer": "在安全感的包裹下才會釋放情慾",
    "leo": "需要被崇拜與注視，表演型慾望",
    "virgo": "克制表面下是細膩的感官需求",
    "libra": "追求均衡與美感，被優雅氣質點燃",
    "scorpio": "極致深層的佔有慾與控制慾",
    "sagittarius": "注重精神層面的火花與冒險快感",
    "capricorn": "務實而持久，權力動態中的慾望",
    "aquarius": "不走尋常路的慾望模式，重視精神獨立",
    "pisces": "夢幻而柔軟，容易在幻想中燃燒",
}


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


# ── Rule 4: Ten Gods Psychological Extraction (Sprint 6) ─────────────────────

def _extract_ten_gods(
    bazi_chart: dict,
    psych_needs: List[str],
) -> tuple:
    """Extract psychological needs from Ten Gods.

    Returns (ten_gods_hv: bool, psychological_conflict: bool).
    """
    ten_gods_hv = False
    psychological_conflict = False

    try:
        tg = compute_ten_gods(bazi_chart)
    except Exception:
        return False, False

    if not tg or not tg.get("god_counts"):
        return False, False

    god_counts = tg.get("god_counts", {})
    spouse_god = tg.get("spouse_palace_god")
    hour_known = bazi_chart.get("hour_known", False)

    # Dynamic threshold: Tier 1 (8 chars) >= 3 to be "偏旺"; Tier 3 (6 chars) >= 2
    dominant_threshold = 3 if hour_known else 2

    triggered_gods: set = set()

    # Check each god for 偏旺 (above threshold) or spouse palace presence
    for god, info in _TEN_GOD_PSYCHOLOGY.items():
        count = god_counts.get(god, 0)
        is_dominant = count >= dominant_threshold
        is_spouse = (spouse_god == god)

        if is_dominant or is_spouse:
            triggered_gods.add(god)
            need = info["need"]
            if need not in psych_needs:
                psych_needs.append(need)
            if info["dynamic"] == "high_voltage":
                ten_gods_hv = True

    # Spouse palace HV gods always trigger even if not 偏旺
    if spouse_god and spouse_god in _HV_GODS and spouse_god not in triggered_gods:
        info = _TEN_GOD_PSYCHOLOGY.get(spouse_god)
        if info:
            need = info["need"]
            if need not in psych_needs:
                psych_needs.append(need)
            ten_gods_hv = True

    # Conflict detection: 傷官見官 / 梟神奪食
    all_gods_present = set(god_counts.keys()) | ({spouse_god} if spouse_god else set())
    for pair, conflict_msg in _CONFLICT_PAIRS:
        if pair.issubset(all_gods_present):
            psychological_conflict = True
            if conflict_msg not in psych_needs:
                psych_needs.append(conflict_msg)

    return ten_gods_hv, psychological_conflict


# ── Rule 5: Psychology & Venus/Mars merge (Sprint 8) ──────────────────────────

def _extract_venus_mars_tags(western_chart: dict) -> List[str]:
    """Extract Venus and Mars sign-based psychological tags."""
    tags: List[str] = []
    venus = _safe_sign(western_chart, "venus_sign")
    if venus and venus in _VENUS_SIGN_TAGS:
        tags.append(f"金星{venus.capitalize()}：{_VENUS_SIGN_TAGS[venus]}")

    mars = _safe_sign(western_chart, "mars_sign")
    if mars and mars in _MARS_SIGN_TAGS:
        tags.append(f"火星{mars.capitalize()}：{_MARS_SIGN_TAGS[mars]}")

    return tags


# ── Classical Astrology layer constants (V3) ─────────────────────────────────

_DISPOSITOR_BOSS_TAGS: Dict[str, str] = {
    "Pluto":   "潛意識底層受到強烈的業力驅動，比起輕鬆的愛，更看重深刻的靈魂綁定或世俗成就的共同成長",
    "Saturn":  "潛意識底層受到強烈的業力驅動，比起輕鬆的愛，更看重深刻的靈魂綁定或世俗成就的共同成長",
    "Venus":   "生命底層渴望和諧與豐盛，感情中極度需要情緒價值、美感與享受",
    "Jupiter": "生命底層渴望和諧與豐盛，感情中極度需要情緒價值、美感與享受",
    "Uranus":  "極度需要心智上的刺激與靈魂自由，討厭沉悶與傳統的感情束縛",
    "Mercury": "極度需要心智上的刺激與靈魂自由，討厭沉悶與傳統的感情束縛",
}

_NATAL_MR_TAGS: Dict[Any, Dict[str, Any]] = {
    frozenset({"Venus", "Mars"}): {
        "need": "情慾與愛情的表達充滿張力與宿命感，容易在感情中產生強烈的執念、佔有慾與投射",
        "dynamic": "high_voltage",
    },
    frozenset({"Sun", "Moon"}): {
        "need": "內在意志與情緒極度自洽，但也容易固執己見，感情中需要完全的包容與認同",
        "dynamic": None,
    },
    frozenset({"Venus", "Jupiter"}): {
        "need": "感情中擁有強大的滋養能力，追求極致的浪漫、美感與情緒價值",
        "dynamic": None,
    },
    frozenset({"Venus", "Moon"}): {
        "need": "感情中擁有強大的滋養能力，追求極致的浪漫、美感與情緒價值",
        "dynamic": None,
    },
}


def _extract_classical_astrology_layer(
    western_chart: dict,
    psych_needs: List[str],
) -> Optional[str]:
    """Rule 1.5: Classical astrology — dignity states, dispositor chain, natal mutual reception.

    Returns relationship_dynamic hint: "high_voltage" | "stable" | None.
    Tier 3 safe: missing moon_sign is silently skipped.
    """
    dynamic_hint: Optional[str] = None

    # Step 1 — Dignity states (Venus + Moon)
    for planet, sign_key in (("Venus", "venus_sign"), ("Moon", "moon_sign")):
        sign = western_chart.get(sign_key)
        if not sign:
            continue
        state = evaluate_planet_dignity(planet, sign)
        if state in ("Detriment", "Fall"):
            need = "感情中容易缺乏安全感，帶有較強的執念、防禦機制與測試心理"
            if need not in psych_needs:
                psych_needs.append(need)
            dynamic_hint = "high_voltage"
        elif state in ("Dignity", "Exaltation"):
            need = "感情需求直接且純粹，有能力給予並享受穩定的愛"
            if need not in psych_needs:
                psych_needs.append(need)
            if dynamic_hint is None:
                dynamic_hint = "stable"

    # Step 2 — Final Dispositor (潛意識大 Boss) from Sun/Moon/Venus/Mars chains
    boss_counts: Dict[str, int] = {}
    for planet in ("Sun", "Moon", "Venus", "Mars"):
        result = find_dispositor_chain(western_chart, planet)
        if result["status"] == "final_dispositor" and result["final_dispositor"]:
            boss = result["final_dispositor"]
            boss_counts[boss] = boss_counts.get(boss, 0) + 1

    if boss_counts:
        top_boss = max(boss_counts, key=lambda b: boss_counts[b])
        tag = _DISPOSITOR_BOSS_TAGS.get(top_boss)
        if tag and tag not in psych_needs:
            psych_needs.append(tag)

    # Step 3 — Natal Mutual Reception detection
    seen_mr_pairs: set = set()
    for planet in ("Sun", "Moon", "Venus", "Mars"):
        result = find_dispositor_chain(western_chart, planet)
        if result["status"] == "mutual_reception" and len(result["mutual_reception"]) >= 2:
            pair = frozenset(result["mutual_reception"][:2])
            if pair in seen_mr_pairs:
                continue
            seen_mr_pairs.add(pair)
            mr_info = _NATAL_MR_TAGS.get(pair)
            if mr_info:
                need = mr_info["need"]
                if need not in psych_needs:
                    psych_needs.append(need)
                if mr_info["dynamic"] == "high_voltage":
                    dynamic_hint = "high_voltage"

    return dynamic_hint


# ── Public API ────────────────────────────────────────────────────────────────

def extract_ideal_partner_profile(
    western_chart: dict,
    bazi_chart: dict,
    zwds_chart: dict,
    psychology_data: dict = None,
) -> dict:
    """Extract an ideal partner profile from chart sources + psychology data.

    Parameters
    ----------
    western_chart : dict
        Output of /calculate-chart.  May be ``{}`` for Tier 3 degradation.
    bazi_chart : dict
        BaZi dict (``chart_data["bazi"]``).  May be ``{}``.
    zwds_chart : dict
        ZWDS dict (output of compute_zwds_chart).  May be ``None`` or ``{}``.
    psychology_data : dict
        Output of psychology.py.  May be ``None`` or ``{}``.

    Returns
    -------
    dict
        target_western_signs    : List[str]
        target_bazi_elements    : List[str]
        relationship_dynamic    : str   ("stable" | "high_voltage")
        psychological_needs     : List[str]
        zwds_partner_tags       : List[str]
        karmic_match_required   : bool
        attachment_style         : str | None
        psychological_conflict  : bool
        venus_mars_tags         : List[str]
        favorable_elements      : List[str]
    """
    western_chart = western_chart or {}
    bazi_chart = bazi_chart or {}
    zwds_chart = zwds_chart or {}
    psychology_data = psychology_data or {}

    target_signs:   List[str] = []
    target_elems:   List[str] = []
    psych_needs:    List[str] = []
    zwds_tags:      List[str] = []

    # Rule 1 — Western
    western_hv = _extract_western(western_chart, target_signs, psych_needs)

    # Rule 1.5 — Classical Astrology (V3): dignity + dispositor chain + natal MR
    classical_dynamic: Optional[str] = None
    try:
        classical_dynamic = _extract_classical_astrology_layer(western_chart, psych_needs)
    except Exception:
        pass

    # Rule 2 — BaZi elements
    _extract_bazi(bazi_chart, target_elems, psych_needs)

    # Rule 3 — ZWDS (never crash)
    zwds_hv = False
    if zwds_chart:
        try:
            zwds_hv = _extract_zwds(zwds_chart, zwds_tags, psych_needs)
        except Exception:
            pass

    # Rule 4 — Ten Gods (Sprint 6)
    ten_gods_hv = False
    psychological_conflict = False
    if bazi_chart:
        try:
            ten_gods_hv, psychological_conflict = _extract_ten_gods(bazi_chart, psych_needs)
        except Exception:
            pass

    # Rule 5 — Psychology & Venus/Mars merge (Sprint 8)
    attachment_style = psychology_data.get("attachment_style")
    if attachment_style:
        _ATTACH_NEEDS = {
            "anxious": "高焦慮依附：極度需要回應與確認，害怕被拋棄",
            "avoidant": "逃避型依附：需要大量獨處空間，親密感會引發壓力",
            "disorganized": "混亂型依附：同時渴望又害怕親密，關係模式矛盾",
        }
        attach_need = _ATTACH_NEEDS.get(attachment_style)
        if attach_need and attach_need not in psych_needs:
            psych_needs.append(attach_need)

    venus_mars_tags = _extract_venus_mars_tags(western_chart)

    # Favorable elements from bazi strength analysis
    favorable_elements: List[str] = []
    try:
        dms = evaluate_day_master_strength(bazi_chart)
        favorable_elements = dms.get("favorable_elements", [])
    except Exception:
        pass

    # Aggregate dynamic: any source triggering HV makes overall HV
    classical_hv = (classical_dynamic == "high_voltage")
    dynamic = "high_voltage" if (western_hv or zwds_hv or ten_gods_hv or classical_hv) else "stable"

    # Karmic flag: BOTH Western AND ZWDS must independently trigger high_voltage
    karmic = western_hv and zwds_hv

    return {
        "target_western_signs":   target_signs,
        "target_bazi_elements":   target_elems,
        "relationship_dynamic":   dynamic,
        "psychological_needs":    psych_needs,
        "zwds_partner_tags":      zwds_tags,
        "karmic_match_required":  karmic,
        "attachment_style":       attachment_style,
        "psychological_conflict": psychological_conflict,
        "venus_mars_tags":        venus_mars_tags,
        "favorable_elements":     favorable_elements,
    }
