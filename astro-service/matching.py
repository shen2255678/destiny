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

from bazi import analyze_element_relation, compute_bazi_season_complement, check_branch_relations, evaluate_day_master_strength
from zwds import compute_zwds_chart
from zwds_synastry import compute_zwds_synastry
from shadow_engine import (
    compute_shadow_and_wound,
    compute_dynamic_attachment,
    compute_attachment_dynamics,
    compute_elemental_fulfillment,
)
from psychology import MODERN_RULERSHIPS

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

# ── WEIGHTS — Centralized weight configuration ─────────────────────────────
# Edit these values to tune scoring without touching function bodies.
# All keys are wired: lust, soul, kernel, tracks, power, glitch, match.
WEIGHTS = {
    # ── compute_lust_score ────────── ✅ wired ───────────────────────────────
    "lust_cross_mars_venus":   0.30,   # mars_a × venus_b  (cross-person, tension) ← primary
    "lust_cross_venus_mars":   0.30,   # mars_b × venus_a  (cross-person, tension) ← primary
    # NOTE: lust_cross_mars_venus and lust_cross_venus_mars MUST stay equal to preserve score symmetry
    # (swapping user_a and user_b must produce the same score).
    "lust_same_venus":         0.15,   # venus_a × venus_b (same-planet, harmony)
    "lust_same_mars":          0.15,   # mars_a × mars_b   (same-planet, harmony)
    "lust_house8_ab":          0.10,   # h8_a × mars_b     (8th house taboo pull)
    "lust_house8_ba":          0.10,   # h8_b × mars_a
    # ASC cross-aspects (first-impression physical pull, Tier 1 only — requires exact degree)
    "lust_mars_asc_ab":        0.10,   # mars_a × asc_b  (tension — A's drive ignites B's persona)
    "lust_mars_asc_ba":        0.10,   # mars_b × asc_a  (tension — B's drive ignites A's persona)
    "lust_venus_asc_ab":       0.10,   # venus_a × asc_b (harmony — A's allure fits B's appearance)
    "lust_venus_asc_ba":       0.10,   # venus_b × asc_a (harmony — B's allure fits A's appearance)
    "lust_karmic":             0.25,   # outer-vs-inner karmic triggers
    "lust_power":              0.30,   # RPV power dynamic
    "lust_power_plateau":      0.75,   # L-10: power_val above this gets diminishing returns
    "lust_power_diminish_factor": 0.60, # L-10: slope beyond plateau (0.90 → effective 0.84)
    "lust_attachment_aa_mult": 1.15,   # L-11: anxious×avoidant lust spike multiplier
    "lust_bazi_restrict_mult": 1.25,   # DEPRECATED: replaced by diminishing-returns additive formula in Sprint 2

    # ── compute_soul_score ────────── ✅ wired ────────────────────────────────
    "soul_moon":              0.25,   # always present
    "soul_mercury":           0.20,   # always present
    "soul_saturn":            0.20,   # always present
    "soul_house4":            0.15,   # Tier 1 only
    "soul_juno":              0.20,   # when ephemeris available
    "soul_attachment":        0.20,   # when questionnaire filled
    "soul_sun_moon":          0.25,   # Sun-Moon cross-aspect (A's Sun × B's Moon, bidirectional avg)
    "soul_generation_mult":   1.20,   # DEPRECATED: replaced by diminishing-returns additive formula in Sprint 2

    # ── compute_kernel_score ─── ✅ wired ────────────────────────────────────
    "kernel_t1_sun":           0.20,
    "kernel_t1_moon":          0.25,
    "kernel_t1_venus":         0.25,
    "kernel_t1_asc":           0.15,
    "kernel_t1_bazi":          0.15,
    "kernel_t2_sun":           0.25,
    "kernel_t2_moon":          0.20,
    "kernel_t2_venus":         0.25,
    "kernel_t2_bazi":          0.30,
    "kernel_t3_sun":           0.30,
    "kernel_t3_venus":         0.30,
    "kernel_t3_bazi":          0.40,

    # ── compute_tracks ─── ✅ wired ──────────────────────────────────────────
    "track_friend_mercury":          0.40,
    "track_friend_jupiter":          0.40,
    "track_friend_bazi":             0.20,
    "track_passion_mars":            0.30,
    "track_passion_venus":           0.30,
    "track_passion_extreme":         0.10,   # additive bonus from max(karmic, house8) signals
    "track_passion_bazi":            0.30,
    "track_partner_moon":            0.35,
    "track_partner_juno":            0.35,
    "track_partner_bazi":            0.30,
    "track_partner_nojuno_moon":     0.55,
    "track_partner_nojuno_bazi":     0.45,
    "track_partner_saturn_cross":    0.10,   # A's Saturn × B's Moon cross-aspect bonus (bidirectional avg)
    # track_soul_chiron / track_soul_karmic / track_soul_useful_god removed (L-12 + L-2 fix):
    # Chiron is now handled exclusively by shadow_engine orb-based checks; sign-level Chiron
    # created false conjunction boosts for same-generation age-peers.
    "track_soul_nochiron_karmic":    0.60,
    "track_soul_nochiron_useful_god": 0.40,

    # ── compute_power_score (RPV) ────────────────────────────────────────────
    "power_conflict":          0.35,
    "power_power":             0.40,
    "power_energy":            0.25,

    # ── compute_glitch_score ─── ✅ wired ────────────────────────────────────
    "glitch_mars":             0.25,
    "glitch_saturn":           0.25,
    "glitch_mars_sat_ab":      0.25,
    "glitch_mars_sat_ba":      0.25,

    # ── compute_match_score (v1 top-level) ───────────────────────────────────
    "match_kernel":            0.50,
    "match_power":             0.30,
    "match_glitch":            0.20,
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

# Exact-degree aspect rules: (center_deg, orb, harmony_max, tension_max)
# Used by compute_exact_aspect for linear orb decay scoring.
ASPECT_RULES = [
    (0,   8,  1.0, 1.0),   # conjunction:  full fusion
    (60,  6,  0.8, 0.3),   # sextile:      easy flow
    (90,  8,  0.2, 0.9),   # square:       friction / tension
    (120, 8,  1.0, 0.2),   # trine:        natural harmony
    (180, 8,  0.4, 1.0),   # opposition:   fatal attraction
]

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


def _resolve_aspect(
    deg_x: Optional[float], sign_x: Optional[str],
    deg_y: Optional[float], sign_y: Optional[str],
    mode: str,
) -> float:
    """Use exact degrees if both available; fall back to sign-level aspect.

    When exact degrees yield void-of-aspect (0.5), preserve sign-level
    background at 80% weight so Tier 1 users are never penalised vs Tier 3.

    Used by compute_lust_score and any future function that accepts both
    exact planet_degrees and sign-level fallback inputs.
    """
    if deg_x is not None and deg_y is not None:
        exact = compute_exact_aspect(deg_x, deg_y, mode)
        if exact == 0.5:  # void of aspect — preserve sign background at 80%
            return round(compute_sign_aspect(sign_x, sign_y, mode) * 0.8, 2)
        return exact
    return compute_sign_aspect(sign_x, sign_y, mode)


# ── Exact Degree Aspect Scoring ─────────────────────────────

def get_shortest_distance(deg_a: float, deg_b: float) -> float:
    """Shortest angular distance between two points on the 360° wheel."""
    diff = abs(deg_a - deg_b)
    return min(diff, 360.0 - diff)


def compute_exact_aspect(deg_a: float, deg_b: float, mode: str = "harmony") -> float:
    """Orb-based exact degree aspect score with linear decay (0.0-1.0).

    Score decays linearly from the aspect center toward the orb boundary:
      strength_ratio = 1.0 - (diff / orb)
      final_score    = 0.2 + (max_score - 0.2) * strength_ratio

    A 0° conjunction scores 1.0; a 7° conjunction scores ~0.30 (harmony mode).

    Aspect table (center_deg, orb, harmony_max, tension_max):
      conjunction  (0°,   orb 8°): harmony=1.0  tension=1.0
      sextile     (60°,  orb 6°): harmony=0.8  tension=0.3
      square      (90°,  orb 8°): harmony=0.2  tension=0.9
      trine      (120°,  orb 8°): harmony=1.0  tension=0.2
      opposition (180°,  orb 8°): harmony=0.4  tension=1.0

    Returns 0.5 (neutral) when either degree is None.
    Returns 0.1 (void of aspect) when no major aspect is within orb.
    """
    if deg_a is None or deg_b is None:
        return 0.5
    dist = get_shortest_distance(deg_a, deg_b)
    for center, orb, harm_max, tens_max in ASPECT_RULES:
        diff = abs(dist - center)
        if diff <= orb:
            max_score = harm_max if mode == "harmony" else tens_max
            strength_ratio = 1.0 - (diff / orb)
            return round(0.2 + (max_score - 0.2) * strength_ratio, 2)
    return 0.5  # void of aspect — neutral, not a penalty


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
                if aspect >= 0.70:   # L-8: lowered from 0.85 — 0.85 required ~1.5° orb, too strict; 0.70 catches ~4° aspects
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

    sun   = _resolve_aspect(user_a.get("sun_degree"),        user_a.get("sun_sign"),
                            user_b.get("sun_degree"),        user_b.get("sun_sign"),        "harmony")
    moon  = _resolve_aspect(user_a.get("moon_degree"),       user_a.get("moon_sign"),
                            user_b.get("moon_degree"),       user_b.get("moon_sign"),       "harmony")
    venus = _resolve_aspect(user_a.get("venus_degree"),      user_a.get("venus_sign"),
                            user_b.get("venus_degree"),      user_b.get("venus_sign"),      "harmony")
    asc   = _resolve_aspect(user_a.get("ascendant_degree"),  user_a.get("ascendant_sign"),
                            user_b.get("ascendant_degree"),  user_b.get("ascendant_sign"),  "harmony")

    # BaZi harmony
    bazi = 0.65  # neutral default
    elem_a = user_a.get("bazi_element")
    elem_b = user_b.get("bazi_element")
    if elem_a and elem_b:
        relation = analyze_element_relation(elem_a, elem_b)
        bazi = relation["harmony_score"]

    if effective_tier == 1:
        return (sun   * WEIGHTS["kernel_t1_sun"]   +
                moon  * WEIGHTS["kernel_t1_moon"]  +
                venus * WEIGHTS["kernel_t1_venus"] +
                asc   * WEIGHTS["kernel_t1_asc"]   +
                bazi  * WEIGHTS["kernel_t1_bazi"])
    elif effective_tier == 2:
        return (sun   * WEIGHTS["kernel_t2_sun"]   +
                moon  * WEIGHTS["kernel_t2_moon"]  +
                venus * WEIGHTS["kernel_t2_venus"] +
                bazi  * WEIGHTS["kernel_t2_bazi"])
    else:
        return (sun   * WEIGHTS["kernel_t3_sun"]   +
                venus * WEIGHTS["kernel_t3_venus"] +
                bazi  * WEIGHTS["kernel_t3_bazi"])


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

    return (conflict * WEIGHTS["power_conflict"] +
            power    * WEIGHTS["power_power"] +
            energy   * WEIGHTS["power_energy"])


# ── Glitch Tolerance (20%) ───────────────────────────────────

def compute_glitch_score(user_a: dict, user_b: dict) -> float:
    """Compute Glitch Tolerance (0.0-1.0).

    Mars/Saturn cross-aspects:
      - mars_a vs mars_b: conflict style
      - saturn_a vs saturn_b: boundaries
      - mars_a vs saturn_b and vice versa: friction triggers
    Higher score = higher tolerance (less destructive friction).
    """
    mars        = _resolve_aspect(user_a.get("mars_degree"),   user_a.get("mars_sign"),
                                  user_b.get("mars_degree"),   user_b.get("mars_sign"),    "tension")
    saturn      = _resolve_aspect(user_a.get("saturn_degree"), user_a.get("saturn_sign"),
                                  user_b.get("saturn_degree"), user_b.get("saturn_sign"),  "harmony")
    mars_sat_ab = _resolve_aspect(user_a.get("mars_degree"),   user_a.get("mars_sign"),
                                  user_b.get("saturn_degree"), user_b.get("saturn_sign"),  "tension")
    mars_sat_ba = _resolve_aspect(user_b.get("mars_degree"),   user_b.get("mars_sign"),
                                  user_a.get("saturn_degree"), user_a.get("saturn_sign"),  "tension")

    return (mars        * WEIGHTS["glitch_mars"] +
            saturn      * WEIGHTS["glitch_saturn"] +
            mars_sat_ab * WEIGHTS["glitch_mars_sat_ab"] +
            mars_sat_ba * WEIGHTS["glitch_mars_sat_ba"])


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
    total = (kernel * WEIGHTS["match_kernel"] +
             power  * WEIGHTS["match_power"] +
             glitch * WEIGHTS["match_glitch"])

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

    Primary signal — cross-person Mars × Venus aspects (exact degrees → sign fallback):
      mars_a × venus_b  tension × WEIGHTS["lust_cross_mars_venus"]  (0.30)
      mars_b × venus_a  tension × WEIGHTS["lust_cross_venus_mars"]  (0.30)

    Secondary — same-planet harmony:
      venus_a × venus_b harmony × WEIGHTS["lust_same_venus"]  (0.15)
      mars_a × mars_b   harmony × WEIGHTS["lust_same_mars"]   (0.15)

    Taboo pull — 8th house × Mars (exact degrees only; omitted when absent):
      h8_a × mars_b  tension × WEIGHTS["lust_house8_ab"]  (0.10)
      h8_b × mars_a  tension × WEIGHTS["lust_house8_ba"]  (0.10)

    Karmic: outer-vs-inner triggers × WEIGHTS["lust_karmic"]  (0.25)
    Power:  RPV dynamic (soft-capped) × WEIGHTS["lust_power"]  (0.30)
            Diminishing returns above lust_power_plateau (0.75): slope = 0.60.

    Additive boosts (applied after base_score, diminishing-returns):
      + (1 - base) × 0.25 when BaZi elements clash (Sprint 2; never exceeds 1.0).
      × WEIGHTS["lust_attachment_aa_mult"] (1.15) when anxious × avoidant pair (L-11).
    Terms 1-4 fall back to sign-level aspect when exact degrees unavailable.
    House 8 signals (terms 5-6) require exact degrees and are omitted when absent.
    """
    score = 0.0
    total_weight = 0.0

    venus_a_deg = user_a.get("venus_degree")
    venus_b_deg = user_b.get("venus_degree")
    mars_a_deg  = user_a.get("mars_degree")
    mars_b_deg  = user_b.get("mars_degree")
    h8_a_deg    = user_a.get("house8_degree")
    h8_b_deg    = user_b.get("house8_degree")

    # 1. Cross-person: mars_a × venus_b (A pursues B)
    w = WEIGHTS["lust_cross_mars_venus"]
    score += _resolve_aspect(mars_a_deg, user_a.get("mars_sign"),
                     venus_b_deg, user_b.get("venus_sign"), "tension") * w
    total_weight += w

    # 2. Cross-person: mars_b × venus_a (B pursues A)
    w = WEIGHTS["lust_cross_venus_mars"]
    score += _resolve_aspect(mars_b_deg, user_b.get("mars_sign"),
                     venus_a_deg, user_a.get("venus_sign"), "tension") * w
    total_weight += w

    # 3. Same-planet: venus_a × venus_b (aesthetic sync)
    w = WEIGHTS["lust_same_venus"]
    score += _resolve_aspect(venus_a_deg, user_a.get("venus_sign"),
                     venus_b_deg, user_b.get("venus_sign"), "harmony") * w
    total_weight += w

    # 4. Same-planet: mars_a × mars_b (energy rhythm sync)
    w = WEIGHTS["lust_same_mars"]
    score += _resolve_aspect(mars_a_deg, user_a.get("mars_sign"),
                     mars_b_deg, user_b.get("mars_sign"), "harmony") * w
    total_weight += w

    # 5. House 8 × Mars cross-aspects (exact degrees only; omitted from denominator if absent)
    if h8_a_deg is not None and mars_b_deg is not None:
        w = WEIGHTS["lust_house8_ab"]
        score += compute_exact_aspect(h8_a_deg, mars_b_deg, "tension") * w
        total_weight += w
    if h8_b_deg is not None and mars_a_deg is not None:
        w = WEIGHTS["lust_house8_ba"]
        score += compute_exact_aspect(h8_b_deg, mars_a_deg, "tension") * w
        total_weight += w

    # 5b. Ascendant cross-aspects (first-impression physical pull, Tier 1 only)
    # Only added when exact degrees available — avoids neutral-score contamination for Tier 2/3
    asc_a_deg = user_a.get("ascendant_degree")
    asc_b_deg = user_b.get("ascendant_degree")
    if mars_a_deg is not None and asc_b_deg is not None:
        w = WEIGHTS["lust_mars_asc_ab"]
        score += compute_exact_aspect(mars_a_deg, asc_b_deg, "tension") * w
        total_weight += w
    if mars_b_deg is not None and asc_a_deg is not None:
        w = WEIGHTS["lust_mars_asc_ba"]
        score += compute_exact_aspect(mars_b_deg, asc_a_deg, "tension") * w
        total_weight += w
    if venus_a_deg is not None and asc_b_deg is not None:
        w = WEIGHTS["lust_venus_asc_ab"]
        score += compute_exact_aspect(venus_a_deg, asc_b_deg, "harmony") * w
        total_weight += w
    if venus_b_deg is not None and asc_a_deg is not None:
        w = WEIGHTS["lust_venus_asc_ba"]
        score += compute_exact_aspect(venus_b_deg, asc_a_deg, "harmony") * w
        total_weight += w

    # 6. Karmic triggers (outer vs inner planets)
    karmic = compute_karmic_triggers(user_a, user_b)
    w = WEIGHTS["lust_karmic"]
    score += karmic * w
    total_weight += w

    # 7. RPV power dynamic (with L-10 diminishing returns above plateau)
    # Extreme complementary power (D/s ideal) gives a strong pull, but beyond a
    # threshold the additional gain flattens — preventing RPV from dominating lust.
    power_val = compute_power_score(user_a, user_b)
    plateau = WEIGHTS["lust_power_plateau"]
    dfactor = WEIGHTS["lust_power_diminish_factor"]
    effective_power = (power_val if power_val <= plateau
                       else plateau + (power_val - plateau) * dfactor)
    w = WEIGHTS["lust_power"]
    score += effective_power * w
    total_weight += w

    base_score = score / total_weight if total_weight > 0 else NEUTRAL_SIGNAL

    # BaZi restriction multiplier (clash = fatal attraction / conquest desire)
    elem_a = user_a.get("bazi_element")
    elem_b = user_b.get("bazi_element")
    if elem_a and elem_b:
        rel = analyze_element_relation(elem_a, elem_b)
        if rel["relation"] in ("a_restricts_b", "b_restricts_a"):
            # 邊際遞減：給予剩餘空間的 25% 加成
            base_score += (1.0 - base_score) * 0.25

    # L-11: Anxious × Avoidant attachment lust spike.
    # The anxious×avoidant dynamic generates intense physical desire: the anxious
    # person chases the elusive avoidant; the avoidant feels safe with someone who
    # keeps trying. Classic "addictive chemistry" — lust spikes, partner suffers.
    att_a = user_a.get("attachment_style")
    att_b = user_b.get("attachment_style")
    if att_a and att_b:
        styles = {att_a.lower(), att_b.lower()}
        if "anxious" in styles and "avoidant" in styles:
            base_score *= WEIGHTS["lust_attachment_aa_mult"]

    return _clamp(base_score * 100)


def compute_soul_score(user_a: dict, user_b: dict) -> float:
    """Soul Score (Y axis): depth / long-term commitment (0-100).

    Uses dynamic weighting: optional fields (House 4, Juno, attachment_style,
    Sun-Moon cross) only contribute their weight when present. Missing fields
    are removed from the denominator so Tier 2/3 scores remain proportionally
    accurate.

    Weights (when all present):
      moon       × 0.25  — always present
      mercury    × 0.20  — always present
      saturn     × 0.20  — always present
      house4     × 0.15  — Tier 1 only
      juno       × 0.20  — when ephemeris available
      attachment × 0.20  — when questionnaire filled
      sun_moon   × 0.20  — Sun-Moon cross-aspect (always present)

    Additive bonuses (diminishing-returns, Sprint 2):
      + (1 - base) × 0.30 when BaZi elements are in a generation relationship (相生).
      + (1 - base) × 0.15 when BaZi elements are same (比和).
    """
    score = 0.0
    total_weight = 0.0

    # 1. Moon — always present
    moon = _resolve_aspect(user_a.get("moon_degree"), user_a.get("moon_sign"),
                           user_b.get("moon_degree"), user_b.get("moon_sign"), "harmony")
    score += moon * WEIGHTS["soul_moon"]
    total_weight += WEIGHTS["soul_moon"]

    # 2. Mercury — always present
    mercury = _resolve_aspect(user_a.get("mercury_degree"), user_a.get("mercury_sign"),
                              user_b.get("mercury_degree"), user_b.get("mercury_sign"), "harmony")
    score += mercury * WEIGHTS["soul_mercury"]
    total_weight += WEIGHTS["soul_mercury"]

    # 3. Saturn — always present
    saturn = _resolve_aspect(user_a.get("saturn_degree"), user_a.get("saturn_sign"),
                             user_b.get("saturn_degree"), user_b.get("saturn_sign"), "harmony")
    score += saturn * WEIGHTS["soul_saturn"]
    total_weight += WEIGHTS["soul_saturn"]

    # 4. House 4 — Tier 1 only
    h4_a = user_a.get("house4_sign")
    h4_b = user_b.get("house4_sign")
    if h4_a and h4_b:
        score += _resolve_aspect(user_a.get("house4_degree"), h4_a,
                                 user_b.get("house4_degree"), h4_b, "harmony") * WEIGHTS["soul_house4"]
        total_weight += WEIGHTS["soul_house4"]

    # 5. Juno — when ephemeris available
    # Cross-aspect: A's Juno × B's Moon + B's Juno × A's Moon (averaged).
    # Juno (asteroid of committed partnerships) should measure whether A's partnership
    # ideal (Juno) aligns with B's emotional core (Moon), and vice versa.
    # Same-sign Juno is unreliable: people born in the same year often share Juno signs
    # (Juno moves ~1-2 signs/year), causing age-peers to get artificially high scores.
    juno_a = user_a.get("juno_sign")
    juno_b = user_b.get("juno_sign")
    moon_a = user_a.get("moon_sign")
    moon_b = user_b.get("moon_sign")
    if juno_a and juno_b and moon_a and moon_b:
        juno_a_moon_b = compute_sign_aspect(juno_a, moon_b, "harmony")
        juno_b_moon_a = compute_sign_aspect(juno_b, moon_a, "harmony")
        juno = (juno_a_moon_b + juno_b_moon_a) / 2.0
        score += juno * WEIGHTS["soul_juno"]
        total_weight += WEIGHTS["soul_juno"]

    # 6. Attachment style — when questionnaire filled
    style_a = user_a.get("attachment_style")
    style_b = user_b.get("attachment_style")
    if style_a and style_b and style_a in ATTACHMENT_FIT and style_b in ATTACHMENT_FIT[style_a]:
        attachment = ATTACHMENT_FIT[style_a][style_b]
        score += attachment * WEIGHTS["soul_attachment"]
        total_weight += WEIGHTS["soul_attachment"]

    # 7. Sun-Moon cross-aspect — A's Sun × B's Moon + B's Sun × A's Moon (averaged).
    # Sun (core identity) × Moon (emotional core) is the primary synastry indicator of
    # long-term soul resonance and emotional-identity compatibility.
    # Cross-aspect avoids same-generation inflation (Sun moves ~1°/day, so same-year
    # pairs rarely share Sun signs, but same-month pairs might; cross-aspect is safer).
    sun_a = user_a.get("sun_sign")
    sun_b = user_b.get("sun_sign")
    if sun_a and sun_b and moon_a and moon_b:
        sun_a_moon_b = _resolve_aspect(user_a.get("sun_degree"), sun_a,
                                       user_b.get("moon_degree"), moon_b, "harmony")
        sun_b_moon_a = _resolve_aspect(user_b.get("sun_degree"), sun_b,
                                       user_a.get("moon_degree"), moon_a, "harmony")
        sun_moon_cross = (sun_a_moon_b + sun_b_moon_a) / 2.0
        score += sun_moon_cross * WEIGHTS["soul_sun_moon"]
        total_weight += WEIGHTS["soul_sun_moon"]

    base_score = score / total_weight if total_weight > 0 else NEUTRAL_SIGNAL

    # Multiplier: 八字相生加成
    elem_a = user_a.get("bazi_element")
    elem_b = user_b.get("bazi_element")
    if elem_a and elem_b:
        rel = analyze_element_relation(elem_a, elem_b)
        if rel["relation"] in ("a_generates_b", "b_generates_a"):
            # 邊際遞減：給予剩餘空間的 30% 加成
            base_score += (1.0 - base_score) * 0.30
        elif rel["relation"] == "same":
            # 比和：給予剩餘空間的 15% 加成
            base_score += (1.0 - base_score) * 0.15

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
             (+ saturn_cross × 0.10 additive bonus when saturn signs present)
    soul:    karmic_triggers × 0.60 + useful_god_complement × 0.40
             (+0.10 bonus if frame_break)
             [Chiron removed — handled exclusively by shadow_engine orb checks. See L-12/L-2.]
    When juno absent:  moon×0.55 + bazi_generation×0.45

    Emotional capacity penalty (applied to partner track before zwds_mods):
      Both users < 40: partner × 0.7  (mutual emotional drain)
      Either user < 30: partner × 0.85 (one user is extremely unstable)
    """
    # Emotional capacity penalty for partner track
    capacity_a = user_a.get("emotional_capacity", 50)
    capacity_b = user_b.get("emotional_capacity", 50)

    # harmony planets: friend / partner tracks
    mercury    = _resolve_aspect(user_a.get("mercury_degree"), user_a.get("mercury_sign"),
                                 user_b.get("mercury_degree"), user_b.get("mercury_sign"), "harmony")
    # Jupiter Friend Track: cross-aspect (A's Jupiter × B's Sun + B's Jupiter × A's Sun) / 2.
    # Same-sign Jupiter comparison is unreliable because Jupiter moves ~1 sign/year, so
    # age-peers all share the same Jupiter sign and would be artificially rewarded.
    jupiter_a  = user_a.get("jupiter_sign")
    jupiter_b  = user_b.get("jupiter_sign")
    sun_a      = user_a.get("sun_sign")
    sun_b      = user_b.get("sun_sign")
    jup_a_sun_b = _resolve_aspect(user_a.get("jupiter_degree"), jupiter_a,
                                   user_b.get("sun_degree"), sun_b, "harmony")
    jup_b_sun_a = _resolve_aspect(user_b.get("jupiter_degree"), jupiter_b,
                                   user_a.get("sun_degree"), sun_a, "harmony")
    jupiter    = (jup_a_sun_b + jup_b_sun_a) / 2.0
    moon_a     = user_a.get("moon_sign")
    moon_b     = user_b.get("moon_sign")
    moon       = _resolve_aspect(user_a.get("moon_degree"), moon_a,
                                 user_b.get("moon_degree"), moon_b, "harmony")
    juno_a, juno_b = user_a.get("juno_sign"), user_b.get("juno_sign")
    juno_present = bool(juno_a and juno_b and moon_a and moon_b)
    # Juno Partner Track: cross-aspect (A's Juno × B's Moon + B's Juno × A's Moon) / 2.
    # Juno (asteroid of committed partnerships) should measure whether A's partnership
    # ideal aligns with B's emotional core (Moon), and vice versa.
    # Same-sign Juno is unreliable: people born in the same year often share Juno signs,
    # causing age-peers to get artificially high partner scores.
    if juno_present:
        juno_a_moon_b = compute_sign_aspect(juno_a, moon_b, "harmony")
        juno_b_moon_a = compute_sign_aspect(juno_b, moon_a, "harmony")
        juno = (juno_a_moon_b + juno_b_moon_a) / 2.0
    else:
        juno = 0.0

    # tension planets: passion / soul tracks
    mars  = _resolve_aspect(user_a.get("mars_degree"), user_a.get("mars_sign"),
                            user_b.get("mars_degree"), user_b.get("mars_sign"), "tension")
    venus = _resolve_aspect(user_a.get("venus_degree"), user_a.get("venus_sign"),
                            user_b.get("venus_degree"), user_b.get("venus_sign"), "tension")  # passion context
    # Cross-layer karmic triggers replace same-generation pluto_a vs pluto_b
    karmic = compute_karmic_triggers(user_a, user_b)
    h8_a, h8_b = user_a.get("house8_sign"), user_b.get("house8_sign")
    house8 = _resolve_aspect(user_a.get("house8_degree"), h8_a,
                             user_b.get("house8_degree"), h8_b, "tension") if (h8_a and h8_b) else 0.0
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
        WEIGHTS["track_friend_mercury"] * mercury +
        WEIGHTS["track_friend_jupiter"] * jupiter +
        WEIGHTS["track_friend_bazi"]    * (1.0 if bazi_harmony else 0.0)
    )
    passion = (
        WEIGHTS["track_passion_mars"]    * mars +
        WEIGHTS["track_passion_venus"]   * venus +
        WEIGHTS["track_passion_extreme"] * passion_extremity +
        WEIGHTS["track_passion_bazi"]    * (1.0 if bazi_clash else 0.0)
    )
    if juno_present:
        partner = (moon * WEIGHTS["track_partner_moon"] +
                   juno * WEIGHTS["track_partner_juno"] +
                   (1.0 if bazi_generation else 0.0) * WEIGHTS["track_partner_bazi"])
    else:
        # Redistribute juno's 0.35 weight: moon gets 0.55, bazi gets 0.45
        partner = (moon * WEIGHTS["track_partner_nojuno_moon"] +
                   (1.0 if bazi_generation else 0.0) * WEIGHTS["track_partner_nojuno_bazi"])

    # Saturn cross-aspect bonus (長期穩定 / commitment indicator): A's Saturn × B's Moon
    # + B's Saturn × A's Moon (averaged).  Saturn bounds the partner track because
    # Saturn's discipline and structure against partner's Moon (emotional security)
    # predicts long-term cohabitation compatibility beyond initial attraction.
    saturn_a = user_a.get("saturn_sign")
    saturn_b = user_b.get("saturn_sign")
    if saturn_a and saturn_b and moon_a and moon_b:
        sat_a_moon_b = _resolve_aspect(user_a.get("saturn_degree"), saturn_a,
                                       user_b.get("moon_degree"), moon_b, "harmony")
        sat_b_moon_a = _resolve_aspect(user_b.get("saturn_degree"), saturn_b,
                                       user_a.get("moon_degree"), moon_a, "harmony")
        saturn_cross = (sat_a_moon_b + sat_b_moon_a) / 2.0
        partner += saturn_cross * WEIGHTS["track_partner_saturn_cross"]

    # L-12: Chiron removed from soul_track — prevents double-counting with shadow_engine.
    # L-2:  Chiron is generational (7 yrs/sign) — sign-level fallback creates false positives for age-peers.
    # Shadow engine handles Chiron wound triggers via orb-based degree checks.
    soul_track = (karmic               * WEIGHTS["track_soul_nochiron_karmic"] +
                  useful_god_complement * WEIGHTS["track_soul_nochiron_useful_god"])

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


# ── Favorable Element Resonance (喜用神互補) — Sprint 7 ──────────────────────

def compute_favorable_element_resonance(
    strength_a: dict,
    strength_b: dict,
    current_soul: float = 50.0,
) -> dict:
    """Compute cross-chart favorable element resonance.

    If B's dominant_elements overlap with A's favorable_elements → B is A's 貴人.
    If A's dominant_elements overlap with B's favorable_elements → A is B's 貴人.
    Bidirectional → perfect resonance.

    Parameters
    ----------
    strength_a : dict  Output of evaluate_day_master_strength for user A.
    strength_b : dict  Output of evaluate_day_master_strength for user B.
    current_soul : float  Current soul score for marginal diminishing calc.

    Returns
    -------
    dict:
        soul_mod : float   — adjustment to soul score (marginal diminishing)
        badges   : List[str]
        b_helps_a : bool
        a_helps_b : bool
    """
    fav_a = set(strength_a.get("favorable_elements", []))
    fav_b = set(strength_b.get("favorable_elements", []))
    dom_a = set(strength_a.get("dominant_elements", []))
    dom_b = set(strength_b.get("dominant_elements", []))

    b_helps_a = bool(fav_a & dom_b)  # B's strength fills A's need
    a_helps_b = bool(fav_b & dom_a)  # A's strength fills B's need
    bidirectional = b_helps_a and a_helps_b

    soul_mod = 0.0
    badges: list = []
    headroom = max(100.0 - current_soul, 0.0)

    if bidirectional:
        soul_mod = headroom * 0.35
        badges.append("完美互補：靈魂能量共振")
    elif b_helps_a or a_helps_b:
        soul_mod = headroom * 0.20
        badges.append("專屬幸運星")

    return {
        "soul_mod":  round(soul_mod, 2),
        "badges":    badges,
        "b_helps_a": b_helps_a,
        "a_helps_b": a_helps_b,
    }


def check_synastry_mutual_reception(chart_a: dict, chart_b: dict) -> List[str]:
    """Check cross-chart mutual reception for three key planet pairs.

    Uses MODERN_RULERSHIPS from psychology.py.
    Missing sign fields are silently skipped — never crashes.

    Returns list of badge strings (empty if none detected).
    """

    def _is_mr(
        sign_x: Optional[str], sign_y: Optional[str],
        planet_x: str, planet_y: str
    ) -> bool:
        if not sign_x or not sign_y:
            return False
        return (
            MODERN_RULERSHIPS.get(sign_x.lower()) == planet_y and
            MODERN_RULERSHIPS.get(sign_y.lower()) == planet_x
        )

    badges: List[str] = []

    a_sun   = chart_a.get("sun_sign")
    a_moon  = chart_a.get("moon_sign")
    a_venus = chart_a.get("venus_sign")
    a_mars  = chart_a.get("mars_sign")
    b_sun   = chart_b.get("sun_sign")
    b_moon  = chart_b.get("moon_sign")
    b_venus = chart_b.get("venus_sign")
    b_mars  = chart_b.get("mars_sign")

    # 1. 日月互溶 (Sun ↔ Moon)
    if _is_mr(a_sun, b_moon, "Sun", "Moon") or _is_mr(b_sun, a_moon, "Sun", "Moon"):
        badges.append("古典業力：日月互溶 (靈魂深處的陰陽完美契合)")

    # 2. 金火互溶 (Venus ↔ Mars)
    if _is_mr(a_venus, b_mars, "Venus", "Mars") or _is_mr(b_venus, a_mars, "Venus", "Mars"):
        badges.append("古典業力：金火互溶 (無法抗拒的致命吸引力與肉體契合)")

    # 3. 金月互溶 (Venus ↔ Moon)
    if _is_mr(a_venus, b_moon, "Venus", "Moon") or _is_mr(b_venus, a_moon, "Venus", "Moon"):
        badges.append("古典業力：金月互溶 (無條件的溫柔接納與情緒滋養)")

    return badges


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

    # ── Phase II: Psychology Modifiers ────────────────────────────────────────────
    # Additive modifiers applied after four-track computation. Only activate when
    # the relevant chart data is present — degrade gracefully otherwise.

    soul_adj    = 0.0
    lust_adj    = 0.0
    partner_adj = 0.0
    high_voltage      = False
    psychological_tags: List[str] = []
    resonance_badges: List[str] = []

    # 1. Shadow & Wound Engine (Chiron + 12th house cross-chart triggers)
    _shadow: dict = {}
    try:
        _shadow = compute_shadow_and_wound(user_a, user_b)
        soul_adj    += _shadow["soul_mod"]
        lust_adj    += _shadow["lust_mod"]
        partner_adj += _shadow.get("partner_mod", 0.0)
        high_voltage = high_voltage or _shadow["high_voltage"]
        psychological_tags.extend(_shadow["shadow_tags"])
    except Exception:
        pass   # never block matching for shadow engine errors

    # 2. Dynamic Attachment + Attachment Dynamics
    _att_a = user_a.get("attachment_style")
    _att_b = user_b.get("attachment_style")
    if _att_a and _att_b:
        try:
            _dyn_a, _dyn_b = compute_dynamic_attachment(
                _att_a, _att_b, user_a, user_b
            )
            _att = compute_attachment_dynamics(_dyn_a, _dyn_b)
            soul_adj    += _att["soul_mod"]
            lust_adj    += _att["lust_mod"]
            partner_adj += _att["partner_mod"]
            high_voltage = high_voltage or _att["high_voltage"]
            if _att["trap_tag"]:
                psychological_tags.append(_att["trap_tag"])
        except Exception:
            pass

    # 3. Elemental Fulfillment (from pre-computed element_profile stored in DB)
    _ep_a = user_a.get("element_profile")
    _ep_b = user_b.get("element_profile")
    if _ep_a and _ep_b:
        try:
            soul_adj += compute_elemental_fulfillment(_ep_a, _ep_b)
        except Exception:
            pass

    # 4. Favorable Element Resonance (Sprint 7)
    try:
        _str_a = evaluate_day_master_strength(user_a.get("bazi") or {})
        _str_b = evaluate_day_master_strength(user_b.get("bazi") or {})
        if _str_a.get("favorable_elements") or _str_b.get("favorable_elements"):
            _res = compute_favorable_element_resonance(_str_a, _str_b, current_soul=soul)
            soul_adj += _res["soul_mod"]
            resonance_badges.extend(_res["badges"])
    except Exception:
        pass

    # 5. Synastry Mutual Reception (V3 Classical Astrology)
    _synastry_mr_badges: List[str] = []
    try:
        _wa = user_a.get("western_chart", user_a)
        _wb = user_b.get("western_chart", user_b)
        _synastry_mr_badges = check_synastry_mutual_reception(_wa, _wb)
        for _ in _synastry_mr_badges:
            soul_adj += (100.0 - soul) * 0.22   # diminishing returns per badge
    except Exception:
        pass

    # L-1: Cap shadow modifiers before applying — prevents overflow from multiple simultaneous triggers
    # soul: max +40 (meaningful boost), min -30 (repulsion visible but not fatal)
    # lust: max +40, min -30 (same rationale)
    # partner: max +25 (narrower — partner track is more delicate), min -20
    soul_adj    = max(min(soul_adj,    40.0), -30.0)
    lust_adj    = max(min(lust_adj,    40.0), -30.0)
    partner_adj = max(min(partner_adj, 25.0), -20.0)

    # Apply modifiers — clamp each track to [0, 100]
    if soul_adj != 0.0:
        tracks["soul"] = _clamp(tracks["soul"] + soul_adj)
        soul           = _clamp(soul + soul_adj)   # propagate to Y-axis score
    if lust_adj != 0.0:
        tracks["passion"] = _clamp(tracks["passion"] + lust_adj)
        lust              = _clamp(lust + lust_adj)   # propagate to X-axis score
    if partner_adj != 0.0:
        tracks["partner"] = _clamp(tracks["partner"] + partner_adj)

    # ── Karmic Tension Index (0-100) ──────────────────────────────────────────
    # 痛感（partner_mod）佔最大視覺比重；情慾執念次之；靈魂羈絆為隱性張力
    # DESIGN DECISION: reads _shadow (astro/karmic layer) only — intentionally
    # excludes attachment dynamics (_att) and elemental fulfillment (_ep).
    # Rationale: karmic_tension measures fated friction encoded in birth charts,
    # not psychological attachment patterns which are captured in psychological_tags.
    # If _shadow fell back to {} (engine error), karmic_tension = 0.0 (safe default).
    raw_tension = (
        abs(_shadow.get("partner_mod", 0.0)) * 1.5 +
        abs(_shadow.get("lust_mod",    0.0)) * 1.0 +
        abs(_shadow.get("soul_mod",    0.0)) * 0.5
    )
    karmic_tension = _clamp(raw_tension)

    # ── Resonance Badges ──────────────────────────────────────────────────────

    # Badge A: 命理雙重認證 — soul ≥ 80 且八字相生/比和
    if soul >= 80 and bazi_relation in ("a_generates_b", "b_generates_a", "same"):
        resonance_badges.append("命理雙重認證")

    # Badge B: 三界共振：宿命伴侶 — Badge A + ZWDS SOULMATE
    if "命理雙重認證" in resonance_badges \
            and zwds_result and zwds_result.get("spiciness_level") == "SOULMATE":
        resonance_badges.append("三界共振：宿命伴侶")

    # Badge C: 進化型靈魂伴侶 — karmic_tension ≥ 30 且 soul ≥ 75
    if karmic_tension >= 30 and soul >= 75:
        resonance_badges.append("進化型靈魂伴侶：虐戀與升級")

    # Synastry MR badges (V3 Classical Astrology)
    resonance_badges.extend(_synastry_mr_badges)

    # ── Dynamic Psychological Triggers ────────────────────────────────────────
    # Surface high-signal psychological dynamics as named triggers so the LLM
    # can apply targeted decoding scripts instead of guessing from raw scores.
    psychological_triggers: List[str] = []

    # 1. Attachment-trap: classic anxious-avoidant chase-and-flee loop
    if "Anxious_Avoidant_Trap" in psychological_tags:
        psychological_triggers.append("attachment_trap: anxious_avoidant")

    # 2. Intimacy fear / soul runner — soul resonance so intense it triggers flight
    if soul >= 80 and high_voltage:
        psychological_triggers.append("intimacy_fear: soul_runner")

    # 3. Healing anchor — one secure person softens the other's attachment wound
    if "Healing_Anchor" in psychological_tags:
        psychological_triggers.append("attachment_healing: secure_base")

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

    # high_voltage from psychology modifiers upgrades spiciness if not already HIGH_VOLTAGE/SOULMATE
    if high_voltage and spiciness not in ("HIGH_VOLTAGE", "SOULMATE"):
        spiciness = "HIGH_VOLTAGE"

    return {
        "lust_score":              round(lust, 1),
        "soul_score":              round(soul, 1),
        "harmony_score":           round(soul, 1),
        "karmic_tension":          round(karmic_tension, 1),
        "resonance_badges":        resonance_badges,
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
        "psychological_tags":      psychological_tags,
        "psychological_triggers":  psychological_triggers,
        "high_voltage":            high_voltage,
        "element_profile_a":       user_a.get("element_profile"),
        "element_profile_b":       user_b.get("element_profile"),
        "defense_mechanisms": {
            "viewer": zwds_result.get("defense_a", []) if zwds_result else [],
            "target": zwds_result.get("defense_b", []) if zwds_result else [],
        },
        "layered_analysis":        zwds_result.get("layered_analysis", {}) if zwds_result else {},
    }
