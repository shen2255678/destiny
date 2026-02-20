"""
DESTINY — Matching Algorithm
Computes compatibility scores between two user profiles.

Match_Score = (Kernel_Compatibility × 0.5) + (Power_Dynamic_Fit × 0.3) + (Glitch_Tolerance × 0.2)

Kernel: Western astrology sign aspects + BaZi five-element harmony
Power:  RPV cross-matching (conflict × power × energy)
Glitch: Mars/Saturn tension tolerance
"""

from __future__ import annotations

from typing import Dict, List, Optional

from bazi import analyze_element_relation

# ── Zodiac Constants ─────────────────────────────────────────

SIGNS = [
    "aries", "taurus", "gemini", "cancer",
    "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
]

SIGN_INDEX = {sign: i for i, sign in enumerate(SIGNS)}

# Sign → Western element (fire/earth/air/water)
SIGN_ELEMENT = {
    "aries": "fire", "taurus": "earth", "gemini": "air", "cancer": "water",
    "leo": "fire", "virgo": "earth", "libra": "air", "scorpio": "water",
    "sagittarius": "fire", "capricorn": "earth", "aquarius": "air", "pisces": "water",
}

# Aspect scores by house distance (0-6)
ASPECT_SCORES = {
    0: 0.90,  # conjunction (same sign)
    1: 0.65,  # semi-sextile (minor)
    2: 0.75,  # sextile
    3: 0.50,  # square
    4: 0.85,  # trine
    5: 0.65,  # quincunx (minor)
    6: 0.60,  # opposition
}

# Deterministic tag pools per match type
TAG_POOLS = {
    "complementary": [
        "Magnetic", "Nurturing", "Grounding",
        "Devoted", "Harmonious", "Intuitive",
    ],
    "similar": [
        "Kindred", "Reflective", "Steady",
        "Empathic", "Familiar", "Flowing",
    ],
    "tension": [
        "Unpredictable", "Intense", "Transformative",
        "Catalytic", "Challenging", "Electric",
    ],
}


# ── Sign Aspect Scoring ─────────────────────────────────────

def compute_sign_aspect(sign_a: Optional[str], sign_b: Optional[str]) -> float:
    """Compute aspect score between two zodiac signs (0.0-1.0).

    Returns 0.65 (neutral) if either sign is None or invalid.
    """
    if not sign_a or not sign_b:
        return 0.65
    if sign_a not in SIGN_INDEX or sign_b not in SIGN_INDEX:
        return 0.65

    distance = abs(SIGN_INDEX[sign_a] - SIGN_INDEX[sign_b]) % 12
    if distance > 6:
        distance = 12 - distance

    return ASPECT_SCORES.get(distance, 0.65)


# ── Kernel Compatibility (50%) ───────────────────────────────

def compute_kernel_score(user_a: dict, user_b: dict) -> float:
    """Compute Kernel Compatibility (0.0-1.0).

    Tier-based weighting:
      Tier 1: Sun(0.20) + Moon(0.25) + Venus(0.25) + Ascendant(0.15) + BaZi(0.15)
      Tier 2: Sun(0.25) + Moon(0.20) + Venus(0.25) + BaZi(0.30)
      Tier 3: Sun(0.30) + Venus(0.30) + BaZi(0.40)
    """
    tier_a = user_a.get("data_tier", 3)
    tier_b = user_b.get("data_tier", 3)
    effective_tier = max(tier_a, tier_b)  # degrade to worst

    sun = compute_sign_aspect(user_a.get("sun_sign"), user_b.get("sun_sign"))
    moon = compute_sign_aspect(user_a.get("moon_sign"), user_b.get("moon_sign"))
    venus = compute_sign_aspect(user_a.get("venus_sign"), user_b.get("venus_sign"))
    asc = compute_sign_aspect(user_a.get("ascendant_sign"), user_b.get("ascendant_sign"))

    # BaZi harmony
    bazi = 0.65  # neutral default
    elem_a = user_a.get("bazi_element")
    elem_b = user_b.get("bazi_element")
    if elem_a and elem_b:
        relation = analyze_element_relation(elem_a, elem_b)
        bazi = relation["harmony_score"]

    if effective_tier == 1:
        return sun * 0.20 + moon * 0.25 + venus * 0.25 + asc * 0.15 + bazi * 0.15
    elif effective_tier == 2:
        return sun * 0.25 + moon * 0.20 + venus * 0.25 + bazi * 0.30
    else:
        return sun * 0.30 + venus * 0.30 + bazi * 0.40


# ── Power Dynamic Fit (30%) ──────────────────────────────────

def compute_power_score(user_a: dict, user_b: dict) -> float:
    """Compute Power Dynamic Fit (0.0-1.0).

    RPV cross-matching:
      conflict: complementary (different) = 0.85, same = 0.55
      power:    complementary (control↔follow) = 0.90, same = 0.50
      energy:   complementary (different) = 0.75, same = 0.65
    Weights: conflict × 0.35 + power × 0.40 + energy × 0.25
    """
    c_a = user_a.get("rpv_conflict")
    c_b = user_b.get("rpv_conflict")
    conflict = (0.85 if c_a != c_b else 0.55) if (c_a and c_b) else 0.60

    p_a = user_a.get("rpv_power")
    p_b = user_b.get("rpv_power")
    power = (0.90 if p_a != p_b else 0.50) if (p_a and p_b) else 0.60

    e_a = user_a.get("rpv_energy")
    e_b = user_b.get("rpv_energy")
    energy = (0.75 if e_a != e_b else 0.65) if (e_a and e_b) else 0.60

    return conflict * 0.35 + power * 0.40 + energy * 0.25


# ── Glitch Tolerance (20%) ───────────────────────────────────

def compute_glitch_score(user_a: dict, user_b: dict) -> float:
    """Compute Glitch Tolerance (0.0-1.0).

    Mars/Saturn cross-aspects:
      - mars_a vs mars_b: conflict style
      - saturn_a vs saturn_b: boundaries
      - mars_a vs saturn_b and vice versa: friction triggers
    Higher score = higher tolerance (less destructive friction).
    """
    mars = compute_sign_aspect(user_a.get("mars_sign"), user_b.get("mars_sign"))
    saturn = compute_sign_aspect(user_a.get("saturn_sign"), user_b.get("saturn_sign"))
    mars_sat_ab = compute_sign_aspect(user_a.get("mars_sign"), user_b.get("saturn_sign"))
    mars_sat_ba = compute_sign_aspect(user_b.get("mars_sign"), user_a.get("saturn_sign"))

    return mars * 0.25 + saturn * 0.25 + mars_sat_ab * 0.25 + mars_sat_ba * 0.25


# ── Match Classification ─────────────────────────────────────

def classify_match_type(kernel: float, power: float, glitch: float) -> str:
    """Classify match: complementary / similar / tension.

    complementary: strong polarity fit (power ≥ 0.75 and kernel ≥ 0.7)
    similar:       harmonic resonance (kernel ≥ 0.75 and glitch ≥ 0.6)
    tension:       growth-oriented friction (everything else)
    """
    if power >= 0.75 and kernel >= 0.70:
        return "complementary"
    if kernel >= 0.75 and glitch >= 0.60:
        return "similar"
    return "tension"


def assign_card_color(match_type: str) -> str:
    """Map match_type to card_color."""
    return {
        "complementary": "coral",
        "similar": "blue",
        "tension": "purple",
    }.get(match_type, "purple")


# ── Radar Scores ─────────────────────────────────────────────

def compute_radar_scores(
    user_a: dict, user_b: dict, scores: dict
) -> Dict[str, int]:
    """Compute radar chart values (0-100 each).

    passion:       Venus aspect + Mars aspect + power_score blend
    stability:     Saturn aspect + BaZi harmony proxy + energy compatibility
    communication: Moon aspect + Sun aspect (Mercury proxy) + conflict style
    """
    venus = compute_sign_aspect(user_a.get("venus_sign"), user_b.get("venus_sign"))
    mars = compute_sign_aspect(user_a.get("mars_sign"), user_b.get("mars_sign"))
    moon = compute_sign_aspect(user_a.get("moon_sign"), user_b.get("moon_sign"))
    sun = compute_sign_aspect(user_a.get("sun_sign"), user_b.get("sun_sign"))
    saturn = compute_sign_aspect(user_a.get("saturn_sign"), user_b.get("saturn_sign"))

    power = scores.get("power_score", 0.6)
    kernel = scores.get("kernel_score", 0.6)
    glitch = scores.get("glitch_score", 0.6)

    passion_raw = venus * 0.35 + mars * 0.30 + power * 0.35
    stability_raw = saturn * 0.30 + kernel * 0.40 + (1.0 - glitch) * 0.10 + glitch * 0.20
    communication_raw = moon * 0.35 + sun * 0.30 + power * 0.35

    return {
        "passion": _clamp_100(passion_raw),
        "stability": _clamp_100(stability_raw),
        "communication": _clamp_100(communication_raw),
    }


def _clamp_100(value: float) -> int:
    """Scale 0.0-1.0 to 0-100 and clamp."""
    return max(0, min(100, int(round(value * 100))))


# ── Tag Generation ───────────────────────────────────────────

def generate_tags(match_type: str, scores: dict) -> List[str]:
    """Generate 3 deterministic chameleon tags based on match_type and scores.

    Uses total_score thresholds to select from a pool of 6 tags.
    """
    pool = TAG_POOLS.get(match_type, TAG_POOLS["tension"])
    total = scores.get("total_score", 0.5)

    # Deterministic selection: pick indices based on score ranges
    if total >= 0.80:
        indices = [0, 1, 2]  # top tags
    elif total >= 0.65:
        indices = [0, 2, 3]
    elif total >= 0.50:
        indices = [1, 3, 4]
    else:
        indices = [2, 4, 5]

    return [pool[i] for i in indices]


# ── Main Scoring Function ────────────────────────────────────

def compute_match_score(user_a: dict, user_b: dict) -> dict:
    """Compute full match score with breakdown.

    Returns dict with: kernel_score, power_score, glitch_score, total_score,
    match_type, radar_passion, radar_stability, radar_communication,
    card_color, tags.
    """
    kernel = compute_kernel_score(user_a, user_b)
    power = compute_power_score(user_a, user_b)
    glitch = compute_glitch_score(user_a, user_b)
    total = kernel * 0.5 + power * 0.3 + glitch * 0.2

    match_type = classify_match_type(kernel, power, glitch)
    card_color = assign_card_color(match_type)

    scores = {
        "kernel_score": round(kernel, 4),
        "power_score": round(power, 4),
        "glitch_score": round(glitch, 4),
        "total_score": round(total, 4),
    }

    radar = compute_radar_scores(user_a, user_b, scores)
    tags = generate_tags(match_type, scores)

    return {
        **scores,
        "match_type": match_type,
        "radar_passion": radar["passion"],
        "radar_stability": radar["stability"],
        "radar_communication": radar["communication"],
        "card_color": card_color,
        "tags": tags,
    }


# ═══════════════════════════════════════════════════════════════════
# Phase G: Matching v2 — Lust × Soul + Four Tracks
# ═══════════════════════════════════════════════════════════════════

# AttachmentFit matrix [style_a][style_b] → 0.0-1.0
ATTACHMENT_FIT: Dict[str, Dict[str, float]] = {
    "anxious":  {"anxious": 0.50, "avoidant": 0.70, "secure": 0.80},
    "avoidant": {"anxious": 0.70, "avoidant": 0.55, "secure": 0.75},
    "secure":   {"anxious": 0.80, "avoidant": 0.75, "secure": 0.90},
}

NEUTRAL_SIGNAL = 0.65  # default when field is None

TRACK_LABELS = {
    "friend":  "✦ 朋友型連結",
    "passion": "✦ 激情型連結",
    "partner": "✦ 伴侶型連結",
    "soul":    "✦ 靈魂型連結",
}


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp value between lo and hi."""
    return max(lo, min(hi, value))


def _rpv_to_frame(rpv_power: Optional[str], rpv_conflict: Optional[str]) -> float:
    """Map RPV responses to a frame stability score (centred at 50.0)."""
    frame = 50.0
    if rpv_power == "control":
        frame += 20
    elif rpv_power == "follow":
        frame -= 20
    if rpv_conflict == "cold_war":
        frame += 10
    elif rpv_conflict == "argue":
        frame -= 10
    return frame


def compute_lust_score(user_a: dict, user_b: dict) -> float:
    """Lust Score (X axis): physical/desire attraction (0-100).

    Weights (Eros-absent):
      venus     × 0.20
      mars      × 0.25
      house8    × 0.15  (0 when tier 2/3, no precise time)
      pluto     × 0.25
      power_fit × 0.30

    Multiplier: × 1.2 if bazi elements are in a restriction (clash) relationship.
    """
    venus = compute_sign_aspect(user_a.get("venus_sign"), user_b.get("venus_sign"))
    mars  = compute_sign_aspect(user_a.get("mars_sign"),  user_b.get("mars_sign"))
    pluto = compute_sign_aspect(user_a.get("pluto_sign"), user_b.get("pluto_sign"))

    h8_a = user_a.get("house8_sign")
    h8_b = user_b.get("house8_sign")
    house8 = compute_sign_aspect(h8_a, h8_b) if (h8_a and h8_b) else 0.0

    power_score = compute_power_score(user_a, user_b)

    score = (
        venus       * 0.20 +
        mars        * 0.25 +
        house8      * 0.15 +
        pluto       * 0.25 +
        power_score * 0.30
    )

    elem_a = user_a.get("bazi_element")
    elem_b = user_b.get("bazi_element")
    if elem_a and elem_b:
        rel = analyze_element_relation(elem_a, elem_b)
        if rel["relation"] in ("a_restricts_b", "b_restricts_a"):
            score *= 1.2

    return _clamp(score * 100)


def compute_soul_score(user_a: dict, user_b: dict) -> float:
    """Soul Score (Y axis): depth / long-term commitment (0-100).

    Weights:
      moon       × 0.25
      mercury    × 0.20
      house4     × 0.15  (0 when tier 2/3)
      saturn     × 0.20
      attachment × 0.20
      juno       × 0.20

    Multiplier: × 1.2 if bazi elements are in a generation relationship.
    """
    moon    = compute_sign_aspect(user_a.get("moon_sign"),    user_b.get("moon_sign"))
    mercury = compute_sign_aspect(user_a.get("mercury_sign"), user_b.get("mercury_sign"))
    saturn  = compute_sign_aspect(user_a.get("saturn_sign"),  user_b.get("saturn_sign"))

    h4_a = user_a.get("house4_sign")
    h4_b = user_b.get("house4_sign")
    house4 = compute_sign_aspect(h4_a, h4_b) if (h4_a and h4_b) else 0.0

    juno_a = user_a.get("juno_sign")
    juno_b = user_b.get("juno_sign")
    juno = compute_sign_aspect(juno_a, juno_b) if (juno_a and juno_b) else NEUTRAL_SIGNAL

    style_a = user_a.get("attachment_style")
    style_b = user_b.get("attachment_style")
    if style_a and style_b and style_a in ATTACHMENT_FIT:
        attachment = ATTACHMENT_FIT[style_a].get(style_b, NEUTRAL_SIGNAL)
    else:
        attachment = NEUTRAL_SIGNAL

    score = (
        moon       * 0.25 +
        mercury    * 0.20 +
        house4     * 0.15 +
        saturn     * 0.20 +
        attachment * 0.20 +
        juno       * 0.20
    )

    elem_a = user_a.get("bazi_element")
    elem_b = user_b.get("bazi_element")
    if elem_a and elem_b:
        rel = analyze_element_relation(elem_a, elem_b)
        if rel["relation"] in ("a_generates_b", "b_generates_a"):
            score *= 1.2

    return _clamp(score * 100)


def _check_chiron_triggered(user_a: dict, user_b: dict) -> bool:
    """Check if A's Mars or Pluto forms a hard aspect (square/opposition) to B's Chiron.

    Uses sign-level approximation: square = 3 signs apart, opposition = 6 apart.
    """
    chiron_b = user_b.get("chiron_sign")
    if not chiron_b or chiron_b not in SIGN_INDEX:
        return False
    mars_a  = user_a.get("mars_sign")
    pluto_a = user_a.get("pluto_sign")

    def is_hard_aspect(sign_x: Optional[str]) -> bool:
        if not sign_x or sign_x not in SIGN_INDEX:
            return False
        dist = abs(SIGN_INDEX[sign_x] - SIGN_INDEX[chiron_b]) % 12
        if dist > 6:
            dist = 12 - dist
        return dist in (3, 6)  # square or opposition

    return is_hard_aspect(mars_a) or is_hard_aspect(pluto_a)


def compute_power_v2(
    user_a: dict,
    user_b: dict,
    chiron_triggered: bool = False,
) -> dict:
    """Power D/s Frame calculation.

    RPV mapping: rpv_power control → +20, follow → -20
                 rpv_conflict cold_war → +10, argue → -10
    Chiron rule: if triggered, frame_B -= 15 (B's stability undermined).
    Returns: {rpv, frame_break, viewer_role, target_role}
    """
    frame_a = _rpv_to_frame(user_a.get("rpv_power"), user_a.get("rpv_conflict"))
    frame_b = _rpv_to_frame(user_b.get("rpv_power"), user_b.get("rpv_conflict"))

    if chiron_triggered:
        frame_b -= 15

    rpv = frame_a - frame_b

    if rpv > 15:
        viewer_role, target_role = "Dom", "Sub"
    elif rpv < -15:
        viewer_role, target_role = "Sub", "Dom"
    else:
        viewer_role, target_role = "Equal", "Equal"

    return {
        "rpv":         round(rpv, 1),
        "frame_break": chiron_triggered,
        "viewer_role": viewer_role,
        "target_role": target_role,
    }


def compute_tracks(user_a: dict, user_b: dict, power: dict) -> dict:
    """Four-track scoring: friend / passion / partner / soul (0-100 each).

    friend:  mercury × 0.40 + jupiter × 0.40 + bazi_harmony × 0.20
    passion: mars × 0.30 + venus × 0.30 + passion_extremity × 0.10 + bazi_clash × 0.30
    partner: moon × 0.35 + juno × 0.35 + bazi_generation × 0.30
    soul:    chiron × 0.40 + pluto × 0.40 + bazi_harmony × 0.20 (+0.10 if frame_break)
    """
    mercury = compute_sign_aspect(user_a.get("mercury_sign"), user_b.get("mercury_sign"))
    jupiter = compute_sign_aspect(user_a.get("jupiter_sign"), user_b.get("jupiter_sign"))
    mars    = compute_sign_aspect(user_a.get("mars_sign"),    user_b.get("mars_sign"))
    venus   = compute_sign_aspect(user_a.get("venus_sign"),   user_b.get("venus_sign"))
    pluto   = compute_sign_aspect(user_a.get("pluto_sign"),   user_b.get("pluto_sign"))
    moon    = compute_sign_aspect(user_a.get("moon_sign"),    user_b.get("moon_sign"))

    h8_a, h8_b = user_a.get("house8_sign"), user_b.get("house8_sign")
    house8 = compute_sign_aspect(h8_a, h8_b) if (h8_a and h8_b) else 0.0

    juno_a, juno_b = user_a.get("juno_sign"), user_b.get("juno_sign")
    juno = compute_sign_aspect(juno_a, juno_b) if (juno_a and juno_b) else NEUTRAL_SIGNAL

    chiron_a, chiron_b = user_a.get("chiron_sign"), user_b.get("chiron_sign")
    chiron = compute_sign_aspect(chiron_a, chiron_b) if (chiron_a and chiron_b) else NEUTRAL_SIGNAL

    elem_a = user_a.get("bazi_element")
    elem_b = user_b.get("bazi_element")
    bazi_harmony = bazi_clash = bazi_generation = False
    if elem_a and elem_b:
        rel = analyze_element_relation(elem_a, elem_b)
        bazi_harmony    = rel["relation"] == "same"
        bazi_clash      = rel["relation"] in ("a_restricts_b", "b_restricts_a")
        bazi_generation = rel["relation"] in ("a_generates_b", "b_generates_a")

    passion_extremity = max(pluto, house8)

    friend = (
        0.40 * mercury +
        0.40 * jupiter +
        0.20 * (1.0 if bazi_harmony else 0.0)
    )
    passion = (
        0.30 * mars +
        0.30 * venus +
        0.10 * passion_extremity +
        0.30 * (1.0 if bazi_clash else 0.0)
    )
    partner = (
        0.35 * moon +
        0.35 * juno +
        0.30 * (1.0 if bazi_generation else 0.0)
    )
    soul_track = (
        0.40 * chiron +
        0.40 * pluto +
        0.20 * (1.0 if bazi_harmony else 0.0)
    )
    if power["frame_break"]:
        soul_track += 0.10

    return {
        "friend":  round(_clamp(friend    * 100), 1),
        "passion": round(_clamp(passion   * 100), 1),
        "partner": round(_clamp(partner   * 100), 1),
        "soul":    round(_clamp(soul_track * 100), 1),
    }


def classify_quadrant(lust_score: float, soul_score: float, threshold: float = 60.0) -> str:
    """Classify Lust × Soul quadrant.

    lust ≥ threshold AND soul ≥ threshold → soulmate
    lust ≥ threshold AND soul <  threshold → lover
    lust <  threshold AND soul ≥ threshold → partner
    lust <  threshold AND soul <  threshold → colleague
    """
    if lust_score >= threshold and soul_score >= threshold:
        return "soulmate"
    if lust_score >= threshold:
        return "lover"
    if soul_score >= threshold:
        return "partner"
    return "colleague"


def compute_match_v2(user_a: dict, user_b: dict) -> dict:
    """Compute full Phase G v2 match score.

    Returns:
      lust_score    (0-100)
      soul_score    (0-100)
      power         {rpv, frame_break, viewer_role, target_role}
      tracks        {friend, passion, partner, soul}  (0-100 each)
      primary_track  argmax of tracks
      quadrant      soulmate | lover | partner | colleague
      labels        [primary_track display label in Traditional Chinese]
    """
    chiron_triggered = _check_chiron_triggered(user_a, user_b)
    power  = compute_power_v2(user_a, user_b, chiron_triggered)
    lust   = compute_lust_score(user_a, user_b)
    soul   = compute_soul_score(user_a, user_b)
    tracks = compute_tracks(user_a, user_b, power)

    primary_track = max(tracks, key=lambda k: tracks[k])
    quadrant      = classify_quadrant(lust, soul)
    label         = TRACK_LABELS.get(primary_track, primary_track)

    return {
        "lust_score":    round(lust, 1),
        "soul_score":    round(soul, 1),
        "power":         power,
        "tracks":        tracks,
        "primary_track": primary_track,
        "quadrant":      quadrant,
        "labels":        [label],
    }
