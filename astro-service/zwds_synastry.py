"""
DESTINY — ZiWei DouShu Synastry Engine
Computes track modifiers from ZWDS charts (Phase H).

Three mechanisms:
  1. Flying Stars (飛星四化): 化祿→partner, 化忌→soul, 化権→RPV
  2. Star Archetypes (主星人設): life palace cluster → track multipliers
  3. Stress Defense (煞星防禦): spouse palace malevolent stars → trigger labels
"""
from __future__ import annotations
from typing import Optional

from zwds import OPPOSITE_PALACE, PALACE_NAMES_ZH, PALACE_KEYS

# ── Star Archetype Matrix ──────────────────────────────────────────────────────
# Each star → {"cluster", "passion", "partner", "friend", "soul", "rpv_frame_bonus"}
STAR_ARCHETYPE_MATRIX = {
    # 殺破狼 cluster
    "七殺": {"cluster": "殺破狼", "passion": 1.3, "partner": 0.8, "friend": 1.0, "soul": 1.0, "rpv_frame_bonus": 15},
    "破軍": {"cluster": "殺破狼", "passion": 1.3, "partner": 0.8, "friend": 1.0, "soul": 1.0, "rpv_frame_bonus": 15},
    "貪狼": {"cluster": "殺破狼", "passion": 1.3, "partner": 0.8, "friend": 1.0, "soul": 1.0, "rpv_frame_bonus": 15},
    # 紫府武相 cluster
    "紫微": {"cluster": "紫府武相", "passion": 1.0, "partner": 1.3, "friend": 1.0, "soul": 0.8, "rpv_frame_bonus": 10},
    "天府": {"cluster": "紫府武相", "passion": 1.0, "partner": 1.3, "friend": 1.0, "soul": 0.8, "rpv_frame_bonus": 10},
    "武曲": {"cluster": "紫府武相", "passion": 1.0, "partner": 1.3, "friend": 1.0, "soul": 0.8, "rpv_frame_bonus": 10},
    "天相": {"cluster": "紫府武相", "passion": 1.0, "partner": 1.3, "friend": 1.0, "soul": 0.8, "rpv_frame_bonus": 5},
    # 機月同梁 cluster
    "天機": {"cluster": "機月同梁", "passion": 0.8, "partner": 1.0, "friend": 1.3, "soul": 1.3, "rpv_frame_bonus": -10},
    "太陰": {"cluster": "機月同梁", "passion": 0.8, "partner": 1.2, "friend": 1.2, "soul": 1.3, "rpv_frame_bonus": -10},
    "天同": {"cluster": "機月同梁", "passion": 0.8, "partner": 1.0, "friend": 1.3, "soul": 1.3, "rpv_frame_bonus": -10},
    "天梁": {"cluster": "機月同梁", "passion": 0.8, "partner": 1.0, "friend": 1.3, "soul": 1.3, "rpv_frame_bonus": -5},
    # 巨日 group
    "太陽": {"cluster": "巨日",   "passion": 1.0, "partner": 1.2, "friend": 1.1, "soul": 1.0, "rpv_frame_bonus": 5},
    "巨門": {"cluster": "巨日",   "passion": 1.0, "partner": 1.0, "friend": 1.0, "soul": 1.2, "rpv_frame_bonus": 0},
    # 廉貞
    "廉貞": {"cluster": "廉貞",   "passion": 1.2, "partner": 1.0, "friend": 1.0, "soul": 1.1, "rpv_frame_bonus": 5},
}

# ── Stress defense trigger groups ─────────────────────────────────────────────
_PREEMPTIVE = {"擎羊", "火星"}
_RUMINATION = {"陀羅", "鈴星"}
_WITHDRAWAL = {"天空", "地劫"}

# ── Key palace sets for flying star targeting ─────────────────────────────────
_PARTNER_PALACES = {"ming", "spouse", "body"}   # body = 身宮 (matched by body_palace_name key)
_SOUL_PALACES    = {"ming", "spouse", "karma"}
_DOM_PALACES     = {"ming"}


# ── Helper: get a star's base name (strip 化X suffix) ─────────────────────────
def _base(star: str) -> str:
    for suffix in ("化祿","化権","化科","化忌"):
        if star.endswith(suffix):
            return star[:-len(suffix)]
    return star


def _get_cluster(chart: dict) -> str:
    """Get the archetype cluster name from the 命宮 main stars."""
    ming_stars = chart["palaces"].get("ming", {}).get("main_stars", [])
    for s in ming_stars:
        base = _base(s)
        if base in STAR_ARCHETYPE_MATRIX:
            return STAR_ARCHETYPE_MATRIX[base]["cluster"]
    return "mixed"


def get_palace_energy(chart: dict, palace_key: str) -> dict:
    """Return stars for a palace, borrowing from opposite at 0.8x if empty."""
    palace = chart["palaces"].get(palace_key, {})
    own_stars = palace.get("main_stars", [])
    if own_stars:
        return {"stars": own_stars, "strength": 1.0, "is_chameleon": False}
    # Empty palace — borrow from opposite
    opp_key = OPPOSITE_PALACE.get(palace_key)
    borrowed = chart["palaces"].get(opp_key, {}).get("main_stars", []) if opp_key else []
    return {"stars": borrowed, "strength": 0.8, "is_chameleon": True}


def detect_stress_defense(chart: dict) -> list:
    """Detect 壓力防禦機制 from malevolent stars in the spouse palace (夫妻宮)."""
    spouse = chart["palaces"].get("spouse", {})
    malevolent = set(spouse.get("malevolent_stars", []))
    triggers = []
    if malevolent & _PREEMPTIVE:
        triggers.append("preemptive_strike")
    if malevolent & _RUMINATION:
        triggers.append("silent_rumination")
    if malevolent & _WITHDRAWAL:
        triggers.append("sudden_withdrawal")
    return triggers


def get_star_archetype_mods(chart: dict) -> dict:
    """Compute per-user track modifiers from their 命宮 star archetypes.

    For empty 命宮: apply chameleon penalty (RPV -10, all tracks neutral).
    For multiple main stars: average the track modifiers.
    """
    energy = get_palace_energy(chart, "ming")
    if energy["is_chameleon"]:
        return {"passion": 1.0, "partner": 1.0, "friend": 1.0, "soul": 1.0,
                "rpv_frame_bonus": -10}

    mods = {"passion": 0.0, "partner": 0.0, "friend": 0.0, "soul": 0.0, "rpv_frame_bonus": 0}
    stars = [_base(s) for s in energy["stars"]]
    matched = [STAR_ARCHETYPE_MATRIX[s] for s in stars if s in STAR_ARCHETYPE_MATRIX]

    if not matched:
        return {"passion": 1.0, "partner": 1.0, "friend": 1.0, "soul": 1.0, "rpv_frame_bonus": 0}

    for field in ("passion", "partner", "friend", "soul"):
        mods[field] = sum(m[field] for m in matched) / len(matched)
    mods["rpv_frame_bonus"] = sum(m["rpv_frame_bonus"] for m in matched) // len(matched)
    return mods


def _star_in_key_palaces(star_name: str, target_chart: dict, palace_keys: set) -> bool:
    """Check if a base star name appears as a main star in any of the target's key palaces."""
    for key in palace_keys:
        if key == "body":
            continue  # body is handled separately below
        palace = target_chart["palaces"].get(key, {})
        for s in palace.get("main_stars", []):
            if _base(s) == star_name:
                return True
    # Also check body palace by name if "body" is in palace_keys
    if "body" in palace_keys:
        body_name = target_chart.get("body_palace_name", "")
        if body_name in PALACE_NAMES_ZH:
            body_key = PALACE_KEYS[PALACE_NAMES_ZH.index(body_name)]
            palace = target_chart["palaces"].get(body_key, {})
            for s in palace.get("main_stars", []):
                if _base(s) == star_name:
                    return True
    return False


def _spouse_palace_match(chart_a: dict, chart_b: dict) -> bool:
    """Check if A's spouse palace main stars appear in B's life palace (靜態天菜雷達)."""
    a_spouse = [_base(s) for s in chart_a["palaces"].get("spouse", {}).get("main_stars", [])]
    b_ming   = [_base(s) for s in chart_b["palaces"].get("ming", {}).get("main_stars", [])]
    return any(s in b_ming for s in a_spouse)


def _compute_flying_stars(chart_a: dict, birth_year_a: int, chart_b: dict) -> dict:
    """Compute 飛星四化 interaction: which palaces A's transformation stars hit in B."""
    from zwds import get_four_transforms
    trans_a = get_four_transforms(birth_year_a)
    return {
        "hua_lu_a_to_b":    _star_in_key_palaces(trans_a["hua_lu"],   chart_b, _PARTNER_PALACES),
        "hua_ji_a_to_b":    _star_in_key_palaces(trans_a["hua_ji"],   chart_b, _SOUL_PALACES),
        "hua_quan_a_to_b":  _star_in_key_palaces(trans_a["hua_quan"], chart_b, _DOM_PALACES),
        "hua_lu_b_to_a":    False,  # caller fills in B→A direction
        "hua_ji_b_to_a":    False,
        "hua_quan_b_to_a":  False,
        "spouse_match_a_sees_b": _spouse_palace_match(chart_a, chart_b),
    }


def _compute_spiciness(track_mods: dict, defense_a: list, defense_b: list) -> str:
    """Classify the overall spiciness level of this pairing."""
    passion  = track_mods.get("passion", 1.0)
    partner  = track_mods.get("partner", 1.0)
    soul     = track_mods.get("soul", 1.0)
    has_withdrawal = "sudden_withdrawal" in defense_a or "sudden_withdrawal" in defense_b

    if soul >= 1.4 and partner >= 1.3:
        return "SOULMATE"
    if passion >= 1.3 and soul >= 1.2:
        return "HIGH_VOLTAGE"
    if has_withdrawal or (passion >= 1.2 and partner <= 0.8):
        return "HIGH_VOLTAGE"
    if passion >= 1.2 or soul >= 1.2 or partner >= 1.2:
        return "MEDIUM"
    return "STABLE"


def compute_zwds_synastry(
    chart_a: dict, birth_year_a: int,
    chart_b: dict, birth_year_b: int,
) -> dict:
    """Compute full ZWDS synastry result for two charts.

    Returns:
        track_mods:       {friend, passion, partner, soul} multipliers (apply × to existing tracks)
        rpv_modifier:     int added to RPV power frame
        defense_a:        list of stress-defense trigger labels for User A
        defense_b:        list of stress-defense trigger labels for User B
        flying_stars:     raw flying-star hit flags
        spiciness_level:  STABLE | MEDIUM | HIGH_VOLTAGE | SOULMATE
        layered_analysis: {karmic_link, energy_dynamic, archetype_cluster_a, archetype_cluster_b}
    """
    from zwds import get_four_transforms

    # ── Flying stars (bidirectional) ──────────────────────────────────────
    fs_ab = _compute_flying_stars(chart_a, birth_year_a, chart_b)
    trans_b = get_four_transforms(birth_year_b)
    fs_ab["hua_lu_b_to_a"]   = _star_in_key_palaces(trans_b["hua_lu"],   chart_a, _PARTNER_PALACES)
    fs_ab["hua_ji_b_to_a"]   = _star_in_key_palaces(trans_b["hua_ji"],   chart_a, _SOUL_PALACES)
    fs_ab["hua_quan_b_to_a"] = _star_in_key_palaces(trans_b["hua_quan"], chart_a, _DOM_PALACES)

    # ── Flying star track modifiers ───────────────────────────────────────
    track_mods = {"friend": 1.0, "passion": 1.0, "partner": 1.0, "soul": 1.0}
    rpv_modifier = 0

    # 化祿
    if fs_ab["hua_lu_a_to_b"] and fs_ab["hua_lu_b_to_a"]:
        track_mods["partner"] *= 1.4  # Mutual 化祿: SSR jackpot
    elif fs_ab["hua_lu_a_to_b"] or fs_ab["hua_lu_b_to_a"]:
        track_mods["partner"] *= 1.2

    # 化忌
    if fs_ab["hua_ji_a_to_b"] and fs_ab["hua_ji_b_to_a"]:
        track_mods["soul"]    *= 1.5   # Mutual 化忌: 業力虐戀
        track_mods["partner"] *= 0.9
    elif fs_ab["hua_ji_a_to_b"] or fs_ab["hua_ji_b_to_a"]:
        track_mods["soul"]    *= 1.3
        track_mods["partner"] *= 0.9

    # 化権 (RPV only, not tracks)
    if fs_ab["hua_quan_a_to_b"] and not fs_ab["hua_quan_b_to_a"]:
        rpv_modifier += 15   # A natural Dom
    elif fs_ab["hua_quan_b_to_a"] and not fs_ab["hua_quan_a_to_b"]:
        rpv_modifier -= 15   # B natural Dom → A shifts Sub

    # 靜態天菜雷達 (spouse palace match)
    if fs_ab["spouse_match_a_sees_b"]:
        track_mods["friend"] *= 1.2

    # ── Star archetypes (命宮 cluster) ────────────────────────────────────
    arch_a = get_star_archetype_mods(chart_a)
    arch_b = get_star_archetype_mods(chart_b)
    # Average the two users' archetypes for the pair
    for t in ("friend", "passion", "partner", "soul"):
        track_mods[t] *= (arch_a[t] + arch_b[t]) / 2
    rpv_modifier += arch_a["rpv_frame_bonus"] + arch_b["rpv_frame_bonus"]

    # ── Empty palace RPV penalty ──────────────────────────────────────────
    if chart_a["palaces"].get("ming", {}).get("is_empty"):
        rpv_modifier -= 10

    # ── Stress defense (夫妻宮 煞星) ──────────────────────────────────────
    defense_a = detect_stress_defense(chart_a)
    defense_b = detect_stress_defense(chart_b)

    _DEFENSE_MODS = {
        "preemptive_strike": {"passion": 1.2, "partner": 0.8},
        "silent_rumination": {"soul": 1.3, "friend": 0.85},
        "sudden_withdrawal": {"partner": 0.6, "soul": 1.2},
    }
    for trigger in set(defense_a) | set(defense_b):
        for t, mod in _DEFENSE_MODS.get(trigger, {}).items():
            track_mods[t] *= mod

    # Round modifiers
    track_mods = {k: round(v, 3) for k, v in track_mods.items()}

    # ── Spiciness level ───────────────────────────────────────────────────
    spiciness = _compute_spiciness(track_mods, defense_a, defense_b)

    # ── Layered analysis ──────────────────────────────────────────────────
    karmic = []
    if fs_ab["hua_ji_a_to_b"] and fs_ab["hua_ji_b_to_a"]:
        karmic.append("mutual_hua_ji (業力虐戀)")
    elif fs_ab["hua_ji_a_to_b"] or fs_ab["hua_ji_b_to_a"]:
        karmic.append("one_way_hua_ji (業力單箭)")
    energy_dyn = []
    if fs_ab["hua_quan_a_to_b"]:
        energy_dyn.append("A_Dom_natural (化権)")
    if fs_ab["hua_quan_b_to_a"]:
        energy_dyn.append("B_Dom_natural (化権)")

    return {
        "track_mods":      track_mods,
        "rpv_modifier":    rpv_modifier,
        "defense_a":       defense_a,
        "defense_b":       defense_b,
        "flying_stars":    fs_ab,
        "spiciness_level": spiciness,
        "layered_analysis": {
            "karmic_link":           karmic,
            "energy_dynamic":        energy_dyn,
            "archetype_cluster_a":   _get_cluster(chart_a),
            "archetype_cluster_b":   _get_cluster(chart_b),
        },
    }
