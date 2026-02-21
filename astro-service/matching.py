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

from bazi import analyze_element_relation, compute_bazi_season_complement, check_branch_relations
from zwds import compute_zwds_chart
from zwds_synastry import compute_zwds_synastry

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

# Harmony mode: rewards smooth, stable, comfortable aspects.
# Used for: friend track, partner track, Moon, Mercury, Jupiter, Saturn, Venus, Juno, Sun, Asc
HARMONY_ASPECTS = {
    0: 0.90,  # conjunction — high resonance
    4: 0.85,  # trine       — naturally smooth
    2: 0.75,  # sextile     — easy flow
    6: 0.60,  # opposition  — complementary but needs effort
    3: 0.40,  # square      — value friction, tiring
}

# Tension mode: rewards friction, desire, magnetic pull.
# Used for: passion track, soul track, Mars, Pluto, Chiron, House 8
TENSION_ASPECTS = {
    0: 1.00,  # conjunction — energy amplification, intense
    3: 0.90,  # square      — friction = sexual tension, control desire
    6: 0.85,  # opposition  — fatal attraction, love-hate
    4: 0.60,  # trine       — too comfortable, lacks spark
    2: 0.50,  # sextile     — friendly, little fire
}

# Minor aspects (semi-sextile=1, quincunx=5) score low in both modes
MINOR_ASPECT_SCORE = 0.10

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

def compute_sign_aspect(
    sign_a: Optional[str],
    sign_b: Optional[str],
    mode: str = "harmony",
) -> float:
    """Compute aspect score between two zodiac signs (0.0-1.0).

    mode="harmony"  — for stable/comfortable planets (Moon, Mercury, Jupiter,
                      Saturn, Venus, Juno, Sun, Asc) and friend/partner tracks.
                      Rewards trines/sextiles; penalises squares.
    mode="tension"  — for desire/power planets (Mars, Pluto, Chiron, House 8)
                      and passion/soul tracks.
                      Rewards squares/oppositions (friction = magnetism).

    Returns 0.65 (neutral) if either sign is None or invalid.
    Returns MINOR_ASPECT_SCORE (0.10) for semi-sextile (1) or quincunx (5).
    """
    if not sign_a or not sign_b:
        return 0.65
    if sign_a not in SIGN_INDEX or sign_b not in SIGN_INDEX:
        return 0.65

    distance = abs(SIGN_INDEX[sign_a] - SIGN_INDEX[sign_b]) % 12
    if distance > 6:
        distance = 12 - distance

    table = HARMONY_ASPECTS if mode == "harmony" else TENSION_ASPECTS
    return table.get(distance, MINOR_ASPECT_SCORE)


# ── Exact Degree Aspect Scoring ─────────────────────────────

def get_shortest_distance(deg_a: float, deg_b: float) -> float:
    """Shortest angular distance between two points on the 360° wheel."""
    diff = abs(deg_a - deg_b)
    return min(diff, 360.0 - diff)


def compute_exact_aspect(deg_a: float, deg_b: float, mode: str = "harmony") -> float:
    """Orb-based exact degree aspect score (0.0-1.0).

    Aspects with orbs:
      conjunction  (0°,  orb 8°): harmony=1.0  tension=1.0
      sextile     (60°,  orb 6°): harmony=0.8  tension=0.2
      square      (90°,  orb 8°): harmony=0.2  tension=0.9
      trine      (120°,  orb 8°): harmony=0.9  tension=0.2
      opposition (180°,  orb 8°): harmony=0.4  tension=0.85

    Returns 0.5 (neutral) when either degree is None.
    Returns 0.1 (void of aspect) when no major aspect is within orb.
    """
    if deg_a is None or deg_b is None:
        return 0.5
    dist = get_shortest_distance(deg_a, deg_b)
    # (center_deg, orb, harmony_score, tension_score)
    ASPECTS = [
        (0,   8,  1.00, 1.00),
        (60,  6,  0.80, 0.20),
        (90,  8,  0.20, 0.90),
        (120, 8,  0.90, 0.20),
        (180, 8,  0.40, 0.85),
    ]
    for center, orb, h_score, t_score in ASPECTS:
        if abs(dist - center) <= orb:
            return h_score if mode == "harmony" else t_score
    return 0.1  # void of aspect


def compute_karmic_triggers(user_a: dict, user_b: dict) -> float:
    """Cross-layer karmic trigger score (0.0-1.0).

    Measures how A's outer generational planets (Uranus/Neptune/Pluto)
    aspect B's inner personal planets (Moon/Venus/Mars), and vice versa.

    This replaces the misleading same-generation pluto_a vs pluto_b comparison.
    (1984-1995 cohort all have Pluto in Scorpio → conjunction = 1.0 for everyone,
    artificially inflating lust/soul scores regardless of real attraction.)

    Only aspects ≥ 0.85 (conjunction / square / opposition in tension mode) count
    as active karmic triggers. Uses exact degrees when available, sign-level fallback.

    Baseline: 0.50 (neutral — no special karmic pull).
    """
    OUTER = ["uranus", "neptune", "pluto"]
    INNER = ["moon", "venus", "mars"]

    score = 0.0
    triggers = 0

    for person_outer, person_inner in ((user_a, user_b), (user_b, user_a)):
        for outer in OUTER:
            for inner in INNER:
                deg_out = person_outer.get(f"{outer}_degree")
                deg_in  = person_inner.get(f"{inner}_degree")
                if deg_out is not None and deg_in is not None:
                    aspect = compute_exact_aspect(deg_out, deg_in, "tension")
                else:
                    aspect = compute_sign_aspect(
                        person_outer.get(f"{outer}_sign"),
                        person_inner.get(f"{inner}_sign"),
                        "tension",
                    )
                if aspect >= 0.85:
                    score += aspect
                    triggers += 1

    if triggers == 0:
        return 0.50
    return min(1.0, 0.50 + (score / (triggers * 2)))


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

    sun   = compute_sign_aspect(user_a.get("sun_sign"),        user_b.get("sun_sign"),        "harmony")
    moon  = compute_sign_aspect(user_a.get("moon_sign"),       user_b.get("moon_sign"),       "harmony")
    venus = compute_sign_aspect(user_a.get("venus_sign"),      user_b.get("venus_sign"),      "harmony")
    asc   = compute_sign_aspect(user_a.get("ascendant_sign"),  user_b.get("ascendant_sign"),  "harmony")

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
    mars       = compute_sign_aspect(user_a.get("mars_sign"),   user_b.get("mars_sign"),    "tension")
    saturn     = compute_sign_aspect(user_a.get("saturn_sign"), user_b.get("saturn_sign"), "harmony")
    mars_sat_ab = compute_sign_aspect(user_a.get("mars_sign"),  user_b.get("saturn_sign"), "tension")
    mars_sat_ba = compute_sign_aspect(user_b.get("mars_sign"),  user_a.get("saturn_sign"), "tension")

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
    venus  = compute_sign_aspect(user_a.get("venus_sign"),  user_b.get("venus_sign"),  "harmony")
    mars   = compute_sign_aspect(user_a.get("mars_sign"),   user_b.get("mars_sign"),   "tension")
    moon   = compute_sign_aspect(user_a.get("moon_sign"),   user_b.get("moon_sign"),   "harmony")
    sun    = compute_sign_aspect(user_a.get("sun_sign"),    user_b.get("sun_sign"),    "harmony")
    saturn = compute_sign_aspect(user_a.get("saturn_sign"), user_b.get("saturn_sign"), "harmony")

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

    Uses dynamic weighting: house8 only contributes when both users have
    precise birth time (Tier 1). Missing house8 is removed from denominator.

    Weights (when all present):
      venus     × 0.20
      mars      × 0.25
      house8    × 0.15  (Tier 1 only — omitted from denominator when absent)
      pluto     × 0.25
      power_fit × 0.30

    Multiplier: × 1.2 if bazi elements are in a restriction (clash) relationship.
    """
    score = 0.0
    total_weight = 0.0

    venus = compute_sign_aspect(user_a.get("venus_sign"), user_b.get("venus_sign"), "harmony")
    score += venus * 0.20
    total_weight += 0.20

    mars = compute_sign_aspect(user_a.get("mars_sign"), user_b.get("mars_sign"), "tension")
    score += mars * 0.25
    total_weight += 0.25

    # Karmic triggers: outer planets (Uranus/Neptune/Pluto) of A vs inner (Moon/Venus/Mars) of B
    # Replaces same-generation pluto_a vs pluto_b which is meaningless for same-cohort pairs.
    karmic = compute_karmic_triggers(user_a, user_b)
    score += karmic * 0.25
    total_weight += 0.25

    # House 8 (0.15) — Tier 1 only
    h8_a = user_a.get("house8_sign")
    h8_b = user_b.get("house8_sign")
    if h8_a and h8_b:
        score += compute_sign_aspect(h8_a, h8_b, "tension") * 0.15
        total_weight += 0.15

    power_score = compute_power_score(user_a, user_b)
    score += power_score * 0.30
    total_weight += 0.30

    base_score = score / total_weight if total_weight > 0 else NEUTRAL_SIGNAL

    elem_a = user_a.get("bazi_element")
    elem_b = user_b.get("bazi_element")
    if elem_a and elem_b:
        rel = analyze_element_relation(elem_a, elem_b)
        if rel["relation"] in ("a_restricts_b", "b_restricts_a"):
            base_score *= 1.2

    return _clamp(base_score * 100)


def compute_soul_score(user_a: dict, user_b: dict) -> float:
    """Soul Score (Y axis): depth / long-term commitment (0-100).

    Uses dynamic weighting: optional fields (House 4, Juno, attachment_style)
    only contribute their weight when present. Missing fields are removed from
    the denominator so Tier 2/3 scores remain proportionally accurate.

    Weights (when all present):
      moon       × 0.25  — always present
      mercury    × 0.20  — always present
      saturn     × 0.20  — always present
      house4     × 0.15  — Tier 1 only
      juno       × 0.20  — when ephemeris available
      attachment × 0.20  — when questionnaire filled

    Multiplier: × 1.2 if bazi elements are in a generation relationship.
    """
    score = 0.0
    total_weight = 0.0

    # 1. Moon (0.25) — always present
    moon = compute_sign_aspect(user_a.get("moon_sign"), user_b.get("moon_sign"), "harmony")
    score += moon * 0.25
    total_weight += 0.25

    # 2. Mercury (0.20) — always present
    mercury = compute_sign_aspect(user_a.get("mercury_sign"), user_b.get("mercury_sign"), "harmony")
    score += mercury * 0.20
    total_weight += 0.20

    # 3. Saturn (0.20) — always present
    saturn = compute_sign_aspect(user_a.get("saturn_sign"), user_b.get("saturn_sign"), "harmony")
    score += saturn * 0.20
    total_weight += 0.20

    # 4. House 4 (0.15) — Tier 1 only
    h4_a = user_a.get("house4_sign")
    h4_b = user_b.get("house4_sign")
    if h4_a and h4_b:
        score += compute_sign_aspect(h4_a, h4_b, "harmony") * 0.15
        total_weight += 0.15

    # 5. Juno (0.20) — when ephemeris available
    juno_a = user_a.get("juno_sign")
    juno_b = user_b.get("juno_sign")
    if juno_a and juno_b:
        score += compute_sign_aspect(juno_a, juno_b, "harmony") * 0.20
        total_weight += 0.20

    # 6. Attachment style (0.20) — when questionnaire filled
    style_a = user_a.get("attachment_style")
    style_b = user_b.get("attachment_style")
    if style_a and style_b and style_a in ATTACHMENT_FIT and style_b in ATTACHMENT_FIT[style_a]:
        attachment = ATTACHMENT_FIT[style_a][style_b]
        score += attachment * 0.20
        total_weight += 0.20

    base_score = score / total_weight if total_weight > 0 else NEUTRAL_SIGNAL

    # Multiplier: 八字相生加成
    elem_a = user_a.get("bazi_element")
    elem_b = user_b.get("bazi_element")
    if elem_a and elem_b:
        rel = analyze_element_relation(elem_a, elem_b)
        if rel["relation"] in ("a_generates_b", "b_generates_a"):
            base_score *= 1.2

    return _clamp(base_score * 100)


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
    chiron_triggered_ab: bool = False,
    chiron_triggered_ba: bool = False,
    bazi_relation: str = "none",
    zwds_rpv_modifier: int = 0,
) -> dict:
    """Power D/s Frame calculation (v2.1).

    RPV mapping: rpv_power control → +20, follow → -20
                 rpv_conflict cold_war → +10, argue → -10
    Chiron rule (bidirectional):
      A's Mars/Pluto hard-aspects B's Chiron → frame_B -= 15
      B's Mars/Pluto hard-aspects A's Chiron → frame_A -= 15
    BaZi restriction dynamics:
      a_restricts_b → frame_A += 15, frame_B -= 15 (A gains dominance)
      b_restricts_a → frame_A -= 15, frame_B += 15 (B gains dominance)
    Returns: {rpv, frame_break, viewer_role, target_role}
    """
    frame_a = _rpv_to_frame(user_a.get("rpv_power"), user_a.get("rpv_conflict"))
    frame_b = _rpv_to_frame(user_b.get("rpv_power"), user_b.get("rpv_conflict"))
    frame_break = False

    # Chiron trauma trigger (bidirectional)
    if chiron_triggered_ab:
        frame_b -= 15
        frame_break = True
    if chiron_triggered_ba:
        frame_a -= 15
        frame_break = True

    # BaZi restriction dynamics: the restrictor gains natural dominance
    if bazi_relation == "a_restricts_b":
        frame_a += 15
        frame_b -= 15
    elif bazi_relation == "b_restricts_a":
        frame_a -= 15
        frame_b += 15

    # ZWDS RPV modifier
    frame_a += zwds_rpv_modifier

    rpv = frame_a - frame_b

    if rpv > 15:
        viewer_role, target_role = "Dom", "Sub"
    elif rpv < -15:
        viewer_role, target_role = "Sub", "Dom"
    else:
        viewer_role, target_role = "Equal", "Equal"

    return {
        "rpv":         round(rpv, 1),
        "frame_break": frame_break,
        "viewer_role": viewer_role,
        "target_role": target_role,
    }


def compute_tracks(
    user_a: dict,
    user_b: dict,
    power: dict,
    useful_god_complement: float = 0.0,
    zwds_mods: dict = None,
) -> dict:
    """Four-track scoring: friend / passion / partner / soul (0-100 each).

    friend:  mercury × 0.40 + jupiter × 0.40 + bazi_same × 0.20
    passion: mars × 0.30 + venus × 0.30 + passion_extremity × 0.10 + bazi_clash × 0.30
    partner: moon × 0.35 + juno × 0.35 + bazi_generation × 0.30
    soul:    chiron × 0.40 + pluto × 0.40 + useful_god_complement × 0.20
             (+0.10 bonus if frame_break)
    When juno absent:  moon×0.55 + bazi_generation×0.45
    When chiron absent: pluto×0.60 + useful_god×0.40

    Emotional capacity penalty (applied to partner track before zwds_mods):
      Both users < 40: partner × 0.7  (mutual emotional drain)
      Either user < 30: partner × 0.85 (one user is extremely unstable)
    """
    # Emotional capacity penalty for partner track
    capacity_a = user_a.get("emotional_capacity", 50)
    capacity_b = user_b.get("emotional_capacity", 50)

    # harmony planets: friend / partner tracks
    mercury = compute_sign_aspect(user_a.get("mercury_sign"), user_b.get("mercury_sign"), "harmony")
    jupiter = compute_sign_aspect(user_a.get("jupiter_sign"), user_b.get("jupiter_sign"), "harmony")
    moon    = compute_sign_aspect(user_a.get("moon_sign"),    user_b.get("moon_sign"),    "harmony")
    juno_a, juno_b = user_a.get("juno_sign"), user_b.get("juno_sign")
    juno_present = bool(juno_a and juno_b)
    juno = compute_sign_aspect(juno_a, juno_b, "harmony") if juno_present else 0.0

    # tension planets: passion / soul tracks
    mars  = compute_sign_aspect(user_a.get("mars_sign"),   user_b.get("mars_sign"),   "tension")
    venus = compute_sign_aspect(user_a.get("venus_sign"),  user_b.get("venus_sign"),  "tension")  # passion context
    # Cross-layer karmic triggers replace same-generation pluto_a vs pluto_b
    karmic = compute_karmic_triggers(user_a, user_b)
    h8_a, h8_b = user_a.get("house8_sign"), user_b.get("house8_sign")
    house8 = compute_sign_aspect(h8_a, h8_b, "tension") if (h8_a and h8_b) else 0.0
    chiron_a, chiron_b = user_a.get("chiron_sign"), user_b.get("chiron_sign")
    chiron_present = bool(chiron_a and chiron_b)
    chiron = compute_sign_aspect(chiron_a, chiron_b, "tension") if chiron_present else 0.0

    elem_a = user_a.get("bazi_element")
    elem_b = user_b.get("bazi_element")
    bazi_harmony = bazi_clash = bazi_generation = False
    if elem_a and elem_b:
        rel = analyze_element_relation(elem_a, elem_b)
        bazi_harmony    = rel["relation"] == "same"
        bazi_clash      = rel["relation"] in ("a_restricts_b", "b_restricts_a")
        bazi_generation = rel["relation"] in ("a_generates_b", "b_generates_a")

    passion_extremity = max(karmic, house8)

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
    if juno_present:
        partner = moon * 0.35 + juno * 0.35 + (1.0 if bazi_generation else 0.0) * 0.30
    else:
        # Redistribute juno's 0.35 weight: moon gets 0.55, bazi gets 0.45
        partner = moon * 0.55 + (1.0 if bazi_generation else 0.0) * 0.45

    if chiron_present:
        soul_track = chiron * 0.40 + karmic * 0.40 + useful_god_complement * 0.20
    else:
        # Redistribute chiron's 0.40 weight: karmic gets 0.60, useful_god gets 0.40
        soul_track = karmic * 0.60 + useful_god_complement * 0.40

    if power["frame_break"]:
        soul_track += 0.10

    # Emotional capacity guard: low capacity → partner track penalty
    if capacity_a < 40 and capacity_b < 40:
        partner *= 0.7  # Both emotional sponges → mutual drain
    elif capacity_a < 30 or capacity_b < 30:
        partner *= 0.85  # One person is extremely unstable

    # Note: track scores here are in [0.0, ~1.3] range (pre-×100 scale).
    # _clamp(lo=0.0, hi=100.0) will not trigger here; the outer _clamp in
    # the return statement handles the final 0-100 clamping.
    if zwds_mods:
        friend     = _clamp(friend     * (0.70 * zwds_mods.get("friend",  1.0) + 0.30))
        passion    = _clamp(passion    * (0.70 * zwds_mods.get("passion", 1.0) + 0.30))
        partner    = _clamp(partner    * (0.70 * zwds_mods.get("partner", 1.0) + 0.30))
        soul_track = _clamp(soul_track * (0.70 * zwds_mods.get("soul",    1.0) + 0.30))

    return {
        "friend":  round(_clamp(friend    * 100), 1),
        "passion": round(_clamp(passion   * 100), 1),
        "partner": round(_clamp(partner   * 100), 1),
        "soul":    round(_clamp(soul_track * 100), 1),
    }


def apply_bazi_branch_modifiers(tracks: dict, relation: str) -> dict:
    """Apply 地支刑沖破害 modifiers to four-track scores (in-place + return).

    Based on Day Branch (日支) = Spouse Palace interaction:

    clash (沖)      — fatal attraction, violently unstable cohabitation
                     passion ×1.25 | partner ×0.70
    punishment (刑) — trauma bonding / emotional torment
                     soul ×1.15 | partner ×0.60
                     (also forces spiciness to HIGH_VOLTAGE in compute_match_v2)
    harm (害)       — passive-aggressive trust erosion
                     friend ×0.60 | partner ×0.50
    neutral         — no modifier
    """
    if relation == "clash":
        tracks["passion"] = min(100.0, tracks["passion"] * 1.25)
        tracks["partner"] = max(0.0, tracks["partner"] * 0.70)
    elif relation == "punishment":
        tracks["soul"]    = min(100.0, tracks["soul"] * 1.15)
        tracks["partner"] = max(0.0, tracks["partner"] * 0.60)
    elif relation == "harm":
        tracks["friend"]  = max(0.0, tracks["friend"] * 0.60)
        tracks["partner"] = max(0.0, tracks["partner"] * 0.50)
    return tracks


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


def _is_zwds_eligible(user: dict) -> bool:
    """Return True if user has Tier 1 data with birth_time for ZWDS computation."""
    return user.get("data_tier") == 1 and bool(user.get("birth_time"))


def compute_match_v2(user_a: dict, user_b: dict) -> dict:
    """Compute full Phase G v2.1 match score.

    New in v2.1:
      - BaZi relation computed once and shared across functions
      - BaZi restriction directionality wired into RPV power frame
      - Chiron trigger checked bidirectionally (A→B and B→A)
      - Soul track uses seasonal useful-god complement (調候互補)
        instead of simple bazi_harmony (same element check)
      - Output includes bazi_relation + useful_god_complement

    Returns:
      lust_score             (0-100)
      soul_score             (0-100)
      power                  {rpv, frame_break, viewer_role, target_role}
      tracks                 {friend, passion, partner, soul}  (0-100 each)
      primary_track          argmax of tracks
      quadrant               soulmate | lover | partner | colleague
      labels                 [primary_track display label in Traditional Chinese]
      bazi_relation          a_generates_b | b_generates_a | a_restricts_b |
                             b_restricts_a | same | none
      useful_god_complement  seasonal complement score (0.0-1.0)
    """
    # BaZi relation (computed once, shared)
    elem_a = user_a.get("bazi_element")
    elem_b = user_b.get("bazi_element")
    bazi_relation = "none"
    if elem_a and elem_b:
        rel = analyze_element_relation(elem_a, elem_b)
        bazi_relation = rel["relation"]

    # Seasonal useful-god complement (uses 月支 month branch for precision)
    branch_a = user_a.get("bazi_month_branch")
    branch_b = user_b.get("bazi_month_branch")
    useful_god_complement = 0.0
    if branch_a and branch_b:
        useful_god_complement = compute_bazi_season_complement(branch_a, branch_b)
    elif user_a.get("birth_month") is not None and user_b.get("birth_month") is not None:
        # Legacy fallback: approximate from Gregorian month
        # Map Gregorian month to approximate branch string
        # Coarse approximation: assigns the dominant branch for each Gregorian month.
        # Births in the first ~4-7 days of Feb/May/Aug/Nov may straddle a solar term
        # boundary and belong to the previous branch. Use bazi_month_branch for precision.
        _MONTH_TO_BRANCH = {
            1: "丑", 2: "寅", 3: "卯", 4: "辰", 5: "巳", 6: "午",
            7: "未", 8: "申", 9: "酉", 10: "戌", 11: "亥", 12: "子"
        }
        fb_a = _MONTH_TO_BRANCH.get(int(user_a["birth_month"]))
        fb_b = _MONTH_TO_BRANCH.get(int(user_b["birth_month"]))
        if fb_a and fb_b:
            useful_god_complement = compute_bazi_season_complement(fb_a, fb_b)

    # Chiron trigger (bidirectional)
    chiron_ab = _check_chiron_triggered(user_a, user_b)
    chiron_ba = _check_chiron_triggered(user_b, user_a)

    # ── ZWDS (紫微斗數) — Tier 1 only ──────────────────────────────────────
    zwds_result = None
    if _is_zwds_eligible(user_a) and _is_zwds_eligible(user_b):
        try:
            chart_a = compute_zwds_chart(
                user_a["birth_year"], user_a["birth_month"], user_a["birth_day"],
                user_a["birth_time"], user_a.get("gender", "M")
            )
            chart_b = compute_zwds_chart(
                user_b["birth_year"], user_b["birth_month"], user_b["birth_day"],
                user_b["birth_time"], user_b.get("gender", "F")
            )
            if chart_a and chart_b:
                zwds_result = compute_zwds_synastry(
                    chart_a, user_a["birth_year"],
                    chart_b, user_b["birth_year"]
                )
        except Exception:
            zwds_result = None  # never block matching for ZWDS failure

    zwds_mods = zwds_result["track_mods"] if zwds_result else None
    zwds_rpv  = zwds_result["rpv_modifier"] if zwds_result else 0

    power  = compute_power_v2(user_a, user_b, chiron_ab, chiron_ba, bazi_relation,
                               zwds_rpv_modifier=zwds_rpv)
    lust   = compute_lust_score(user_a, user_b)
    soul   = compute_soul_score(user_a, user_b)
    tracks = compute_tracks(user_a, user_b, power, useful_god_complement,
                            zwds_mods=zwds_mods)

    # ── BaZi day-branch 刑沖破害 (Spouse Palace dynamics) ─────────────────
    day_branch_a = user_a.get("bazi_day_branch")
    day_branch_b = user_b.get("bazi_day_branch")
    day_branch_relation = "neutral"
    if day_branch_a and day_branch_b:
        day_branch_relation = check_branch_relations(day_branch_a, day_branch_b)
        apply_bazi_branch_modifiers(tracks, day_branch_relation)

    primary_track = max(tracks, key=lambda k: tracks[k])
    quadrant      = classify_quadrant(lust, soul)
    label         = TRACK_LABELS.get(primary_track, primary_track)

    # Spiciness level: ZWDS base, upgraded to HIGH_VOLTAGE when punishment (刑) detected
    _SPICINESS_ORDER = ["STABLE", "MEDIUM", "HIGH_VOLTAGE", "SOULMATE"]
    spiciness = zwds_result["spiciness_level"] if zwds_result else "STABLE"
    if day_branch_relation == "punishment":
        cur_idx    = _SPICINESS_ORDER.index(spiciness) if spiciness in _SPICINESS_ORDER else 0
        target_idx = _SPICINESS_ORDER.index("HIGH_VOLTAGE")
        if cur_idx < target_idx:
            spiciness = "HIGH_VOLTAGE"

    return {
        "lust_score":              round(lust, 1),
        "soul_score":              round(soul, 1),
        "power":                   power,
        "tracks":                  tracks,
        "primary_track":           primary_track,
        "quadrant":                quadrant,
        "labels":                  [label],
        "bazi_relation":           bazi_relation,
        "bazi_day_branch_relation": day_branch_relation,
        "useful_god_complement":   round(useful_god_complement, 2),
        "zwds":                    zwds_result,
        "spiciness_level":         spiciness,
        "defense_mechanisms": {
            "viewer": zwds_result["defense_a"] if zwds_result else [],
            "target": zwds_result["defense_b"] if zwds_result else [],
        },
        "layered_analysis":        zwds_result.get("layered_analysis", {}) if zwds_result else {},
    }
