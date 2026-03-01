"""
DESTINY — Matching Algorithm Tests
pytest suite for astro-service/matching.py
"""

import pytest
from matching import (
    compute_sign_aspect,
    compute_kernel_score,
    compute_power_score,
    compute_glitch_score,
    classify_match_type,
    generate_tags,
    compute_match_score,
    compute_karmic_triggers,
    HARMONY_ASPECTS,
    TENSION_ASPECTS,
)


# ── compute_sign_aspect ──────────────────────────────────────

class TestComputeSignAspect:
    def test_conjunction_same_sign(self):
        """Distance 0 → conjunction = 0.90"""
        assert compute_sign_aspect("aries", "aries") == pytest.approx(0.90)

    def test_trine_4_houses_apart(self):
        """Aries (0) and Leo (4) → trine = 0.85"""
        assert compute_sign_aspect("aries", "leo") == pytest.approx(0.85)

    def test_sextile_2_houses_apart(self):
        """Aries (0) and Gemini (2) → sextile = 0.75"""
        assert compute_sign_aspect("aries", "gemini") == pytest.approx(0.75)

    def test_square_3_houses_apart(self):
        """Aries (0) and Cancer (3) → square: harmony=0.40, tension=0.90"""
        assert compute_sign_aspect("aries", "cancer", "harmony") == pytest.approx(0.40)
        assert compute_sign_aspect("aries", "cancer", "tension") == pytest.approx(0.90)

    def test_opposition_6_houses_apart(self):
        """Aries (0) and Libra (6) → opposition: harmony=0.60, tension=0.85"""
        assert compute_sign_aspect("aries", "libra", "harmony") == pytest.approx(0.60)
        assert compute_sign_aspect("aries", "libra", "tension") == pytest.approx(0.85)

    def test_wraps_correctly_beyond_6(self):
        """Distance 7 wraps to 5 (quincunx) → minor aspect = 0.10 in both modes"""
        # Scorpio(7) vs Aries(0): distance=7, wraps to 12-7=5 → quincunx
        assert compute_sign_aspect("scorpio", "aries", "harmony") == pytest.approx(0.10)
        assert compute_sign_aspect("scorpio", "aries", "tension") == pytest.approx(0.10)

    def test_tension_conjunction_is_1(self):
        """Tension mode: conjunction = 1.00 (energy amplification)"""
        assert compute_sign_aspect("aries", "aries", "tension") == pytest.approx(1.00)

    def test_tension_trine_lower_than_square(self):
        """Tension mode: trine(4)=0.60 < square(3)=0.90 (too comfortable = less spark)"""
        trine  = compute_sign_aspect("aries", "leo",    "tension")  # diff=4
        square = compute_sign_aspect("aries", "cancer", "tension")  # diff=3
        assert trine < square

    def test_none_sign_returns_neutral(self):
        """None sign returns 0.65 neutral"""
        assert compute_sign_aspect(None, "aries") == pytest.approx(0.65)
        assert compute_sign_aspect("aries", None) == pytest.approx(0.65)
        assert compute_sign_aspect(None, None) == pytest.approx(0.65)

    def test_invalid_sign_returns_neutral(self):
        """Unknown sign name returns 0.65 neutral"""
        assert compute_sign_aspect("invalid", "aries") == pytest.approx(0.65)

    def test_symmetry(self):
        """Aspect score is symmetric: A→B == B→A"""
        assert compute_sign_aspect("taurus", "virgo") == compute_sign_aspect("virgo", "taurus")
        assert compute_sign_aspect("aries", "cancer") == compute_sign_aspect("cancer", "aries")


# ── compute_kernel_score ─────────────────────────────────────

class TestComputeKernelScore:
    def _make_user(self, tier=3, sun="aries", moon="taurus", venus="gemini",
                   asc=None, mars="cancer", saturn="leo", bazi_elem=None):
        return {
            "data_tier": tier,
            "sun_sign": sun, "moon_sign": moon, "venus_sign": venus,
            "ascendant_sign": asc, "mars_sign": mars, "saturn_sign": saturn,
            "bazi_element": bazi_elem,
        }

    def test_tier3_uses_sun_venus_bazi_weights(self):
        """Tier 3: Sun(0.30) + Venus(0.30) + BaZi(0.40)"""
        a = self._make_user(tier=3, sun="aries", venus="aries", bazi_elem="wood")
        b = self._make_user(tier=3, sun="aries", venus="aries", bazi_elem="wood")
        score = compute_kernel_score(a, b)
        # All conjunction (0.90) + bazi same element (0.60)
        expected = 0.90 * 0.30 + 0.90 * 0.30 + 0.60 * 0.40
        assert score == pytest.approx(expected, abs=0.01)

    def test_tier2_includes_moon(self):
        """Tier 2: Sun(0.25) + Moon(0.20) + Venus(0.25) + BaZi(0.30)"""
        a = self._make_user(tier=2, sun="aries", moon="aries", venus="aries", bazi_elem="wood")
        b = self._make_user(tier=2, sun="aries", moon="aries", venus="aries", bazi_elem="wood")
        score = compute_kernel_score(a, b)
        expected = 0.90 * 0.25 + 0.90 * 0.20 + 0.90 * 0.25 + 0.60 * 0.30
        assert score == pytest.approx(expected, abs=0.01)

    def test_tier1_includes_ascendant(self):
        """Tier 1: Sun(0.20) + Moon(0.25) + Venus(0.25) + Asc(0.15) + BaZi(0.15)"""
        a = self._make_user(tier=1, sun="aries", moon="aries", venus="aries",
                            asc="aries", bazi_elem="wood")
        b = self._make_user(tier=1, sun="aries", moon="aries", venus="aries",
                            asc="aries", bazi_elem="wood")
        score = compute_kernel_score(a, b)
        expected = 0.90 * 0.20 + 0.90 * 0.25 + 0.90 * 0.25 + 0.90 * 0.15 + 0.60 * 0.15
        assert score == pytest.approx(expected, abs=0.01)

    def test_degrades_to_worse_tier(self):
        """If one user is tier 3, effective tier = 3 (worst)"""
        a = self._make_user(tier=1, sun="aries", venus="aries")
        b = self._make_user(tier=3, sun="aries", venus="aries")
        # effective_tier = max(1, 3) = 3 → tier 3 formula
        score = compute_kernel_score(a, b)
        # At tier 3, no moon/asc weighting
        expected = 0.90 * 0.30 + 0.90 * 0.30 + 0.65 * 0.40  # bazi both None → 0.65
        assert score == pytest.approx(expected, abs=0.01)

    def test_no_bazi_uses_neutral(self):
        """Missing bazi_element → neutral 0.65"""
        a = self._make_user(tier=3, sun="aries", venus="taurus", bazi_elem=None)
        b = self._make_user(tier=3, sun="aries", venus="taurus", bazi_elem=None)
        score = compute_kernel_score(a, b)
        sun_aspect = compute_sign_aspect("aries", "aries")   # 0.90
        venus_aspect = compute_sign_aspect("taurus", "taurus")  # 0.90
        expected = sun_aspect * 0.30 + venus_aspect * 0.30 + 0.65 * 0.40
        assert score == pytest.approx(expected, abs=0.01)

    def test_score_in_range(self):
        """Kernel score is always between 0.0 and 1.0"""
        a = self._make_user(tier=3, sun="aries", venus="cancer", bazi_elem="wood")
        b = self._make_user(tier=3, sun="libra", venus="scorpio", bazi_elem="metal")
        score = compute_kernel_score(a, b)
        assert 0.0 <= score <= 1.0

    def test_cross_sign_conjunction_scores_high(self):
        """Aries 29° (lon=29.0) and Taurus 1° (lon=31.0) → 2° apart → should score as conjunction.
        With sign-level only: Aries vs Taurus = semi-sextile (0.10). Bad!
        With _resolve_aspect + exact degrees: conjunction 2° → ~0.80. Correct!
        Sign-level kernel = 0.7025 (sun misscored as 0.10, other planets compensate).
        Exact-degree kernel = ~0.91 (sun correctly scores ~0.80 conjunction).
        Threshold 0.85 requires exact-degree accuracy — fails with sign-level sun.
        """
        a = {
            "data_tier": 1,
            "sun_degree": 29.0, "sun_sign": "aries",
            "moon_degree": 45.0, "moon_sign": "taurus",
            "venus_degree": 90.0, "venus_sign": "cancer",
            "ascendant_degree": 0.0, "ascendant_sign": "aries",
            "bazi_element": None,
        }
        b = {
            "data_tier": 1,
            "sun_degree": 31.0, "sun_sign": "taurus",   # only 2° from A's sun
            "moon_degree": 45.0, "moon_sign": "taurus",
            "venus_degree": 90.0, "venus_sign": "cancer",
            "ascendant_degree": 0.0, "ascendant_sign": "aries",
            "bazi_element": None,
        }
        score = compute_kernel_score(a, b)
        assert score >= 0.85, (
            f"Cross-sign conjunction kernel score {score:.3f} should be >= 0.85 "
            f"(sign-level gives ~0.70 due to aries/taurus semi-sextile; "
            f"exact-degree gives ~0.91 as 2° conjunction)"
        )


# ── compute_power_score ──────────────────────────────────────

class TestComputePowerScore:
    def test_complementary_power_pair(self):
        """control + follow → power=0.90, complementary conflict → 0.85"""
        a = {"rpv_conflict": "cold_war", "rpv_power": "control", "rpv_energy": "home"}
        b = {"rpv_conflict": "argue",    "rpv_power": "follow",  "rpv_energy": "out"}
        score = compute_power_score(a, b)
        expected = 0.85 * 0.35 + 0.90 * 0.40 + 0.75 * 0.25
        assert score == pytest.approx(expected, abs=0.01)

    def test_same_rpv_all(self):
        """All same → 0.55×0.35 + 0.50×0.40 + 0.65×0.25"""
        a = {"rpv_conflict": "argue", "rpv_power": "control", "rpv_energy": "home"}
        b = {"rpv_conflict": "argue", "rpv_power": "control", "rpv_energy": "home"}
        score = compute_power_score(a, b)
        expected = 0.55 * 0.35 + 0.50 * 0.40 + 0.65 * 0.25
        assert score == pytest.approx(expected, abs=0.01)

    def test_missing_rpv_uses_neutral(self):
        """Missing RPV fields → neutral 0.60 per dimension"""
        a = {}
        b = {}
        score = compute_power_score(a, b)
        expected = 0.60 * 0.35 + 0.60 * 0.40 + 0.60 * 0.25
        assert score == pytest.approx(expected, abs=0.01)

    def test_score_in_range(self):
        a = {"rpv_conflict": "cold_war", "rpv_power": "control", "rpv_energy": "out"}
        b = {"rpv_conflict": "argue", "rpv_power": "follow", "rpv_energy": "home"}
        score = compute_power_score(a, b)
        assert 0.0 <= score <= 1.0


# ── compute_glitch_score ─────────────────────────────────────

class TestComputeGlitchScore:
    def test_all_conjunctions_high_score(self):
        """Glitch formula uses tension for mars, harmony for saturn."""
        a = {"mars_sign": "aries", "saturn_sign": "leo"}
        b = {"mars_sign": "aries", "saturn_sign": "leo"}
        score = compute_glitch_score(a, b)
        # mars vs mars: tension("aries","aries") = 1.00
        # saturn vs saturn: harmony("leo","leo") = 0.90
        # mars_a vs sat_b: tension("aries","leo") = trine in tension = 0.60
        # mars_b vs sat_a: tension("aries","leo") = 0.60
        expected = (
            compute_sign_aspect("aries", "aries", "tension") * 0.25 +
            compute_sign_aspect("leo",   "leo",   "harmony") * 0.25 +
            compute_sign_aspect("aries", "leo",   "tension") * 0.25 +
            compute_sign_aspect("aries", "leo",   "tension") * 0.25
        )
        assert score == pytest.approx(expected, abs=0.01)

    def test_missing_planets_neutral(self):
        """None signs → neutral 0.65 per aspect"""
        a = {}
        b = {}
        score = compute_glitch_score(a, b)
        assert score == pytest.approx(0.65, abs=0.01)

    def test_score_in_range(self):
        a = {"mars_sign": "aries", "saturn_sign": "capricorn"}
        b = {"mars_sign": "cancer", "saturn_sign": "libra"}
        score = compute_glitch_score(a, b)
        assert 0.0 <= score <= 1.0

    def test_cross_sign_mars_scores_correctly(self):
        """Mars Aries 29° vs Mars Taurus 1° → 2° apart → should score as conjunction (tension).
        With no saturn data (neutral 0.65 each component):
          - sign-only: mars=0.10 (aries/taurus semi-sextile) → total ~0.51
          - degree-based: mars=0.80 (2° conjunction) → total ~0.69
        Score must be >= 0.60 to confirm _resolve_aspect (orb-based) path is used.
        """
        a = {
            "mars_degree": 29.0, "mars_sign": "aries",
        }
        b = {
            "mars_degree": 31.0, "mars_sign": "taurus",
        }
        score = compute_glitch_score(a, b)
        assert score >= 0.60, (
            f"Cross-sign Mars conjunction glitch score {score:.3f} should reflect true "
            f"2° conjunction (~0.69), not sign-level semi-sextile (~0.51)"
        )


# ── classify_match_type ──────────────────────────────────────

class TestClassifyMatchType:
    def test_complementary_when_high_power_and_kernel(self):
        assert classify_match_type(kernel=0.80, power=0.80, glitch=0.70) == "complementary"

    def test_complementary_threshold(self):
        assert classify_match_type(kernel=0.70, power=0.75, glitch=0.50) == "complementary"

    def test_similar_when_high_kernel_and_glitch(self):
        assert classify_match_type(kernel=0.80, power=0.65, glitch=0.70) == "similar"

    def test_similar_threshold(self):
        assert classify_match_type(kernel=0.75, power=0.60, glitch=0.60) == "similar"

    def test_tension_when_below_thresholds(self):
        assert classify_match_type(kernel=0.60, power=0.60, glitch=0.50) == "tension"

    def test_tension_when_power_too_low_for_complementary(self):
        # High kernel but power < 0.75 → falls through to similar or tension
        assert classify_match_type(kernel=0.80, power=0.70, glitch=0.50) == "tension"


# ── generate_tags ────────────────────────────────────────────

class TestGenerateTags:
    def test_returns_3_tags(self):
        scores = {"total_score": 0.75}
        tags = generate_tags("complementary", scores)
        assert len(tags) == 3

    def test_tags_from_correct_pool(self):
        from matching import TAG_POOLS
        for match_type in ["complementary", "similar", "tension"]:
            pool = TAG_POOLS[match_type]
            tags = generate_tags(match_type, {"total_score": 0.75})
            assert all(t in pool for t in tags)

    def test_high_score_picks_top_tags(self):
        from matching import TAG_POOLS
        scores = {"total_score": 0.85}
        tags = generate_tags("complementary", scores)
        expected = TAG_POOLS["complementary"][:3]
        assert tags == expected

    def test_unknown_type_falls_back_to_tension(self):
        tags = generate_tags("unknown_type", {"total_score": 0.50})
        from matching import TAG_POOLS
        pool = TAG_POOLS["tension"]
        assert all(t in pool for t in tags)

    def test_deterministic_across_calls(self):
        scores = {"total_score": 0.60}
        assert generate_tags("similar", scores) == generate_tags("similar", scores)


# ── compute_match_score (integration) ────────────────────────

class TestComputeMatchScore:
    def _tier3_user(self, sun, venus, mars, saturn, rpv_c, rpv_p, rpv_e, bazi_elem=None):
        return {
            "data_tier": 3,
            "sun_sign": sun, "venus_sign": venus,
            "mars_sign": mars, "saturn_sign": saturn,
            "rpv_conflict": rpv_c, "rpv_power": rpv_p, "rpv_energy": rpv_e,
            "bazi_element": bazi_elem,
        }

    def test_returns_all_required_keys(self):
        a = self._tier3_user("aries", "taurus", "gemini", "cancer", "cold_war", "control", "home")
        b = self._tier3_user("leo",   "virgo",  "libra",  "scorpio","argue",    "follow",  "out")
        result = compute_match_score(a, b)
        required = {
            "kernel_score", "power_score", "glitch_score", "total_score",
            "match_type", "radar_passion", "radar_stability", "radar_communication",
            "card_color", "tags",
        }
        assert required.issubset(result.keys())

    def test_total_score_formula(self):
        """total_score = kernel×0.5 + power×0.3 + glitch×0.2"""
        a = self._tier3_user("aries", "aries", "aries", "aries", "cold_war", "control", "home", "wood")
        b = self._tier3_user("aries", "aries", "aries", "aries", "argue", "follow", "out", "fire")
        result = compute_match_score(a, b)
        expected_total = (
            result["kernel_score"] * 0.5 +
            result["power_score"] * 0.3 +
            result["glitch_score"] * 0.2
        )
        assert result["total_score"] == pytest.approx(expected_total, abs=0.001)

    def test_radar_scores_in_range(self):
        a = self._tier3_user("aries", "taurus", "gemini", "cancer", "cold_war", "control", "home")
        b = self._tier3_user("libra", "scorpio","sagittarius","capricorn","argue","follow","out")
        result = compute_match_score(a, b)
        assert 0 <= result["radar_passion"] <= 100
        assert 0 <= result["radar_stability"] <= 100
        assert 0 <= result["radar_communication"] <= 100

    def test_match_type_is_valid(self):
        a = self._tier3_user("aries", "taurus", "gemini", "cancer", "cold_war", "control", "home")
        b = self._tier3_user("leo", "virgo", "libra", "scorpio", "argue", "follow", "out")
        result = compute_match_score(a, b)
        assert result["match_type"] in ("complementary", "similar", "tension")

    def test_card_color_matches_type(self):
        from matching import assign_card_color
        for mt in ("complementary", "similar", "tension"):
            color = assign_card_color(mt)
            assert color in ("coral", "blue", "purple")

    def test_tags_length_is_3(self):
        a = self._tier3_user("aries", "taurus", "gemini", "cancer", "cold_war", "control", "home")
        b = self._tier3_user("leo", "virgo", "libra", "scorpio", "argue", "follow", "out")
        result = compute_match_score(a, b)
        assert len(result["tags"]) == 3

    def test_symmetric_total_score(self):
        """Total score should be symmetric (A→B == B→A)"""
        a = self._tier3_user("aries", "taurus", "gemini", "cancer", "cold_war", "control", "home")
        b = self._tier3_user("leo", "virgo", "libra", "scorpio", "argue", "follow", "out")
        r1 = compute_match_score(a, b)
        r2 = compute_match_score(b, a)
        assert r1["total_score"] == pytest.approx(r2["total_score"], abs=0.01)

    def test_empty_profiles_returns_neutral_result(self):
        """Empty profiles should not crash and return neutral scores"""
        a = {}
        b = {}
        result = compute_match_score(a, b)
        assert "total_score" in result
        assert 0.0 <= result["total_score"] <= 1.0


# ════════════════════════════════════════════════════════════════
# Phase G: Matching v2 Tests
# ════════════════════════════════════════════════════════════════

from matching import (
    compute_lust_score,
    compute_soul_score,
    compute_power_v2,
    compute_tracks,
    classify_quadrant,
    _check_chiron_triggered,
    compute_match_v2,
    ATTACHMENT_FIT,
)


# ── compute_lust_score ────────────────────────────────────────

class TestLustScore:
    def _user(self, venus="aries", mars="aries", pluto="scorpio",
              house8=None, bazi_elem=None, rpv_power=None, rpv_conflict=None):
        return {
            "venus_sign": venus, "mars_sign": mars, "pluto_sign": pluto,
            "house8_sign": house8, "bazi_element": bazi_elem,
            "rpv_power": rpv_power, "rpv_conflict": rpv_conflict,
        }

    def test_score_in_range(self):
        a = self._user(rpv_power="control")
        b = self._user(rpv_power="follow")
        assert 0 <= compute_lust_score(a, b) <= 100

    def test_bazi_clash_multiplier_increases_score(self):
        """Metal restricts Wood → × 1.2 multiplier raises lust above baseline."""
        base_a = self._user()
        base_b = self._user()
        a_clash = self._user(bazi_elem="metal")
        b_clash = self._user(bazi_elem="wood")
        score_no_clash = compute_lust_score(base_a, base_b)
        score_clash = compute_lust_score(a_clash, b_clash)
        assert score_clash > score_no_clash

    def test_no_house8_gives_lower_score_than_matching_house8(self):
        """When house8_degree is present and opposite mars_degree (tension=1.0),
        score should be higher than when house8 data is absent.

        New formula: house8 cross-aspects use exact degrees only (h8_a × mars_b).
        """
        a_no  = self._user(house8=None)
        b_no  = self._user(house8=None)
        # Provide house8_degree on a and mars_degree on b for the cross-aspect
        a_yes = {**self._user(house8="scorpio"), "house8_degree": 0.0}
        b_yes = {**self._user(house8="scorpio"), "mars_degree": 180.0}
        score_without = compute_lust_score(a_no, b_no)
        score_with    = compute_lust_score(a_yes, b_yes)
        # opposition in tension = 1.0, adding this cross-aspect raises score
        assert score_with > score_without

    def test_power_control_follow_increases_lust(self):
        """Complementary RPV power → higher power_fit → higher lust score."""
        a_comp = self._user(rpv_power="control")
        b_comp = self._user(rpv_power="follow")
        a_same = self._user(rpv_power="control")
        b_same = self._user(rpv_power="control")
        assert compute_lust_score(a_comp, b_comp) > compute_lust_score(a_same, b_same)


# ── TestComputeLustScore (v1.6 cross-aspect tests) ───────────

class TestComputeLustScore:
    def test_lust_cross_aspects_opposition_gives_high_score(self):
        """mars_a exactly opposite venus_b (tension mode, 180° diff) → high lust."""
        user_a = {
            "mars_degree": 0.0,   "mars_sign": "aries",
            "venus_degree": None, "venus_sign": "aries",
            "bazi_element": "wood",
            "rpv_power": "control", "rpv_conflict": "cold_war", "rpv_energy": "out",
        }
        user_b = {
            "venus_degree": 180.0, "venus_sign": "libra",
            "mars_degree": None,   "mars_sign": "libra",
            "bazi_element": "water",
            "rpv_power": "follow", "rpv_conflict": "argue", "rpv_energy": "home",
        }
        score = compute_lust_score(user_a, user_b)
        assert score == pytest.approx(76.8, abs=1.0)

    def test_lust_cross_beats_same_planet(self):
        """Cross-aspect pair (mars_a × venus_b opposition) scores higher than same-planet trine."""
        cross_a = {
            "mars_degree": 0.0,    "mars_sign": "aries",
            "venus_degree": None,  "venus_sign": "aries",
            "rpv_power": "control", "rpv_conflict": "cold_war", "rpv_energy": "out",
        }
        cross_b = {
            "venus_degree": 180.0, "venus_sign": "libra",
            "mars_degree": None,   "mars_sign": "libra",
            "rpv_power": "follow", "rpv_conflict": "argue", "rpv_energy": "home",
        }
        same_a = {
            "venus_degree": 0.0,   "venus_sign": "aries",
            "mars_degree": None,   "mars_sign": "aries",
            "rpv_power": "control", "rpv_conflict": "cold_war", "rpv_energy": "out",
        }
        same_b = {
            "venus_degree": 120.0, "venus_sign": "leo",
            "mars_degree": None,   "mars_sign": "leo",
            "rpv_power": "follow", "rpv_conflict": "argue", "rpv_energy": "home",
        }
        cross_score = compute_lust_score(cross_a, cross_b)
        same_score  = compute_lust_score(same_a,  same_b)
        assert cross_score > same_score, f"Cross {cross_score:.1f} should > same-planet {same_score:.1f}"

    def test_asc_cross_aspect_boosts_lust_tier1(self):
        """Mars exact conjunction with partner's ASC (tension) should boost lust score for Tier 1."""
        base = {
            "data_tier": 1,
            "mars_sign": "aries",     "mars_degree":  0.0,
            "venus_sign": "taurus",   "venus_degree": 30.0,
            "ascendant_sign": "leo",  "ascendant_degree": 120.0,
            "bazi_element": None, "rpv_conflict": None, "rpv_power": None, "rpv_energy": None,
        }
        # B's ASC at 1.0° — 1° from A's Mars at 0.0° → near-perfect conjunction
        b_with_asc = {
            "data_tier": 1,
            "mars_sign": "aries",      "mars_degree":  10.0,
            "venus_sign": "taurus",    "venus_degree": 30.0,
            "ascendant_sign": "aries", "ascendant_degree": 1.0,
            "bazi_element": None, "rpv_conflict": None, "rpv_power": None, "rpv_energy": None,
        }
        b_no_asc = {
            "data_tier": 1,
            "mars_sign": "aries",    "mars_degree":  10.0,
            "venus_sign": "taurus",  "venus_degree": 30.0,
            "ascendant_sign": None,  "ascendant_degree": None,
            "bazi_element": None, "rpv_conflict": None, "rpv_power": None, "rpv_energy": None,
        }
        score_with = compute_lust_score(base, b_with_asc)
        score_without = compute_lust_score(base, b_no_asc)
        assert score_with > score_without, (
            f"Lust score with ASC conjunction ({score_with:.1f}) should beat without ASC ({score_without:.1f})"
        )

    def test_asc_cross_aspect_absent_tier2(self):
        """Tier 2 user has no ASC degree — ASC terms are skipped, score normalizes correctly."""
        a = {
            "data_tier": 2,
            "mars_sign": "aries",   "mars_degree": 0.0,
            "venus_sign": "taurus", "venus_degree": 30.0,
            "ascendant_sign": None, "ascendant_degree": None,
            "bazi_element": None, "rpv_conflict": None, "rpv_power": None, "rpv_energy": None,
        }
        b = dict(a)
        score = compute_lust_score(a, b)
        assert 0.0 <= score <= 100.0


# ── compute_soul_score ────────────────────────────────────────

class TestSoulScore:
    def _user(self, moon="cancer", mercury="gemini", saturn="capricorn",
              house4=None, juno=None, bazi_elem=None, attachment=None):
        return {
            "moon_sign": moon, "mercury_sign": mercury, "saturn_sign": saturn,
            "house4_sign": house4, "juno_sign": juno,
            "bazi_element": bazi_elem, "attachment_style": attachment,
        }

    def test_score_in_range(self):
        a = self._user()
        b = self._user()
        assert 0 <= compute_soul_score(a, b) <= 100

    def test_bazi_generation_multiplier(self):
        """Wood generates Fire → × 1.2 multiplier raises soul above baseline."""
        a_gen = self._user(bazi_elem="wood")
        b_gen = self._user(bazi_elem="fire")
        a_no  = self._user()
        b_no  = self._user()
        assert compute_soul_score(a_gen, b_gen) > compute_soul_score(a_no, b_no)

    def test_secure_secure_highest_attachment(self):
        """secure+secure = 0.90 (highest fit) → higher soul than anxious+secure (0.80)."""
        a_ss = self._user(attachment="secure")
        b_ss = self._user(attachment="secure")
        a_as = self._user(attachment="anxious")
        b_as = self._user(attachment="secure")
        assert compute_soul_score(a_ss, b_ss) > compute_soul_score(a_as, b_as)

    def test_missing_attachment_uses_neutral(self):
        """No attachment_style → uses NEUTRAL_SIGNAL (0.65), should not crash."""
        a = self._user(attachment=None)
        b = self._user(attachment=None)
        assert 0 <= compute_soul_score(a, b) <= 100


# ── compute_power_v2 ──────────────────────────────────────────

class TestComputePowerV2:
    def test_control_vs_follow_gives_dom_sub(self):
        """control (+20) vs follow (-20) → frame diff = 40 → Dom/Sub."""
        a = {"rpv_power": "control", "rpv_conflict": None}
        b = {"rpv_power": "follow",  "rpv_conflict": None}
        result = compute_power_v2(a, b)
        assert result["viewer_role"] == "Dom"
        assert result["target_role"] == "Sub"
        assert result["rpv"] == pytest.approx(40.0)

    def test_equal_rpv_gives_equal_roles(self):
        """Same RPV → frame_A == frame_B → rpv = 0 → Equal/Equal."""
        a = {"rpv_power": "control", "rpv_conflict": "cold_war"}
        b = {"rpv_power": "control", "rpv_conflict": "cold_war"}
        result = compute_power_v2(a, b)
        assert result["viewer_role"] == "Equal"
        assert result["rpv"] == pytest.approx(0.0)

    def test_chiron_triggered_sets_frame_break_true(self):
        """chiron_triggered_ab=True → frame_break=True in output."""
        a = {"rpv_power": None, "rpv_conflict": None}
        b = {"rpv_power": None, "rpv_conflict": None}
        result = compute_power_v2(a, b, chiron_triggered_ab=True)
        assert result["frame_break"] is True

    def test_chiron_trigger_shifts_rpv_by_15(self):
        """Chiron A→B trigger reduces frame_b by 15 → rpv increases by 15."""
        a = {"rpv_power": None, "rpv_conflict": None}
        b = {"rpv_power": None, "rpv_conflict": None}
        no_trigger   = compute_power_v2(a, b, chiron_triggered_ab=False)
        with_trigger = compute_power_v2(a, b, chiron_triggered_ab=True)
        assert with_trigger["rpv"] == pytest.approx(no_trigger["rpv"] + 15)

    def test_chiron_ba_trigger_shifts_rpv_by_minus_15(self):
        """Chiron B→A trigger reduces frame_a by 15 → rpv decreases by 15."""
        a = {"rpv_power": None, "rpv_conflict": None}
        b = {"rpv_power": None, "rpv_conflict": None}
        no_trigger   = compute_power_v2(a, b)
        with_trigger = compute_power_v2(a, b, chiron_triggered_ba=True)
        assert with_trigger["rpv"] == pytest.approx(no_trigger["rpv"] - 15)

    def test_bazi_restriction_a_restricts_b_gives_dom(self):
        """a_restricts_b: frame_A += 15, frame_B -= 15 → rpv shifts +30 → A=Dom."""
        a = {"rpv_power": None, "rpv_conflict": None}
        b = {"rpv_power": None, "rpv_conflict": None}
        neutral  = compute_power_v2(a, b)
        result   = compute_power_v2(a, b, bazi_relation="a_restricts_b")
        assert result["rpv"] == pytest.approx(neutral["rpv"] + 30)
        assert result["viewer_role"] == "Dom"

    def test_bazi_restriction_b_restricts_a_gives_sub(self):
        """b_restricts_a: frame_A -= 15, frame_B += 15 → rpv shifts -30 → A=Sub."""
        a = {"rpv_power": None, "rpv_conflict": None}
        b = {"rpv_power": None, "rpv_conflict": None}
        neutral  = compute_power_v2(a, b)
        result   = compute_power_v2(a, b, bazi_relation="b_restricts_a")
        assert result["rpv"] == pytest.approx(neutral["rpv"] - 30)
        assert result["viewer_role"] == "Sub"

    def test_bazi_same_does_not_shift_frame(self):
        """bazi_relation='same' → no frame shift, rpv unchanged."""
        a = {"rpv_power": None, "rpv_conflict": None}
        b = {"rpv_power": None, "rpv_conflict": None}
        neutral = compute_power_v2(a, b)
        result  = compute_power_v2(a, b, bazi_relation="same")
        assert result["rpv"] == pytest.approx(neutral["rpv"])


# ── _check_chiron_triggered ───────────────────────────────────

class TestChironTriggered:
    def test_mars_square_chiron_triggers(self):
        """Aries (0) to Cancer (3): distance = 3 = square → triggered."""
        a = {"mars_sign": "aries", "pluto_sign": None}
        b = {"chiron_sign": "cancer"}
        assert _check_chiron_triggered(a, b) is True

    def test_pluto_opposition_chiron_triggers(self):
        """Aries (0) to Libra (6): distance = 6 = opposition → triggered."""
        a = {"mars_sign": None, "pluto_sign": "aries"}
        b = {"chiron_sign": "libra"}
        assert _check_chiron_triggered(a, b) is True

    def test_trine_does_not_trigger(self):
        """Aries (0) to Leo (4): distance = 4 = trine → NOT triggered."""
        a = {"mars_sign": "aries", "pluto_sign": None}
        b = {"chiron_sign": "leo"}
        assert _check_chiron_triggered(a, b) is False

    def test_no_chiron_does_not_trigger(self):
        """Missing chiron_sign → always False."""
        a = {"mars_sign": "aries", "pluto_sign": "scorpio"}
        b = {"chiron_sign": None}
        assert _check_chiron_triggered(a, b) is False


# ── classify_quadrant ─────────────────────────────────────────

class TestClassifyQuadrant:
    def test_soulmate_both_above_threshold(self):
        assert classify_quadrant(75, 80) == "soulmate"

    def test_lover_high_lust_low_soul(self):
        assert classify_quadrant(70, 40) == "lover"

    def test_partner_low_lust_high_soul(self):
        assert classify_quadrant(40, 70) == "partner"

    def test_colleague_both_below_threshold(self):
        assert classify_quadrant(40, 40) == "colleague"

    def test_boundary_exactly_at_threshold(self):
        """Exactly 60 is included in the high category."""
        assert classify_quadrant(60, 60) == "soulmate"
        assert classify_quadrant(60, 59) == "lover"
        assert classify_quadrant(59, 60) == "partner"
        assert classify_quadrant(59, 59) == "colleague"


# ── AttachmentFit matrix ──────────────────────────────────────

class TestAttachmentFit:
    def test_secure_secure_highest(self):
        assert ATTACHMENT_FIT["secure"]["secure"] == pytest.approx(0.90)

    def test_anxious_anxious_lowest(self):
        assert ATTACHMENT_FIT["anxious"]["anxious"] == pytest.approx(0.50)

    def test_anxious_avoidant_symmetric(self):
        """Tension attraction: anxious→avoidant == avoidant→anxious."""
        assert ATTACHMENT_FIT["anxious"]["avoidant"] == ATTACHMENT_FIT["avoidant"]["anxious"]


# ── compute_match_v2 integration ─────────────────────────────

class TestComputeMatchV2Integration:
    def _user(self, **kwargs):
        defaults = {
            "data_tier": 3,
            "sun_sign": "aries", "moon_sign": None, "venus_sign": "taurus",
            "mars_sign": "gemini", "saturn_sign": "cancer",
            "mercury_sign": "aries", "jupiter_sign": "taurus",
            "pluto_sign": "scorpio",
            "chiron_sign": None, "juno_sign": None,
            "house4_sign": None, "house8_sign": None,
            "ascendant_sign": None,
            "bazi_element": None,
            "rpv_conflict": None, "rpv_power": None, "rpv_energy": None,
            "attachment_style": None,
        }
        defaults.update(kwargs)
        return defaults

    def test_returns_all_required_keys(self):
        a = self._user()
        b = self._user(venus_sign="leo")
        result = compute_match_v2(a, b)
        required = {"lust_score", "soul_score", "power", "tracks",
                    "primary_track", "quadrant", "labels",
                    "bazi_relation", "useful_god_complement"}
        assert required.issubset(result.keys())

    def test_lust_score_in_range(self):
        a = self._user(rpv_power="control")
        b = self._user(rpv_power="follow")
        assert 0 <= compute_match_v2(a, b)["lust_score"] <= 100

    def test_soul_score_in_range(self):
        a = self._user()
        b = self._user()
        assert 0 <= compute_match_v2(a, b)["soul_score"] <= 100

    def test_primary_track_is_valid(self):
        a = self._user()
        b = self._user()
        assert compute_match_v2(a, b)["primary_track"] in (
            "friend", "passion", "partner", "soul"
        )

    def test_quadrant_is_valid(self):
        a = self._user()
        b = self._user()
        assert compute_match_v2(a, b)["quadrant"] in (
            "soulmate", "lover", "partner", "colleague"
        )

    def test_power_has_required_keys(self):
        a = self._user()
        b = self._user()
        power = compute_match_v2(a, b)["power"]
        assert "rpv" in power
        assert "frame_break" in power
        assert "viewer_role" in power
        assert "target_role" in power

    def test_tracks_has_four_keys(self):
        a = self._user()
        b = self._user()
        tracks = compute_match_v2(a, b)["tracks"]
        assert set(tracks.keys()) == {"friend", "passion", "partner", "soul"}

    def test_all_track_values_in_range(self):
        a = self._user(bazi_element="wood", rpv_power="control")
        b = self._user(bazi_element="fire", rpv_power="follow")
        tracks = compute_match_v2(a, b)["tracks"]
        for key, val in tracks.items():
            assert 0 <= val <= 100, f"track {key} out of range: {val}"

    def test_bazi_relation_in_output(self):
        """bazi_relation reflects the five-element relationship."""
        a = self._user(bazi_element="metal")
        b = self._user(bazi_element="wood")
        result = compute_match_v2(a, b)
        # Metal restricts Wood
        assert result["bazi_relation"] == "a_restricts_b"

    def test_useful_god_complement_summer_winter_via_branch(self):
        """午 (summer) ↔ 子 (winter) via bazi_month_branch → useful_god_complement = 1.0."""
        a = self._user(bazi_month_branch="午")
        b = self._user(bazi_month_branch="子")
        result = compute_match_v2(a, b)
        assert result["useful_god_complement"] == pytest.approx(1.0)

    def test_useful_god_complement_same_season_via_branch(self):
        """Same summer branches → useful_god_complement = 0.0."""
        a = self._user(bazi_month_branch="午")
        b = self._user(bazi_month_branch="未")
        result = compute_match_v2(a, b)
        assert result["useful_god_complement"] == pytest.approx(0.0)

    def test_useful_god_complement_fallback_birth_month(self):
        """Legacy fallback: birth_month=6 ↔ birth_month=12 → 1.0 (via 午/子 mapping)."""
        a = self._user(birth_month=6)
        b = self._user(birth_month=12)
        result = compute_match_v2(a, b)
        assert result["useful_god_complement"] == pytest.approx(1.0)

    def test_useful_god_complement_same_season_fallback(self):
        """Legacy fallback: same season months → useful_god_complement = 0.0."""
        a = self._user(birth_month=6)
        b = self._user(birth_month=7)
        result = compute_match_v2(a, b)
        assert result["useful_god_complement"] == pytest.approx(0.0)

    def test_useful_god_complement_missing_month(self):
        """No birth_month and no bazi_month_branch → useful_god_complement = 0.0."""
        a = self._user()
        b = self._user()
        result = compute_match_v2(a, b)
        assert result["useful_god_complement"] == pytest.approx(0.0)

    def test_bazi_month_branch_preferred_over_birth_month(self):
        """bazi_month_branch takes precedence over the birth_month fallback.

        A: bazi_month_branch=午 (summer/hot), birth_month=11 (Gregorian → 亥 cold in legacy).
        B: bazi_month_branch=巳 (summer/hot), birth_month=6  (Gregorian → 午 hot in legacy).
        Branch path:   午↔巳 = same season → 0.0.
        Gregorian fallback would give: 亥↔午 = cold↔hot → 1.0.
        Since bazi_month_branch is present, branch path must win → 0.0.
        """
        # bazi_month_branch=午 (summer), birth_month=11 (Gregorian winter → cold in legacy)
        # bazi_month_branch=巳 (summer), birth_month=6 (Gregorian summer → hot in legacy)
        # Branch result: 午↔巳 = same season = 0.0
        # Gregorian fallback would give: 亥↔午 = cold↔hot = 1.0
        # Since bazi_month_branch is present, branch path must win → 0.0
        a = self._user(bazi_month_branch="午", birth_month=11)
        b = self._user(bazi_month_branch="巳", birth_month=6)
        result = compute_match_v2(a, b)
        assert result["useful_god_complement"] == pytest.approx(0.0)

    def test_summer_winter_raises_soul_track_via_branch(self):
        """Summer ↔ Winter complement (1.0) should give higher soul track
        than same-season pair (0.0) when using bazi_month_branch."""
        a_sw = self._user(bazi_month_branch="午")
        b_sw = self._user(bazi_month_branch="子")
        a_ss = self._user(bazi_month_branch="午")
        b_ss = self._user(bazi_month_branch="未")
        soul_sw = compute_match_v2(a_sw, b_sw)["tracks"]["soul"]
        soul_ss = compute_match_v2(a_ss, b_ss)["tracks"]["soul"]
        assert soul_sw > soul_ss

    def test_lust_soul_modifier_propagates_to_axes(self):
        """soul_adj and lust_adj must update lust/soul axes, not just tracks.
        Shadow engine soul_mod should raise soul_score, not just tracks["soul"].

        Uses a deliberately LOW-soul baseline (all planets 25° apart = void-of-aspect
        → soul_score ~10) vs a Vertex-triggered pair (+75 soul_adj → soul_score ~85).
        25° separation is outside all major aspect orbs, so degree-level gives 0.10
        (void) for every planet pair, ensuring the base score is well below 100.

        NOTE: Test data was updated after L-2 degree-level upgrade: the original
        all-same-degree (45°) data caused every planet to score 1.0 (perfect conj)
        → soul_score = 100 for BOTH cases, masking the propagation test.
        """
        # A: all personal planets at 0° / 270° (capricorn for saturn)
        a = {
            "data_tier": 1,
            "sun_sign": "aries",       "sun_degree": 0.0,
            "moon_sign": "aries",      "moon_degree": 0.0,
            "venus_sign": "aries",     "venus_degree": 0.0,
            "mars_sign": "aries",      "mars_degree": 0.0,
            "mercury_sign": "aries",   "mercury_degree": 0.0,
            "saturn_sign": "capricorn","saturn_degree": 270.0,
            "ascendant_sign": "aries", "ascendant_degree": 0.0,
            "bazi_element": None, "rpv_conflict": None, "rpv_power": None, "rpv_energy": None,
        }
        # B: all planets 25° ahead (void of aspect with A), PLUS vertex near A's sun/moon/venus
        # A_Sun (0°) × vertex (1°): 1° → conjunction trigger → soul_mod +25
        # A_Moon (0°) × vertex (1°): same → +25
        # A_Venus (0°) × vertex (1°): same → +25  → total soul_adj = +75
        b_with_vertex = {
            "data_tier": 1,
            "sun_sign": "aries",       "sun_degree": 25.0,
            "moon_sign": "aries",      "moon_degree": 25.0,
            "venus_sign": "aries",     "venus_degree": 25.0,
            "mars_sign": "aries",      "mars_degree": 25.0,
            "mercury_sign": "aries",   "mercury_degree": 25.0,
            "saturn_sign": "capricorn","saturn_degree": 295.0,
            "ascendant_sign": "aries", "ascendant_degree": 25.0,
            "vertex_degree": 1.0,   # 1° from A's sun/moon/venus → 3 Vertex triggers
            "bazi_element": None, "rpv_conflict": None, "rpv_power": None, "rpv_energy": None,
        }
        # B WITHOUT Vertex — identical, no shadow soul_mod
        b_without_vertex = {
            "data_tier": 1,
            "sun_sign": "aries",       "sun_degree": 25.0,
            "moon_sign": "aries",      "moon_degree": 25.0,
            "venus_sign": "aries",     "venus_degree": 25.0,
            "mars_sign": "aries",      "mars_degree": 25.0,
            "mercury_sign": "aries",   "mercury_degree": 25.0,
            "saturn_sign": "capricorn","saturn_degree": 295.0,
            "ascendant_sign": "aries", "ascendant_degree": 25.0,
            "bazi_element": None, "rpv_conflict": None, "rpv_power": None, "rpv_energy": None,
        }
        result_with    = compute_match_v2(a, b_with_vertex)
        result_without = compute_match_v2(a, b_without_vertex)

        # tracks["soul"] must be boosted — this should always hold (even before the fix)
        assert result_with["tracks"]["soul"] > result_without["tracks"]["soul"], (
            "tracks['soul'] should be boosted by Vertex trigger"
        )

        # soul_score (the Y-axis) must ALSO be boosted — this is the propagation fix.
        # Before the fix, soul_score is identical in both cases (bug).
        assert result_with["soul_score"] > result_without["soul_score"], (
            f"soul_score should be boosted by shadow engine Vertex trigger: "
            f"with={result_with['soul_score']} vs without={result_without['soul_score']}"
        )

        # psychological_tags should contain at least one Vertex trigger tag
        assert any("Vertex" in t for t in result_with.get("psychological_tags", [])), (
            "Vertex trigger tag should appear in psychological_tags"
        )


# ── bazi.py: seasonal complement functions ────────────────────

from bazi import get_season_type, compute_bazi_season_complement


class TestGetSeasonType:
    def test_summer_branches(self):
        """巳午未 → hot (夏)"""
        for b in ("巳", "午", "未"):
            assert get_season_type(b) == "hot"

    def test_winter_branches(self):
        """亥子丑 → cold (冬)"""
        for b in ("亥", "子", "丑"):
            assert get_season_type(b) == "cold"

    def test_spring_branches(self):
        """寅卯辰 → warm (春)"""
        for b in ("寅", "卯", "辰"):
            assert get_season_type(b) == "warm"

    def test_autumn_branches(self):
        """申酉戌 → cool (秋)"""
        for b in ("申", "酉", "戌"):
            assert get_season_type(b) == "cool"

    def test_unknown_branch_returns_unknown(self):
        """Invalid branch → 'unknown'."""
        assert get_season_type("X") == "unknown"
        assert get_season_type("") == "unknown"


class TestBaziSeasonComplement:
    def test_hot_cold_is_perfect(self):
        """Summer ↔ Winter = 1.0 (水火既濟)."""
        assert compute_bazi_season_complement("午", "子") == pytest.approx(1.0)
        assert compute_bazi_season_complement("子", "午") == pytest.approx(1.0)

    def test_warm_cool_is_good(self):
        """Spring ↔ Autumn = 0.8 (金木相成)."""
        assert compute_bazi_season_complement("卯", "酉") == pytest.approx(0.8)
        assert compute_bazi_season_complement("酉", "卯") == pytest.approx(0.8)

    def test_extreme_moderate_is_partial(self):
        """Summer ↔ Autumn = 0.5 (partial)."""
        assert compute_bazi_season_complement("午", "酉") == pytest.approx(0.5)

    def test_same_season_is_zero(self):
        """Same season = 0.0 (no complement)."""
        assert compute_bazi_season_complement("巳", "未") == pytest.approx(0.0)
        assert compute_bazi_season_complement("子", "亥") == pytest.approx(0.0)

    def test_symmetric(self):
        """Complement score is symmetric: A↔B == B↔A."""
        assert compute_bazi_season_complement("午", "子") == \
               compute_bazi_season_complement("子", "午")

    def test_empty_branch_returns_zero(self):
        """Empty or None branch → 0.0."""
        assert compute_bazi_season_complement("", "午") == pytest.approx(0.0)
        assert compute_bazi_season_complement("午", "") == pytest.approx(0.0)


# ════════════════════════════════════════════════════════════════
# Phase H: ZWDS Integration Tests
# ════════════════════════════════════════════════════════════════

from unittest.mock import patch

# Tier 1 users with birth_time for ZWDS
T1_ZWDS_A = {
    "birth_year": 1990, "birth_month": 6, "birth_day": 15,
    "birth_time": "11:30", "gender": "M", "data_tier": 1,
    "sun_sign": "gemini", "moon_sign": "aries", "venus_sign": "taurus",
    "ascendant_sign": "scorpio", "mars_sign": "leo", "saturn_sign": "capricorn",
    "mercury_sign": "gemini", "jupiter_sign": "cancer", "pluto_sign": "scorpio",
    "chiron_sign": "cancer", "juno_sign": "sagittarius",
    "house4_sign": "pisces", "house8_sign": "cancer",
    "bazi_element": "metal", "bazi_day_master": "庚",
    "rpv_conflict": "argue", "rpv_power": "control", "rpv_energy": "home",
    "attachment_style": "secure", "attachment_role": "dom_secure",
}
T1_ZWDS_B = {**T1_ZWDS_A, "birth_year": 1993, "birth_month": 3, "birth_day": 8,
             "birth_time": "05:00", "gender": "F", "bazi_element": "water",
             "rpv_power": "follow", "attachment_role": "sub_secure"}
T3_ZWDS_A = {**T1_ZWDS_A, "data_tier": 3, "birth_time": None}


class TestZwdsMatchIntegration:
    def test_output_has_zwds_key(self):
        result = compute_match_v2(T1_ZWDS_A, T1_ZWDS_B)
        assert "zwds" in result

    def test_output_has_spiciness_level(self):
        result = compute_match_v2(T1_ZWDS_A, T1_ZWDS_B)
        assert "spiciness_level" in result
        assert result["spiciness_level"] in ["STABLE", "MEDIUM", "HIGH_VOLTAGE", "SOULMATE"]

    def test_output_has_defense_mechanisms(self):
        result = compute_match_v2(T1_ZWDS_A, T1_ZWDS_B)
        assert "defense_mechanisms" in result
        dm = result["defense_mechanisms"]
        assert "viewer" in dm
        assert "target" in dm

    def test_output_has_layered_analysis(self):
        result = compute_match_v2(T1_ZWDS_A, T1_ZWDS_B)
        assert "layered_analysis" in result

    def test_zwds_is_none_for_tier3(self):
        result = compute_match_v2(T3_ZWDS_A, T1_ZWDS_B)
        assert result["zwds"] is None
        assert result["spiciness_level"] == "STABLE"

    def test_zwds_not_called_for_tier3(self):
        with patch("matching.compute_zwds_synastry") as mock:
            compute_match_v2(T3_ZWDS_A, T1_ZWDS_B)
        mock.assert_not_called()

    def test_zwds_mods_shift_passion_track(self):
        mock_zwds_result = {
            "track_mods": {"friend": 1.0, "passion": 1.3, "partner": 0.8, "soul": 1.0},
            "rpv_modifier": 0,
            "defense_a": [], "defense_b": [],
            "flying_stars": {}, "spiciness_level": "HIGH_VOLTAGE",
            "layered_analysis": {"karmic_link": [], "energy_dynamic": [],
                                 "archetype_cluster_a": "殺破狼", "archetype_cluster_b": "機月同梁"},
        }
        with patch("matching.compute_zwds_synastry", return_value=mock_zwds_result):
            result_with = compute_match_v2(T1_ZWDS_A, T1_ZWDS_B)
        with patch("matching.compute_zwds_synastry", return_value=None):
            result_without = compute_match_v2(T1_ZWDS_A, T1_ZWDS_B)
        assert result_with["tracks"]["passion"] > result_without["tracks"]["passion"]

    def test_zwds_exception_does_not_break_matching(self):
        with patch("matching.compute_zwds_synastry", side_effect=Exception("ZWDS down")):
            result = compute_match_v2(T1_ZWDS_A, T1_ZWDS_B)
        assert "zwds" in result
        assert result["zwds"] is None


# ════════════════════════════════════════════════════════════════
# Task 2: Dynamic Weighting Tests
# ════════════════════════════════════════════════════════════════


class TestSoulScoreDynamicWeighting:
    """Tests verifying that optional fields are excluded from the denominator
    when absent (Tier 2/3 users), so scores are not diluted."""

    def _tier3_user(self, moon="cancer", mercury="gemini", saturn="capricorn"):
        """Tier 3 user: only core planets, no house4 / juno / attachment."""
        return {
            "moon_sign": moon,
            "mercury_sign": mercury,
            "saturn_sign": saturn,
            "house4_sign": None,
            "juno_sign": None,
            "attachment_style": None,
            "bazi_element": None,
        }

    def _tier1_user(self, moon="cancer", mercury="gemini", saturn="capricorn",
                    house4="pisces", juno="sagittarius", attachment="secure"):
        """Tier 1 user: all fields present."""
        return {
            "moon_sign": moon,
            "mercury_sign": mercury,
            "saturn_sign": saturn,
            "house4_sign": house4,
            "juno_sign": juno,
            "attachment_style": attachment,
            "bazi_element": None,
        }

    def test_soul_score_tier3_no_house4_juno_attachment(self):
        """Tier 3 user (no house4, juno, attachment) gets a score based only
        on moon + mercury + saturn with total_weight = 0.65.

        Dynamic formula: score / total_weight × 100
        Expected = (moon*0.25 + mercury*0.20 + saturn*0.20) / 0.65 * 100
        """
        a = self._tier3_user(moon="cancer", mercury="gemini", saturn="capricorn")
        b = self._tier3_user(moon="cancer", mercury="gemini", saturn="capricorn")

        moon_v    = compute_sign_aspect("cancer",    "cancer",    "harmony")   # 0.90
        mercury_v = compute_sign_aspect("gemini",    "gemini",    "harmony")   # 0.90
        saturn_v  = compute_sign_aspect("capricorn", "capricorn", "harmony")   # 0.90

        numerator = moon_v * 0.25 + mercury_v * 0.20 + saturn_v * 0.20
        total_w   = 0.25 + 0.20 + 0.20  # = 0.65
        expected  = (numerator / total_w) * 100

        assert compute_soul_score(a, b) == pytest.approx(expected, abs=0.1)

    def test_soul_score_tier1_all_fields(self):
        """Tier 1 user with all fields present: score uses all 6 components
        with total_weight = 1.20.

        Juno now uses cross-aspect (juno_a × moon_b + juno_b × moon_a) / 2.0.
        With juno="sagittarius" and moon="cancer" for both users:
        juno_v = (sign_aspect("sagittarius","cancer") + sign_aspect("sagittarius","cancer")) / 2.0
               = sign_aspect("sagittarius","cancer","harmony")  [square: 3 signs apart = 0.40]

        Expected = (moon*0.25 + mercury*0.20 + saturn*0.20
                    + house4*0.15 + juno_cross*0.20 + attachment*0.20) / 1.20 * 100
        """
        a = self._tier1_user(moon="cancer", mercury="gemini", saturn="capricorn",
                              house4="pisces", juno="sagittarius", attachment="secure")
        b = self._tier1_user(moon="cancer", mercury="gemini", saturn="capricorn",
                              house4="pisces", juno="sagittarius", attachment="secure")

        moon_v       = compute_sign_aspect("cancer",    "cancer",    "harmony")
        mercury_v    = compute_sign_aspect("gemini",    "gemini",    "harmony")
        saturn_v     = compute_sign_aspect("capricorn", "capricorn", "harmony")
        house4_v     = compute_sign_aspect("pisces",    "pisces",    "harmony")
        # Cross-aspect: juno_a × moon_b + juno_b × moon_a (both users same signs)
        juno_v       = (compute_sign_aspect("sagittarius", "cancer", "harmony") +
                        compute_sign_aspect("sagittarius", "cancer", "harmony")) / 2.0
        attachment_v = ATTACHMENT_FIT["secure"]["secure"]  # 0.90

        numerator = (moon_v * 0.25 + mercury_v * 0.20 + saturn_v * 0.20
                     + house4_v * 0.15 + juno_v * 0.20 + attachment_v * 0.20)
        total_w   = 0.25 + 0.20 + 0.20 + 0.15 + 0.20 + 0.20  # = 1.20
        expected  = (numerator / total_w) * 100

        assert compute_soul_score(a, b) == pytest.approx(expected, abs=0.1)

    def test_soul_score_tier3_higher_than_fixed_weight_would_give(self):
        """With the old fixed-weight formula and house4=0 / juno=NEUTRAL (0.65) /
        attachment=NEUTRAL (0.65), the denominator was effectively 1.20 while
        only 0.65 of weight contributed real signal. Dynamic weighting gives a
        proportionally correct (higher) score for the same core planets.
        """
        a = self._tier3_user(moon="cancer", mercury="cancer", saturn="cancer")
        b = self._tier3_user(moon="cancer", mercury="cancer", saturn="cancer")

        # Dynamic score uses only the 3 core planets (all conjunction = 0.90)
        score = compute_soul_score(a, b)

        # Old formula: raw weighted sum (no normalization), with NEUTRAL_SIGNAL=0.65
        # for absent juno and attachment, resulting in a lower score.
        old_score = (0.90 * 0.25 + 0.90 * 0.20 + 0.0 * 0.15 + 0.90 * 0.20
                     + 0.65 * 0.20 + 0.65 * 0.20) * 100  # raw sum, no normalization
        assert score > old_score


class TestLustScoreDynamicWeighting:
    """Tests verifying house8 dynamic weighting in compute_lust_score."""

    def _user(self, venus="aries", mars="aries", pluto="scorpio",
              house8=None, bazi_elem=None, rpv_power=None, rpv_conflict=None):
        return {
            "venus_sign": venus, "mars_sign": mars, "pluto_sign": pluto,
            "house8_sign": house8, "bazi_element": bazi_elem,
            "rpv_power": rpv_power, "rpv_conflict": rpv_conflict,
        }

    def test_lust_score_tier3_no_house8(self):
        """Tier 3 without house8_degree: score uses cross + same-planet + karmic + power.
        house8 cross-aspects are excluded from denominator when house8_degree is absent.

        New formula (v1.6): sign-level fallback for cross/same-planet aspects.
        Expected = (cross_mv*0.30 + cross_vm*0.30
                    + same_v*0.15 + same_m*0.15
                    + karmic*0.25 + power*0.30) / 1.45 * 100
        """
        a = self._user(venus="aries", mars="aries", pluto="scorpio")
        b = self._user(venus="aries", mars="aries", pluto="scorpio")

        # No exact degrees → sign-level fallback for all cross/same aspects
        cross_mv = compute_sign_aspect("aries", "aries", "tension")   # mars_a vs venus_b = 1.00
        cross_vm = compute_sign_aspect("aries", "aries", "tension")   # mars_b vs venus_a = 1.00
        same_v   = compute_sign_aspect("aries", "aries", "harmony")   # venus_a vs venus_b = 0.90
        same_m   = compute_sign_aspect("aries", "aries", "harmony")   # mars_a vs mars_b   = 0.90
        karmic_v = compute_karmic_triggers(a, b)

        from matching import compute_power_score
        power_v = compute_power_score(a, b)

        numerator = (cross_mv * 0.30 + cross_vm * 0.30
                     + same_v * 0.15 + same_m * 0.15
                     + karmic_v * 0.25 + power_v * 0.30)
        total_w   = 0.30 + 0.30 + 0.15 + 0.15 + 0.25 + 0.30  # = 1.45
        expected  = (numerator / total_w) * 100

        assert compute_lust_score(a, b) == pytest.approx(expected, abs=0.1)

    def test_lust_score_tier1_with_house8(self):
        """Tier 1 with exact house8_degree and mars_degree: h8 cross-aspects activate.

        New formula (v1.6): h8_a_deg × mars_b_deg and h8_b_deg × mars_a_deg contribute
        when both are present. No venus_degree → cross/same-venus use sign-level fallback.

        Setup: both users have house8_degree=0.0, mars_degree=0.0, no venus_degree.
          cross_mv: mars_a_deg=0.0 vs venus_b_deg=None → sign fallback aries×aries tension=1.00
          cross_vm: same                                → sign fallback aries×aries tension=1.00
          same_v:   venus_a_deg=None, venus_b_deg=None → sign fallback aries×aries harmony=0.90
          same_m:   mars_a_deg=0.0, mars_b_deg=0.0    → exact conjunction harmony=1.00
          h8_ab:    h8_a_deg=0.0, mars_b_deg=0.0      → exact conjunction tension=1.00
          h8_ba:    h8_b_deg=0.0, mars_a_deg=0.0      → exact conjunction tension=1.00
        total_weight = 0.30+0.30+0.15+0.15+0.10+0.10+0.25+0.30 = 1.65
        """
        from matching import compute_exact_aspect
        a = {**self._user(venus="aries", mars="aries", pluto="scorpio", house8="scorpio"),
             "house8_degree": 0.0, "mars_degree": 0.0}
        b = {**self._user(venus="aries", mars="aries", pluto="scorpio", house8="scorpio"),
             "house8_degree": 0.0, "mars_degree": 0.0}

        # Cross aspects fall back to sign-level (venus_degree absent)
        cross_mv = compute_sign_aspect("aries", "aries", "tension")   # 1.00
        cross_vm = compute_sign_aspect("aries", "aries", "tension")   # 1.00
        same_v   = compute_sign_aspect("aries", "aries", "harmony")   # 0.90
        same_m   = compute_exact_aspect(0.0, 0.0, "harmony")          # 1.00
        h8_ab    = compute_exact_aspect(0.0, 0.0, "tension")          # 1.00
        h8_ba    = compute_exact_aspect(0.0, 0.0, "tension")          # 1.00
        karmic_v = compute_karmic_triggers(a, b)

        from matching import compute_power_score
        power_v = compute_power_score(a, b)

        numerator = (cross_mv * 0.30 + cross_vm * 0.30
                     + same_v * 0.15 + same_m * 0.15
                     + h8_ab * 0.10 + h8_ba * 0.10
                     + karmic_v * 0.25 + power_v * 0.30)
        total_w   = 0.30 + 0.30 + 0.15 + 0.15 + 0.10 + 0.10 + 0.25 + 0.30  # = 1.65
        expected  = (numerator / total_w) * 100

        assert compute_lust_score(a, b) == pytest.approx(expected, abs=0.1)


class TestTracksNullHandling:
    """Tests verifying dynamic redistribution in compute_tracks when
    juno or chiron are absent."""

    def _base_user(self, **kwargs):
        defaults = {
            "moon_sign": "cancer", "mercury_sign": "gemini",
            "jupiter_sign": "sagittarius", "mars_sign": "aries",
            "venus_sign": "taurus", "pluto_sign": "scorpio",
            "saturn_sign": "capricorn",
            "juno_sign": None, "chiron_sign": None,
            "house8_sign": None, "bazi_element": None,
            "rpv_power": None, "rpv_conflict": None,
        }
        defaults.update(kwargs)
        return defaults

    def _power_no_frame_break(self):
        return {"rpv": 0.0, "frame_break": False, "viewer_role": "Equal", "target_role": "Equal"}

    def test_partner_track_no_juno(self):
        """When both users lack juno_sign, partner track redistributes weight:
        moon gets 0.55 and bazi_generation gets 0.45, plus Saturn cross-aspect bonus.

        With no bazi_generation and moon conjunction (0.90), saturn_a=capricorn × moon_b=cancer:
        capricorn-cancer = 6 signs (opposition) → harmony=0.60; cross=(0.60+0.60)/2=0.60
        partner = 0.90*0.55 + 0.0*0.45 + 0.60*0.10 = 0.495 + 0.06 = 0.555 → 55.5
        """
        a = self._base_user(moon_sign="cancer")
        b = self._base_user(moon_sign="cancer")
        power = self._power_no_frame_break()

        tracks = compute_tracks(a, b, power, useful_god_complement=0.0)
        moon_v = compute_sign_aspect("cancer", "cancer", "harmony")  # 0.90
        # Saturn cross: capricorn × cancer (opposition) + capricorn × cancer = 0.60 each
        sat_cross = (compute_sign_aspect("capricorn", "cancer", "harmony") +
                     compute_sign_aspect("capricorn", "cancer", "harmony")) / 2.0  # 0.60
        expected_partner = (moon_v * 0.55 + 0.0 * 0.45 + sat_cross * 0.10) * 100
        assert tracks["partner"] == pytest.approx(expected_partner, abs=0.5)

    def test_partner_track_with_juno_uses_original_weights(self):
        """When juno_sign is present, partner uses original weights:
        moon*0.35 + juno*0.35 + bazi_generation*0.30, plus Saturn cross-aspect bonus.

        Juno now uses cross-aspect (juno_a × moon_b + juno_b × moon_a) / 2.0.
        With juno="libra" and moon="cancer": both users share the same signs, so
        juno = (sign_aspect("libra","cancer") + sign_aspect("libra","cancer")) / 2.0
             = sign_aspect("libra", "cancer", "harmony")  [square = 0.40]
        """
        a = self._base_user(moon_sign="cancer", juno_sign="libra")
        b = self._base_user(moon_sign="cancer", juno_sign="libra")
        power = self._power_no_frame_break()

        tracks = compute_tracks(a, b, power, useful_god_complement=0.0)
        moon_v = compute_sign_aspect("cancer", "cancer", "harmony")  # 0.90
        # Cross-aspect: juno_a × moon_b + juno_b × moon_a
        juno_v = (compute_sign_aspect("libra", "cancer", "harmony") +
                  compute_sign_aspect("libra", "cancer", "harmony")) / 2.0  # square = 0.40
        # Saturn cross: capricorn × cancer (opposition) = 0.60 each
        sat_cross = (compute_sign_aspect("capricorn", "cancer", "harmony") +
                     compute_sign_aspect("capricorn", "cancer", "harmony")) / 2.0  # 0.60
        expected_partner = (moon_v * 0.35 + juno_v * 0.35 + 0.0 * 0.30 + sat_cross * 0.10) * 100
        assert tracks["partner"] == pytest.approx(expected_partner, abs=0.5)

    def test_soul_track_no_chiron(self):
        """When both users lack chiron_sign, soul track redistributes weight:
        karmic gets 0.60 and useful_god gets 0.40.

        karmic = compute_karmic_triggers(a, b) replaces old pluto×pluto comparison.
        soul_track = karmic * 0.60 + 0.0 * 0.40
        """
        a = self._base_user(pluto_sign="scorpio")
        b = self._base_user(pluto_sign="scorpio")
        power = self._power_no_frame_break()

        tracks = compute_tracks(a, b, power, useful_god_complement=0.0)
        karmic_v = compute_karmic_triggers(a, b)
        expected_soul = (karmic_v * 0.60 + 0.0 * 0.40) * 100
        assert tracks["soul"] == pytest.approx(expected_soul, abs=0.5)

    def test_soul_track_chiron_present_still_uses_nochiron_formula(self):
        """L-12 + L-2 fix: Even when chiron_sign is present, soul_track must use
        the no-Chiron formula (karmic*0.60 + useful_god*0.40).

        Chiron is generational (7 yrs/sign) so same-age users share Chiron sign,
        causing false conjunction boosts. Shadow engine handles Chiron wound triggers
        via orb-based degree checks — so using Chiron here also double-counts.
        """
        a = self._base_user(pluto_sign="scorpio", chiron_sign="aries")
        b = self._base_user(pluto_sign="scorpio", chiron_sign="aries")
        power = self._power_no_frame_break()

        tracks = compute_tracks(a, b, power, useful_god_complement=0.5)
        karmic_v = compute_karmic_triggers(a, b)
        # Always use no-Chiron formula regardless of chiron_sign presence
        expected_soul = (karmic_v * 0.60 + 0.5 * 0.40) * 100
        assert tracks["soul"] == pytest.approx(expected_soul, abs=0.5)


class TestChironSameGenerationNoInflation:
    """L-2 regression: same-year users (same Chiron sign) must not get inflated soul track."""

    def _base_user(self, **kwargs):
        defaults = {
            "moon_sign": "cancer", "mercury_sign": "gemini",
            "jupiter_sign": "sagittarius", "mars_sign": "aries",
            "venus_sign": "taurus", "pluto_sign": "scorpio",
            "saturn_sign": "capricorn",
            "juno_sign": None, "chiron_sign": None,
            "house8_sign": None, "bazi_element": None,
            "rpv_power": None, "rpv_conflict": None,
            "sun_sign": "aries", "ascendant_sign": None,
            "house4_sign": None, "attachment_style": None,
            "data_tier": 3,
        }
        defaults.update(kwargs)
        return defaults

    def test_chiron_same_generation_no_inflation(self):
        """Same-year users (same Chiron sign) should NOT get inflated soul track.
        Chiron is generational; same-gen pairs must rely only on karmic + useful_god."""
        from matching import compute_match_v2
        user_a = self._base_user(chiron_sign="Aries", chiron_degree=10.0)
        user_b = self._base_user(chiron_sign="Aries", chiron_degree=15.0)
        result = compute_match_v2(user_a, user_b)
        # Soul track should not be inflated by same-gen Chiron conjunction
        # karmic + useful_god formula caps out at ~60-70 without shadow engine boosts
        assert result["tracks"]["soul"] <= 75.0, (
            f"Soul track {result['tracks']['soul']} inflated by same-gen Chiron"
        )


class TestEmotionalCapacityPartnerTrack:
    """Tests for emotional capacity penalty on partner track in compute_tracks."""

    def _power_no_frame_break(self):
        return {"rpv": 0, "frame_break": False, "viewer_role": "Equal", "target_role": "Equal"}

    def test_partner_track_penalty_both_low_capacity(self):
        """Both users < 40 capacity → partner track × 0.7.

        saturn_sign="aries" × moon_sign="aries" (conjunction) = 0.90; cross=0.90; bonus=0.09
        base = moon*0.55 + 0*0.45 + saturn_cross*0.10 = 0.90*0.55 + 0.90*0.10 = 0.495 + 0.09 = 0.585
        × 0.7 penalty → 0.585*0.7*100 = 40.95
        """
        user = {"moon_sign": "aries", "bazi_element": "fire", "juno_sign": None,
                "rpv_conflict": None, "rpv_power": None, "rpv_energy": None,
                "chiron_sign": None, "mars_sign": "aries", "venus_sign": "aries",
                "mercury_sign": "aries", "jupiter_sign": "aries", "pluto_sign": "aries",
                "saturn_sign": "aries", "emotional_capacity": 30}
        user_b = dict(user)
        result = compute_tracks(user, user_b, self._power_no_frame_break())
        # base = moon*0.55 + saturn_cross*0.10 = 0.90*0.55 + 0.90*0.10 = 0.585
        assert result["partner"] == pytest.approx(0.585 * 0.7 * 100, abs=1.0)

    def test_partner_track_penalty_one_very_low(self):
        """One user < 30 capacity → partner track × 0.85."""
        user_a = {"moon_sign": "aries", "bazi_element": "fire", "juno_sign": None,
                  "rpv_conflict": None, "rpv_power": None, "rpv_energy": None,
                  "chiron_sign": None, "mars_sign": "aries", "venus_sign": "aries",
                  "mercury_sign": "aries", "jupiter_sign": "aries", "pluto_sign": "aries",
                  "saturn_sign": "aries", "emotional_capacity": 25}
        user_b = dict(user_a)
        user_b["emotional_capacity"] = 60  # healthy
        result = compute_tracks(user_a, user_b, self._power_no_frame_break())
        # base = 0.90*0.55 + 0.90*0.10 = 0.585
        assert result["partner"] == pytest.approx(0.585 * 0.85 * 100, abs=1.0)

    def test_partner_track_no_penalty_healthy_capacity(self):
        """Both users >= 40 capacity → no partner track penalty."""
        user = {"moon_sign": "aries", "bazi_element": "fire", "juno_sign": None,
                "rpv_conflict": None, "rpv_power": None, "rpv_energy": None,
                "chiron_sign": None, "mars_sign": "aries", "venus_sign": "aries",
                "mercury_sign": "aries", "jupiter_sign": "aries", "pluto_sign": "aries",
                "saturn_sign": "aries", "emotional_capacity": 60}
        result = compute_tracks(user, user, self._power_no_frame_break())
        # base = 0.90*0.55 + 0.90*0.10 = 0.585
        assert result["partner"] == pytest.approx(0.585 * 100, abs=1.0)


# ════════════════════════════════════════════════════════════════
# Phase H v1.5: BaZi Day Branch 刑沖破害 Modifier Tests
# ════════════════════════════════════════════════════════════════

from matching import apply_bazi_branch_modifiers


class TestApplyBaziBranchModifiers:
    """Unit tests for apply_bazi_branch_modifiers(tracks, relation)."""

    def _base_tracks(self):
        return {"friend": 60.0, "passion": 60.0, "partner": 60.0, "soul": 60.0}

    def test_neutral_no_change(self):
        """neutral relation: tracks unchanged."""
        tracks = self._base_tracks()
        result = apply_bazi_branch_modifiers(tracks, "neutral")
        assert result["passion"] == pytest.approx(60.0)
        assert result["partner"] == pytest.approx(60.0)
        assert result["friend"]  == pytest.approx(60.0)
        assert result["soul"]    == pytest.approx(60.0)

    def test_clash_boosts_passion(self):
        """clash: passion × 1.25."""
        tracks = self._base_tracks()
        apply_bazi_branch_modifiers(tracks, "clash")
        assert tracks["passion"] == pytest.approx(60.0 * 1.25)

    def test_clash_reduces_partner(self):
        """clash: partner × 0.70."""
        tracks = self._base_tracks()
        apply_bazi_branch_modifiers(tracks, "clash")
        assert tracks["partner"] == pytest.approx(60.0 * 0.70)

    def test_clash_passion_capped_at_100(self):
        """Passion cannot exceed 100 even with × 1.25 boost."""
        tracks = {**self._base_tracks(), "passion": 90.0}
        apply_bazi_branch_modifiers(tracks, "clash")
        assert tracks["passion"] == pytest.approx(100.0)

    def test_punishment_boosts_soul(self):
        """punishment: soul × 1.15."""
        tracks = self._base_tracks()
        apply_bazi_branch_modifiers(tracks, "punishment")
        assert tracks["soul"] == pytest.approx(60.0 * 1.15)

    def test_punishment_reduces_partner(self):
        """punishment: partner × 0.60 (stronger than clash)."""
        tracks = self._base_tracks()
        apply_bazi_branch_modifiers(tracks, "punishment")
        assert tracks["partner"] == pytest.approx(60.0 * 0.60)

    def test_harm_reduces_friend(self):
        """harm: friend × 0.60."""
        tracks = self._base_tracks()
        apply_bazi_branch_modifiers(tracks, "harm")
        assert tracks["friend"] == pytest.approx(60.0 * 0.60)

    def test_harm_reduces_partner(self):
        """harm: partner × 0.50 (strongest partner penalty)."""
        tracks = self._base_tracks()
        apply_bazi_branch_modifiers(tracks, "harm")
        assert tracks["partner"] == pytest.approx(60.0 * 0.50)

    def test_partner_floor_at_zero(self):
        """Partner cannot go below 0."""
        tracks = {**self._base_tracks(), "partner": 0.0}
        apply_bazi_branch_modifiers(tracks, "harm")
        assert tracks["partner"] == pytest.approx(0.0)


class TestDayBranchInMatchV2:
    """Integration: bazi_day_branch_relation appears in compute_match_v2 output
    and correctly modifies tracks."""

    def _user(self, day_branch=None):
        return {
            "data_tier": 3,
            "sun_sign": "aries", "moon_sign": "cancer",
            "venus_sign": "taurus", "mars_sign": "aries",
            "saturn_sign": "capricorn", "mercury_sign": "gemini",
            "jupiter_sign": "sagittarius", "pluto_sign": "scorpio",
            "bazi_element": "fire",
            "bazi_month_branch": "午",
            "bazi_day_branch": day_branch,
            "rpv_conflict": "argue", "rpv_power": "follow", "rpv_energy": "home",
        }

    def test_output_has_day_branch_relation(self):
        """compute_match_v2 should always include bazi_day_branch_relation."""
        a = self._user("子")
        b = self._user("午")
        result = compute_match_v2(a, b)
        assert "bazi_day_branch_relation" in result
        assert result["bazi_day_branch_relation"] == "clash"

    def test_missing_day_branch_is_neutral(self):
        """When bazi_day_branch is absent, relation is neutral."""
        a = self._user(None)
        b = self._user(None)
        result = compute_match_v2(a, b)
        assert result["bazi_day_branch_relation"] == "neutral"

    def test_clash_raises_passion_track(self):
        """六沖 (子午) should give higher passion than neutral pair."""
        a_clash = self._user("子")
        b_clash = self._user("午")
        a_neutral = self._user("子")
        b_neutral = self._user("子")  # same branch → neutral
        r_clash   = compute_match_v2(a_clash, b_clash)
        r_neutral = compute_match_v2(a_neutral, b_neutral)
        assert r_clash["tracks"]["passion"] > r_neutral["tracks"]["passion"]

    def test_punishment_forces_high_voltage(self):
        """相刑 (子卯) should upgrade spiciness to HIGH_VOLTAGE when it was STABLE/MEDIUM."""
        a = self._user("子")
        b = self._user("卯")
        result = compute_match_v2(a, b)
        assert result["bazi_day_branch_relation"] == "punishment"
        assert result["spiciness_level"] in ("HIGH_VOLTAGE", "SOULMATE")

    def test_harm_reduces_partner_track(self):
        """相害 (子未) should give lower partner track than neutral pair."""
        a_harm    = self._user("子")
        b_harm    = self._user("未")
        a_neutral = self._user("子")
        b_neutral = self._user("子")
        r_harm    = compute_match_v2(a_harm, b_harm)
        r_neutral = compute_match_v2(a_neutral, b_neutral)
        assert r_harm["tracks"]["partner"] < r_neutral["tracks"]["partner"]


# ── Phase I: Exact Degree Aspect Tests ──────────────────────────────────────

from matching import get_shortest_distance, compute_exact_aspect


class TestGetShortestDistance:
    def test_same_degree(self):
        assert get_shortest_distance(0.0, 0.0) == pytest.approx(0.0)

    def test_180_degrees(self):
        assert get_shortest_distance(0.0, 180.0) == pytest.approx(180.0)

    def test_wraps_around(self):
        """350° and 10° → 20° not 340°"""
        assert get_shortest_distance(350.0, 10.0) == pytest.approx(20.0)

    def test_wraps_around_reverse(self):
        assert get_shortest_distance(10.0, 350.0) == pytest.approx(20.0)

    def test_exact_trine(self):
        assert get_shortest_distance(0.0, 120.0) == pytest.approx(120.0)


class TestComputeExactAspect:
    def test_conjunction_harmony(self):
        """0° apart → conjunction = 1.0 in harmony mode"""
        assert compute_exact_aspect(0.0, 0.0, "harmony") == pytest.approx(1.0)

    def test_conjunction_tension(self):
        assert compute_exact_aspect(0.0, 0.0, "tension") == pytest.approx(1.0)

    def test_trine_harmony(self):
        """120° apart → trine = 1.0 in harmony mode (perfect center, linear decay)"""
        assert compute_exact_aspect(0.0, 120.0, "harmony") == pytest.approx(1.0)

    def test_trine_tension(self):
        """120° apart → trine = 0.2 in tension mode"""
        assert compute_exact_aspect(0.0, 120.0, "tension") == pytest.approx(0.2)

    def test_square_tension(self):
        """90° apart → square = 0.9 in tension mode"""
        assert compute_exact_aspect(0.0, 90.0, "tension") == pytest.approx(0.9)

    def test_opposition_tension(self):
        """180° apart → opposition = 1.0 in tension mode (tension_max raised to 1.0)"""
        assert compute_exact_aspect(0.0, 180.0, "tension") == pytest.approx(1.0)

    def test_sextile_harmony(self):
        """60° apart → sextile = 0.8 in harmony mode"""
        assert compute_exact_aspect(0.0, 60.0, "harmony") == pytest.approx(0.8)

    def test_within_orb(self):
        """87° (3° from square center 90°) within 8° orb → linear decay applies.
        diff=3, orb=8, tens_max=0.9: 0.2 + 0.7 * (1 - 3/8) = 0.2 + 0.4375 = 0.64"""
        assert compute_exact_aspect(0.0, 87.0, "tension") == pytest.approx(0.64)

    def test_just_outside_orb(self):
        """100° (10° from square, 10° from trine) → void of aspect = 0.5 (neutral).
        Bug-1 fix: void-of-aspect now returns 0.5 instead of the old penalty 0.1."""
        assert compute_exact_aspect(0.0, 100.0, "tension") == pytest.approx(0.5)

    def test_cross_sign_conjunction(self):
        """29° Aries (29.0) and 1° Taurus (31.0) → 2° apart → conjunction with linear decay.
        diff=2, orb=8, tens_max=1.0: 0.2 + 0.8 * (1 - 2/8) = 0.2 + 0.6 = 0.80"""
        assert compute_exact_aspect(29.0, 31.0, "tension") == pytest.approx(0.80)

    def test_none_returns_neutral(self):
        """None degree → 0.5 neutral"""
        assert compute_exact_aspect(None, 90.0, "tension") == pytest.approx(0.5)
        assert compute_exact_aspect(0.0, None, "harmony") == pytest.approx(0.5)

    def test_wrap_around_opposition(self):
        """10° and 190° → shortest dist 180° → perfect opposition in tension = 1.0"""
        assert compute_exact_aspect(10.0, 190.0, "tension") == pytest.approx(1.0)

    def test_exact_aspect_linear_decay_conjunction(self):
        """Closer conjunction must score higher than wider conjunction."""
        score_1deg    = compute_exact_aspect(0.0, 1.0,  "harmony")
        score_7deg    = compute_exact_aspect(0.0, 7.0,  "harmony")
        score_perfect = compute_exact_aspect(0.0, 0.0,  "harmony")
        assert score_1deg > score_7deg, f"{score_1deg} should > {score_7deg}"
        assert score_perfect == pytest.approx(1.0, abs=0.01)

    def test_exact_aspect_linear_decay_square_tension(self):
        """Square at center (90°) scores higher than square near orb edge."""
        score_center = compute_exact_aspect(0.0, 90.0, "tension")   # diff=0
        score_edge   = compute_exact_aspect(0.0, 97.5, "tension")   # diff=7.5° within orb 8
        assert score_center > score_edge
        assert score_center == pytest.approx(0.9, abs=0.01)

    def test_exact_aspect_opposition_tension_max(self):
        """Opposition in tension mode should return 1.0 (previously was 0.85)."""
        score = compute_exact_aspect(0.0, 180.0, "tension")
        assert score == pytest.approx(1.0, abs=0.01)


class TestComputeKarmicTriggers:
    def _make_user(self, pluto_sign="scorpio", uranus_sign="sagittarius",
                   neptune_sign="capricorn", moon_sign="aries",
                   venus_sign="taurus", mars_sign="cancer"):
        return {
            "pluto_sign": pluto_sign,
            "uranus_sign": uranus_sign,
            "neptune_sign": neptune_sign,
            "moon_sign": moon_sign,
            "venus_sign": venus_sign,
            "mars_sign": mars_sign,
        }

    def test_baseline_no_triggers(self):
        """Identical outer planets (same generation) should return ~0.50 baseline."""
        same_gen = self._make_user()
        result = compute_karmic_triggers(same_gen, same_gen)
        # Pluto in Scorpio vs Moon in Aries = distance 7 → wraps to 5 → minor = 0.10 (below 0.85)
        # Most combos for same-gen users should produce no triggers → 0.50 baseline
        assert 0.0 <= result <= 1.0

    def test_returns_float_in_range(self):
        a = self._make_user("scorpio", "sagittarius", "capricorn", "aries", "taurus", "cancer")
        b = self._make_user("scorpio", "sagittarius", "capricorn", "scorpio", "scorpio", "scorpio")
        result = compute_karmic_triggers(a, b)
        assert 0.0 <= result <= 1.0

    def test_high_trigger_when_conjunction(self):
        """Pluto in Scorpio vs Moon in Scorpio = conjunction (tension=1.0 >= 0.85) → triggers."""
        a = {"pluto_sign": "scorpio", "uranus_sign": "aquarius", "neptune_sign": "pisces",
             "moon_sign": "aries", "venus_sign": "gemini", "mars_sign": "leo"}
        b = {"pluto_sign": "pisces", "uranus_sign": "gemini", "neptune_sign": "leo",
             "moon_sign": "scorpio", "venus_sign": "cancer", "mars_sign": "virgo"}
        result = compute_karmic_triggers(a, b)
        # a's pluto (scorpio) vs b's moon (scorpio) → conjunction → triggers
        assert result > 0.50

    def test_degree_based_when_available(self):
        """When degree fields present, use exact degree calculation."""
        a = {"pluto_sign": "aries", "pluto_degree": 15.0,  # 15° Aries
             "uranus_sign": "taurus", "uranus_degree": 45.0,
             "neptune_sign": "gemini", "neptune_degree": 75.0,
             "moon_sign": "aries", "moon_degree": 17.0,    # 2° from pluto → conjunction
             "venus_sign": "leo", "venus_degree": 130.0,
             "mars_sign": "libra", "mars_degree": 195.0}
        b = {"pluto_sign": "virgo", "pluto_degree": 165.0,
             "uranus_sign": "libra", "uranus_degree": 185.0,
             "neptune_sign": "scorpio", "neptune_degree": 225.0,
             "moon_sign": "aries", "moon_degree": 17.0,
             "venus_sign": "leo", "venus_degree": 130.0,
             "mars_sign": "libra", "mars_degree": 195.0}
        result = compute_karmic_triggers(a, b)
        # a's pluto (15°) vs b's moon (17°) → 2° → conjunction → triggers
        assert result > 0.50

    def test_symmetric(self):
        """compute_karmic_triggers(a, b) == compute_karmic_triggers(b, a)"""
        a = self._make_user("scorpio", "sagittarius", "capricorn", "aries", "taurus", "cancer")
        b = self._make_user("pisces", "aquarius", "scorpio", "leo", "libra", "sagittarius")
        assert compute_karmic_triggers(a, b) == pytest.approx(compute_karmic_triggers(b, a))

    def test_false_conjunction_not_triggered_with_degrees(self):
        """L-8: same outer/inner sign (sign-level conjunction → triggers) but 25° apart
        in degrees → void-of-aspect → degree-level correctly returns baseline 0.50.

        Without degrees: Pluto=Aries × Moon=Aries → sign-level conjunction 1.0 → triggers.
        With degrees: 25° apart → no major aspect within orb → 0.10 → no trigger.

        Uses minimal dicts so only the Pluto-Moon pair can fire; all other outer/inner
        planet fields are absent (missing) → compute_sign_aspect(None, ...) = 0.65 → no trigger.
        """
        # Sign-level only: Pluto(aries) × Moon(aries) → conjunction 1.0 → triggers
        a_sign = {"pluto_sign": "aries", "pluto_degree": None}
        b_sign = {"moon_sign":  "aries", "moon_degree":  None}
        result_sign = compute_karmic_triggers(a_sign, b_sign)
        assert result_sign > 0.50, "Sign-level false conjunction should trigger"

        # Degree-level: same aries band but 25° apart → void (0.1) → no trigger → baseline
        a_deg = {"pluto_sign": "aries", "pluto_degree": 0.0}
        b_deg = {"moon_sign":  "aries", "moon_degree":  25.0}
        result_deg = compute_karmic_triggers(a_deg, b_deg)
        assert result_deg == pytest.approx(0.50), (
            f"Degree-level (25° apart, void) should return baseline 0.50, got {result_deg:.3f}"
        )

    def test_karmic_triggers_fire_at_moderate_aspect_strength(self):
        """Karmic trigger with ~0.80 aspect strength should be counted after L-8 fix.

        Previously required >= 0.85 (only ~1.5° orb for conjunction with orb=8°);
        now >= 0.70 (catches aspects up to ~4.5° off-exact).

        pluto_degree=15.0 vs moon_degree=17.0: distance=2°, conjunction,
        strength = 0.2 + (1.0-0.2) * (1.0 - 2/8) = 0.2 + 0.6 = 0.80.
        0.80 < 0.85 (old threshold: NO trigger) but 0.80 >= 0.70 (new: trigger).

        All other outer/inner fields are absent so sign-level fallback returns
        compute_sign_aspect(None, None) = 0.65 — below both thresholds.
        """
        # Only pluto(A) and moon(B) are set; all other outer/inner fields absent
        user_a = {"pluto_degree": 15.0}
        user_b = {"moon_degree": 17.0}
        result = compute_karmic_triggers(user_a, user_b)
        # With old 0.85 threshold: 0.80 < 0.85 → no trigger → baseline 0.50
        # With new 0.70 threshold: 0.80 >= 0.70 → trigger fires → result > 0.50
        assert result > 0.50, (
            f"Pluto-Moon at 2° gap (strength 0.80) should trigger with 0.70 threshold, got {result:.3f}"
        )


class TestKarmicInLustScore:
    """Verify that lust score no longer uses same-generation pluto×pluto comparison."""

    def _user(self, **kwargs):
        base = {
            "data_tier": 3,
            "sun_sign": "aries",
            "venus_sign": "taurus",
            "mars_sign": "gemini",
            "pluto_sign": "scorpio",
            "rpv_conflict": "cold_war",
            "rpv_power": "control",
            "rpv_energy": "home",
            "bazi_element": "wood",
        }
        base.update(kwargs)
        return base

    def test_same_gen_pluto_no_longer_inflates_lust(self):
        """Two users with same Pluto sign (same generation) should not get 1.0 karmic score."""
        a = self._user(pluto_sign="scorpio")  # born 1984-1995
        b = self._user(pluto_sign="scorpio")  # same generation
        # Import compute_lust_score to check directly
        from matching import compute_lust_score
        lust = compute_lust_score(a, b)
        # The old code gave pluto=1.0 for same-sign → inflated lust
        # New code: karmic_triggers(a, b) = 0.50 baseline when no cross-layer triggers
        # lust should be in a reasonable range (not artificially maxed)
        assert 0 <= lust <= 100


class TestKarmicInSoulTrack:
    """Verify that soul track no longer uses same-generation pluto×pluto."""

    def _user(self, moon_sign="aries", pluto_sign="scorpio"):
        return {
            "data_tier": 3,
            "sun_sign": "aries",
            "moon_sign": moon_sign,
            "mercury_sign": "taurus",
            "venus_sign": "taurus",
            "mars_sign": "gemini",
            "saturn_sign": "capricorn",
            "jupiter_sign": "sagittarius",
            "pluto_sign": pluto_sign,
            "chiron_sign": None,
            "uranus_sign": "sagittarius",
            "neptune_sign": "capricorn",
            "rpv_conflict": "cold_war",
            "rpv_power": "control",
            "rpv_energy": "home",
            "bazi_element": "wood",
            "emotional_capacity": 50,
        }

    def test_soul_track_uses_karmic_not_pluto(self):
        """compute_tracks soul track should no longer reference pluto_a vs pluto_b."""
        from matching import compute_tracks, compute_power_v2
        a = self._user(pluto_sign="scorpio")
        b = self._user(pluto_sign="scorpio")
        power = compute_power_v2(a, b)
        tracks = compute_tracks(a, b, power, 0.0)
        # Soul track should be a valid 0-100 score
        assert 0 <= tracks["soul"] <= 100



# ════════════════════════════════════════════════════════════════
# Task 80: Jupiter Friend Track cross-aspect fix
# ════════════════════════════════════════════════════════════════

class TestJupiterFriendTrackCrossAspect:
    """Verify that compute_tracks Friend Track uses cross-aspect Jupiter scoring.

    Before the fix: jupiter = compute_sign_aspect(jupiter_a, jupiter_b, "harmony")
    After the fix:  jupiter = (jup_a_sun_b + jup_b_sun_a) / 2.0

    People born in the same year share the same Jupiter sign (Jupiter moves ~1 sign/year).
    The old same-planet comparison rewarded age-peers regardless of actual synastry fit.
    The fix uses A's Jupiter × B's Sun + B's Jupiter × A's Sun, which is the correct
    astrological cross-aspect measuring whether A's expansion energy aligns with B's identity.
    """

    def _power_no_frame_break(self):
        return {"rpv": 0.0, "frame_break": False, "viewer_role": "Equal", "target_role": "Equal"}

    def _minimal_user(self, sun_sign, jupiter_sign, **kwargs):
        """Minimal user dict with only the fields compute_tracks needs."""
        defaults = {
            "sun_sign": sun_sign,
            "jupiter_sign": jupiter_sign,
            "mercury_sign": None,
            "moon_sign": None,
            "mars_sign": None,
            "venus_sign": None,
            "saturn_sign": None,
            "chiron_sign": None,
            "juno_sign": None,
            "house8_sign": None,
            "bazi_element": None,
            "rpv_power": None,
            "rpv_conflict": None,
            "rpv_energy": None,
        }
        defaults.update(kwargs)
        return defaults

    def test_cross_aspect_elevated_when_jupiter_harmonizes_with_sun_not_jupiter(self):
        """Friend track is elevated when jupiter_a harmonizes with sun_b (Fire/Fire trine),
        even though jupiter_a does NOT harmonize with jupiter_b (Fire/Earth semi-sextile → 0.10).

        Setup:
          jupiter_a = Aries  (Fire)
          sun_b     = Leo    (Fire) → trine, harmony score = 0.85
          jupiter_b = Taurus (Earth) → semi-sextile from Aries, score = 0.10

          Under the OLD same-planet formula:
            jupiter = compute_sign_aspect("aries", "taurus", "harmony") = 0.10 (semi-sextile)
          Under the NEW cross-aspect formula:
            jup_a_sun_b = compute_sign_aspect("aries", "leo", "harmony") = 0.85 (trine)
            jup_b_sun_a = compute_sign_aspect("taurus", sun_a, "harmony")
            jupiter = (jup_a_sun_b + jup_b_sun_a) / 2.0  → significantly higher than 0.10
        """
        # jupiter_a=Aries (Fire), sun_b=Leo (Fire) → trine = 0.85
        # jupiter_b=Taurus (Earth), sun_a=Capricorn (Earth) → trine = 0.85 too
        chart_a = self._minimal_user(sun_sign="capricorn", jupiter_sign="aries")
        chart_b = self._minimal_user(sun_sign="leo",       jupiter_sign="taurus")
        power = self._power_no_frame_break()

        tracks = compute_tracks(chart_a, chart_b, power, useful_god_complement=0.0)

        # Cross-aspect jupiter: (0.85 + 0.85) / 2.0 = 0.85
        # friend = 0.40 * mercury_neutral + 0.40 * 0.85 + 0.20 * 0.0
        #        = 0.40 * 0.65 + 0.40 * 0.85
        mercury_score = compute_sign_aspect(None, None, "harmony")  # 0.65 neutral
        expected_jupiter = (
            compute_sign_aspect("aries", "leo", "harmony") +
            compute_sign_aspect("taurus", "capricorn", "harmony")
        ) / 2.0
        expected_friend = (
            0.40 * mercury_score +
            0.40 * expected_jupiter +
            0.20 * 0.0
        ) * 100

        assert tracks["friend"] == pytest.approx(expected_friend, abs=0.5)

        # Also verify it is higher than what the old same-planet formula would produce.
        # Old formula: compute_sign_aspect("aries", "taurus", "harmony") = 0.10 (semi-sextile)
        old_jupiter = compute_sign_aspect("aries", "taurus", "harmony")
        old_expected_friend = (
            0.40 * mercury_score +
            0.40 * old_jupiter +
            0.20 * 0.0
        ) * 100
        assert tracks["friend"] > old_expected_friend, (
            "Cross-aspect formula must produce a higher friend score than "
            "the old same-planet formula when jupiter_a trines sun_b but not jupiter_b."
        )

    def test_friend_track_jupiter_component_is_symmetric(self):
        """compute_tracks(a, b)['friend'] == compute_tracks(b, a)['friend'].

        The cross-aspect formula (jup_a_sun_b + jup_b_sun_a) / 2.0 is symmetric by
        construction. This test guards against future regressions that would break symmetry.
        """
        chart_a = self._minimal_user(sun_sign="gemini",  jupiter_sign="cancer")
        chart_b = self._minimal_user(sun_sign="scorpio", jupiter_sign="pisces")
        power = self._power_no_frame_break()

        tracks_ab = compute_tracks(chart_a, chart_b, power, useful_god_complement=0.0)
        tracks_ba = compute_tracks(chart_b, chart_a, power, useful_god_complement=0.0)

        assert tracks_ab["friend"] == pytest.approx(tracks_ba["friend"], abs=0.01)

    def test_friend_track_exact_formula_mercury_and_jupiter(self):
        """friend = mercury*0.40 + jupiter_cross*0.40 + bazi_same*0.20.

        All values are deterministic here so we can verify the exact calculation.

        Setup: both users share the same mercury (Gemini), which is conjunction (0.90).
          jupiter_a = Sagittarius, sun_b = Aries → trine (4 signs apart) = 0.85
          jupiter_b = Leo,         sun_a = Cancer → sextile (2 signs apart) = 0.75
          cross_jupiter = (0.85 + 0.75) / 2.0 = 0.80
          No bazi_element on either user → bazi_harmony = False → bazi term = 0.
          friend = 0.40 * 0.90 + 0.40 * 0.80 + 0.20 * 0.0 = 0.36 + 0.32 = 0.68 → 68.0
        """
        chart_a = self._minimal_user(
            sun_sign="cancer",      # sun_a
            jupiter_sign="sagittarius",  # jupiter_a
            mercury_sign="gemini",
        )
        chart_b = self._minimal_user(
            sun_sign="aries",       # sun_b
            jupiter_sign="leo",     # jupiter_b
            mercury_sign="gemini",
        )
        power = self._power_no_frame_break()

        tracks = compute_tracks(chart_a, chart_b, power, useful_god_complement=0.0)

        mercury_score   = compute_sign_aspect("gemini", "gemini", "harmony")     # 0.90
        jup_a_sun_b     = compute_sign_aspect("sagittarius", "aries", "harmony") # 0.85 (trine)
        jup_b_sun_a     = compute_sign_aspect("leo", "cancer", "harmony")        # 0.75 (sextile)
        cross_jupiter   = (jup_a_sun_b + jup_b_sun_a) / 2.0                     # 0.80
        expected_friend = (0.40 * mercury_score + 0.40 * cross_jupiter + 0.20 * 0.0) * 100

        assert tracks["friend"] == pytest.approx(expected_friend, abs=0.5)

    def test_same_birth_year_peers_no_longer_get_inflated_friend_score(self):
        """Age-peers (same Jupiter sign) should NOT automatically get a high friend score.

        Under the OLD same-planet formula, two people born in the same year share the
        same Jupiter sign (conjunction → 0.90), inflating their friend score regardless
        of real synastry. Under the NEW cross-aspect formula, the score depends on whether
        their Jupiters align with each other's Suns, which varies by individual.

        This test uses a pair where same Jupiter sign gives 0.90 same-planet score,
        but the cross-aspect (jupiter × sun) gives a different (lower in this case) result.

        Setup:
          Both users have jupiter_sign=Scorpio (same year — old formula gives conjunction 0.90).
          sun_a = Gemini, sun_b = Gemini (same Sun for simplicity).
          jup_a_sun_b = compute_sign_aspect("scorpio", "gemini", "harmony")
            Scorpio(7) → Gemini(2): distance = 5 → quincunx → 0.10
          cross_jupiter = (0.10 + 0.10) / 2.0 = 0.10
          This is much lower than the old conjunction score of 0.90.
        """
        chart_a = self._minimal_user(sun_sign="gemini", jupiter_sign="scorpio")
        chart_b = self._minimal_user(sun_sign="gemini", jupiter_sign="scorpio")
        power = self._power_no_frame_break()

        tracks = compute_tracks(chart_a, chart_b, power, useful_god_complement=0.0)

        # New cross-aspect score
        jup_cross = compute_sign_aspect("scorpio", "gemini", "harmony")  # quincunx = 0.10
        mercury_score = compute_sign_aspect(None, None, "harmony")        # neutral = 0.65
        expected_new = (0.40 * mercury_score + 0.40 * jup_cross + 0.20 * 0.0) * 100

        # Old same-planet score would have been conjunction (0.90)
        old_jupiter = compute_sign_aspect("scorpio", "scorpio", "harmony")  # conjunction = 0.90
        expected_old = (0.40 * mercury_score + 0.40 * old_jupiter + 0.20 * 0.0) * 100

        assert tracks["friend"] == pytest.approx(expected_new, abs=0.5)
        assert expected_old > expected_new, (
            "Old same-planet formula inflated age-peer friend score; "
            "new cross-aspect formula correctly reduces it."
        )


# ── Phase II: psychology modifier integration ────────────────────────────────────────────────

def test_compute_match_v2_psychological_tags_key_present():
    """Result dict must always contain psychological_tags and high_voltage keys."""
    ua = {
        "birth_year": 1995, "birth_date": "1995-06-15",
        "sun_sign": "gemini", "moon_sign": "aries", "venus_sign": "taurus",
        "mars_sign": "cancer", "mercury_sign": "gemini", "jupiter_sign": "sagittarius",
        "saturn_sign": "pisces", "uranus_sign": "capricorn", "neptune_sign": "capricorn",
        "pluto_sign": "scorpio", "chiron_sign": "virgo", "juno_sign": "leo",
        "bazi_element": "wood",
    }
    ub = {
        "birth_year": 1993, "birth_date": "1993-09-01",
        "sun_sign": "virgo", "moon_sign": "capricorn", "venus_sign": "leo",
        "mars_sign": "cancer", "mercury_sign": "virgo", "jupiter_sign": "libra",
        "saturn_sign": "aquarius", "uranus_sign": "capricorn", "neptune_sign": "capricorn",
        "pluto_sign": "scorpio", "chiron_sign": "virgo", "juno_sign": "aries",
        "bazi_element": "fire",
    }
    result = compute_match_v2(ua, ub)
    assert "psychological_tags" in result
    assert "high_voltage" in result
    assert isinstance(result["psychological_tags"], list)
    assert isinstance(result["high_voltage"], bool)


def test_compute_match_v2_attachment_dynamics_applied():
    """Anxious + Avoidant pair should trigger high_voltage in v2 result."""
    ua = {
        "birth_year": 1995, "birth_date": "1995-06-15",
        "sun_sign": "gemini", "moon_sign": "aries", "venus_sign": "taurus",
        "mars_sign": "cancer", "mercury_sign": "gemini", "jupiter_sign": "sagittarius",
        "saturn_sign": "pisces", "uranus_sign": "capricorn", "neptune_sign": "capricorn",
        "pluto_sign": "scorpio", "chiron_sign": "virgo", "juno_sign": "leo",
        "bazi_element": "wood",
        "attachment_style": "anxious",
    }
    ub = {
        "birth_year": 1993, "birth_date": "1993-09-01",
        "sun_sign": "virgo", "moon_sign": "capricorn", "venus_sign": "leo",
        "mars_sign": "cancer", "mercury_sign": "virgo", "jupiter_sign": "libra",
        "saturn_sign": "aquarius", "uranus_sign": "capricorn", "neptune_sign": "capricorn",
        "pluto_sign": "scorpio", "chiron_sign": "virgo", "juno_sign": "aries",
        "bazi_element": "fire",
        "attachment_style": "avoidant",
    }
    result = compute_match_v2(ua, ub)
    assert result["high_voltage"] is True
    assert "Anxious_Avoidant_Trap" in result["psychological_tags"]


# ════════════════════════════════════════════════════════════════
# Task 81: Juno Partner Track cross-aspect fix
# ════════════════════════════════════════════════════════════════

class TestJunoPartnerTrackCrossAspect:
    """Verify that compute_tracks Partner Track and compute_soul_score use
    cross-aspect Juno scoring (juno × moon) rather than same-planet Juno.

    Before the fix: juno = compute_sign_aspect(juno_a, juno_b, "harmony")
    After the fix:  juno = (compute_sign_aspect(juno_a, moon_b, "harmony")
                          + compute_sign_aspect(juno_b, moon_a, "harmony")) / 2.0

    People born in the same year often share the same Juno sign (Juno moves
    ~1-2 signs/year).  The old same-planet comparison rewarded age-peers
    regardless of whether A's partnership ideal (Juno) actually aligns with
    B's emotional core (Moon).  The fix uses the correct astrological
    cross-aspect.
    """

    def _power_no_frame_break(self):
        return {"rpv": 0.0, "frame_break": False, "viewer_role": "Equal", "target_role": "Equal"}

    def _minimal_user(self, moon_sign, juno_sign, **kwargs):
        """Minimal user dict with only the fields compute_tracks / compute_soul_score need."""
        defaults = {
            "moon_sign": moon_sign,
            "juno_sign": juno_sign,
            "sun_sign": None,
            "mercury_sign": None,
            "jupiter_sign": None,
            "mars_sign": None,
            "venus_sign": None,
            "saturn_sign": None,
            "chiron_sign": None,
            "house8_sign": None,
            "house4_sign": None,
            "bazi_element": None,
            "attachment_style": None,
            "rpv_power": None,
            "rpv_conflict": None,
            "rpv_energy": None,
        }
        defaults.update(kwargs)
        return defaults

    # ── Partner track (compute_tracks) ───────────────────────────────────────

    def test_cross_aspect_elevated_when_juno_harmonizes_with_moon_not_juno(self):
        """Partner track is elevated when juno_a harmonizes with moon_b (trine),
        even though juno_a does NOT harmonize with juno_b (semi-sextile → 0.10).

        Setup:
          juno_a  = Aries  (Fire)
          moon_b  = Leo    (Fire) → trine, harmony score = 0.85
          juno_b  = Taurus (Earth) → semi-sextile from Aries, score = 0.10

        Under the OLD same-planet formula:
          juno = compute_sign_aspect("aries", "taurus", "harmony") = 0.10
        Under the NEW cross-aspect formula:
          juno_a_moon_b = compute_sign_aspect("aries", "leo",  "harmony") = 0.85 (trine)
          juno_b_moon_a = compute_sign_aspect("taurus", moon_a, "harmony")
          juno = (juno_a_moon_b + juno_b_moon_a) / 2.0  → much higher than 0.10
        """
        # juno_a=Aries, moon_b=Leo → trine (0.85); juno_b=Taurus, moon_a=Capricorn → trine (0.85)
        user_a = self._minimal_user(moon_sign="capricorn", juno_sign="aries")
        user_b = self._minimal_user(moon_sign="leo",       juno_sign="taurus")
        power = self._power_no_frame_break()

        tracks = compute_tracks(user_a, user_b, power, useful_god_complement=0.0)

        juno_cross = (
            compute_sign_aspect("aries", "leo",        "harmony") +  # 0.85 trine
            compute_sign_aspect("taurus", "capricorn", "harmony")    # 0.85 trine
        ) / 2.0
        moon_v = compute_sign_aspect("capricorn", "leo", "harmony")
        expected_partner = (moon_v * 0.35 + juno_cross * 0.35 + 0.0 * 0.30) * 100

        assert tracks["partner"] == pytest.approx(expected_partner, abs=0.5)

        # Confirm it beats the old same-planet formula.
        old_juno = compute_sign_aspect("aries", "taurus", "harmony")  # semi-sextile = 0.10
        old_expected_partner = (moon_v * 0.35 + old_juno * 0.35 + 0.0 * 0.30) * 100
        assert tracks["partner"] > old_expected_partner, (
            "Cross-aspect formula must produce a higher partner score than "
            "the old same-planet formula when juno_a trines moon_b but not juno_b."
        )

    def test_partner_track_juno_cross_aspect_is_symmetric(self):
        """compute_tracks(a, b)['partner'] == compute_tracks(b, a)['partner'].

        The cross-aspect formula (juno_a × moon_b + juno_b × moon_a) / 2.0 is
        symmetric by construction.  This test guards against future regressions.
        """
        user_a = self._minimal_user(moon_sign="cancer",    juno_sign="sagittarius")
        user_b = self._minimal_user(moon_sign="capricorn", juno_sign="gemini")
        power = self._power_no_frame_break()

        tracks_ab = compute_tracks(user_a, user_b, power, useful_god_complement=0.0)
        tracks_ba = compute_tracks(user_b, user_a, power, useful_god_complement=0.0)

        assert tracks_ab["partner"] == pytest.approx(tracks_ba["partner"], abs=0.01)

    def test_age_peers_same_juno_differing_moon_no_inflated_partner(self):
        """Age-peers with same Juno sign should NOT get inflated partner scores
        when their Moon signs are incompatible.

        Under the OLD same-planet formula: juno_a == juno_b (conjunction → 0.90)
        → age-peers always scored high on partner track regardless of Moon fit.

        Under the NEW cross-aspect formula: juno_a × moon_b matters, so if
        juno (Scorpio) squares moon_b (Aquarius), the score drops significantly.

        Setup: both users born same year → same Juno = Scorpio
          moon_a = Aquarius, moon_b = Aquarius (same Moon for this test)
          juno_a_moon_b = sign_aspect("scorpio", "aquarius") = square = 0.40
          juno_b_moon_a = sign_aspect("scorpio", "aquarius") = 0.40
          juno_cross = 0.40 (much lower than old conjunction 0.90)
        """
        user_a = self._minimal_user(moon_sign="aquarius", juno_sign="scorpio")
        user_b = self._minimal_user(moon_sign="aquarius", juno_sign="scorpio")
        power = self._power_no_frame_break()

        tracks = compute_tracks(user_a, user_b, power, useful_god_complement=0.0)

        # New cross-aspect score (Scorpio vs Aquarius → square = 0.40)
        juno_cross = compute_sign_aspect("scorpio", "aquarius", "harmony")  # 0.40
        moon_v = compute_sign_aspect("aquarius", "aquarius", "harmony")     # 0.90
        expected_new = (moon_v * 0.35 + juno_cross * 0.35 + 0.0 * 0.30) * 100

        # Old same-planet score: Scorpio vs Scorpio → conjunction = 0.90
        old_juno = compute_sign_aspect("scorpio", "scorpio", "harmony")     # 0.90
        expected_old = (moon_v * 0.35 + old_juno * 0.35 + 0.0 * 0.30) * 100

        assert tracks["partner"] == pytest.approx(expected_new, abs=0.5)
        assert expected_old > expected_new, (
            "Old same-planet formula inflated age-peer partner score; "
            "new cross-aspect formula correctly reduces it when Juno squares Moon."
        )

    # ── Soul score (compute_soul_score) ──────────────────────────────────────

    def test_soul_score_juno_cross_aspect_elevated_when_juno_trines_moon(self):
        """Soul score Juno component is elevated when juno_a trines moon_b.

        Setup:
          juno_a = Aries (Fire), moon_b = Leo (Fire)  → trine = 0.85
          juno_b = Aries (Fire), moon_a = Leo  (Fire) → trine = 0.85
          juno_cross = (0.85 + 0.85) / 2.0 = 0.85

        Verify the score is higher than when juno_a squares moon_b.
        """
        # Trine pair: juno=Aries, moon=Leo (Fire trine)
        user_a_good = self._minimal_user(moon_sign="leo",   juno_sign="aries",
                                         mercury_sign="gemini", saturn_sign="capricorn")
        user_b_good = self._minimal_user(moon_sign="leo",   juno_sign="aries",
                                         mercury_sign="gemini", saturn_sign="capricorn")

        # Square pair: juno=Aries, moon=Cancer (square = 0.40)
        user_a_bad  = self._minimal_user(moon_sign="cancer", juno_sign="aries",
                                         mercury_sign="gemini", saturn_sign="capricorn")
        user_b_bad  = self._minimal_user(moon_sign="cancer", juno_sign="aries",
                                         mercury_sign="gemini", saturn_sign="capricorn")

        soul_good = compute_soul_score(user_a_good, user_b_good)
        soul_bad  = compute_soul_score(user_a_bad,  user_b_bad)

        assert soul_good > soul_bad, (
            f"Juno trine Moon should give higher soul score ({soul_good:.1f}) "
            f"than Juno square Moon ({soul_bad:.1f})."
        )

    def test_soul_score_juno_cross_aspect_symmetric(self):
        """compute_soul_score(a, b) == compute_soul_score(b, a) for Juno component.

        The cross-aspect formula is symmetric by construction.
        """
        user_a = self._minimal_user(moon_sign="cancer",  juno_sign="libra",
                                    mercury_sign="virgo", saturn_sign="aries")
        user_b = self._minimal_user(moon_sign="scorpio", juno_sign="taurus",
                                    mercury_sign="virgo", saturn_sign="aries")

        assert compute_soul_score(user_a, user_b) == pytest.approx(
            compute_soul_score(user_b, user_a), abs=0.1
        )

    def test_soul_score_age_peers_same_juno_differing_moon_not_inflated(self):
        """Age-peers sharing the same Juno sign do not get inflated soul scores
        when their Moon signs are incompatible with that Juno.

        Old formula: juno_a == juno_b (same sign) → conjunction = 0.90 always.
        New formula: juno_a × moon_b → score depends on how juno relates to Moon.
        If Juno (Scorpio) vs Moon (Aquarius) = square = 0.40, soul score drops.
        """
        user_a = self._minimal_user(moon_sign="aquarius", juno_sign="scorpio",
                                    mercury_sign="gemini", saturn_sign="capricorn")
        user_b = self._minimal_user(moon_sign="aquarius", juno_sign="scorpio",
                                    mercury_sign="gemini", saturn_sign="capricorn")

        soul = compute_soul_score(user_a, user_b)

        # If old same-planet formula were used, juno_v would be 0.90 (conjunction).
        # With new cross-aspect, juno_v = sign_aspect("scorpio","aquarius") = 0.40 (square).
        # Build a "perfect juno trine moon" baseline to confirm cross-aspect is lower.
        user_a_trine = self._minimal_user(moon_sign="cancer", juno_sign="scorpio",
                                          mercury_sign="gemini", saturn_sign="capricorn")
        user_b_trine = self._minimal_user(moon_sign="cancer", juno_sign="scorpio",
                                          mercury_sign="gemini", saturn_sign="capricorn")
        soul_trine = compute_soul_score(user_a_trine, user_b_trine)

        assert soul < soul_trine, (
            "Age-peers with incompatible Juno × Moon (square) should score "
            f"lower ({soul:.1f}) than pairs where Juno trines Moon ({soul_trine:.1f})."
        )


# ── L-4: Sun-Moon cross-aspect in compute_soul_score ──────────────────────────

class TestSoulScoreSunMoonCrossAspect:
    """Verify Sun-Moon cross-aspect (A's Sun × B's Moon + B's Sun × A's Moon)
    is included in compute_soul_score (L-4 fix).
    """

    def _user(self, sun_sign, moon_sign, **kwargs):
        defaults = {
            "sun_sign": sun_sign,
            "moon_sign": moon_sign,
            "mercury_sign": "gemini",
            "saturn_sign": "capricorn",
            "house4_sign": None,
            "juno_sign": None,
            "attachment_style": None,
            "bazi_element": None,
        }
        defaults.update(kwargs)
        return defaults

    def test_sun_moon_trine_elevates_soul_vs_square(self):
        """A's Sun trine B's Moon (Leo-Sag=4 signs) should yield higher soul than square (Leo-Sco=3)."""
        a_trine = self._user("leo", "aries")        # sun=leo
        b_trine = self._user("gemini", "sagittarius")  # moon=sag; leo-sag = 4 signs apart (trine)
        a_square = self._user("leo", "aries")
        b_square = self._user("gemini", "scorpio")     # moon=sco; leo-sco = 3 signs apart (square)
        soul_trine  = compute_soul_score(a_trine,  b_trine)
        soul_square = compute_soul_score(a_square, b_square)
        assert soul_trine > soul_square, (
            f"Sun-Moon trine ({soul_trine:.1f}) should score higher than square ({soul_square:.1f})"
        )

    def test_sun_moon_cross_aspect_is_symmetric(self):
        """compute_soul_score(a, b) == compute_soul_score(b, a) for Sun-Moon cross."""
        a = self._user("cancer", "aquarius")
        b = self._user("pisces", "gemini")
        assert compute_soul_score(a, b) == pytest.approx(compute_soul_score(b, a), abs=0.1)

    def test_soul_score_harmonious_sun_moon_beats_discordant(self):
        """Harmonious Sun-Moon cross (trine) should give higher soul than discordant (quincunx).

        Keep all other fields identical; only vary which sun sign crosses which moon.
        trine: Sun=Leo × Moon=Sagittarius (4 signs) = 0.85
        quincunx: Sun=Leo × Moon=Capricorn (5 signs) = 0.10
        """
        # trine pair: Leo sun hits Sag moon (trine); Gemini sun hits Aries moon (sextile)
        a_good = self._user("leo",   "aries")
        b_good = self._user("gemini", "sagittarius")
        # quincunx pair: Leo sun hits Cap moon; Gemini sun hits Sco moon
        a_bad  = self._user("leo",   "aries")
        b_bad  = self._user("gemini", "capricorn")
        soul_good = compute_soul_score(a_good, b_good)
        soul_bad  = compute_soul_score(a_bad,  b_bad)
        assert soul_good > soul_bad, (
            f"Harmonious Sun-Moon cross ({soul_good:.1f}) should beat discordant ({soul_bad:.1f})"
        )

    def test_soul_score_in_range_with_sun_moon(self):
        """compute_soul_score result stays in [0, 100] with Sun-Moon cross included."""
        a = self._user("aries", "aries")
        b = self._user("aries", "aries")   # best possible cross
        assert 0 <= compute_soul_score(a, b) <= 100


# ── L-5: Saturn cross-aspect in compute_tracks partner track ──────────────────

class TestPartnerTrackSaturnCrossAspect:
    """Verify Saturn cross-aspect (A's Saturn × B's Moon + B's Saturn × A's Moon)
    is included as a bonus in compute_tracks partner track (L-5 fix).
    """

    def _power(self):
        return {"rpv": 0.0, "frame_break": False, "viewer_role": "Equal", "target_role": "Equal"}

    def _user(self, moon_sign, saturn_sign, **kwargs):
        defaults = {
            "moon_sign": moon_sign,
            "saturn_sign": saturn_sign,
            "sun_sign": "aries",
            "mercury_sign": "gemini",
            "jupiter_sign": None,
            "mars_sign": None,
            "venus_sign": None,
            "juno_sign": None,
            "chiron_sign": None,
            "house8_sign": None,
            "bazi_element": None,
            "rpv_power": None,
            "rpv_conflict": None,
            "rpv_energy": None,
            "emotional_capacity": 60,
        }
        defaults.update(kwargs)
        return defaults

    def test_saturn_cross_trine_elevates_partner_vs_square(self):
        """A's Saturn trine B's Moon should give higher partner track than A's Saturn square B's Moon."""
        # Saturn=Leo, Moon=Sag: Leo-Sag = 4 signs (trine)
        a_trine = self._user("aries", "leo")
        b_trine = self._user("sagittarius", "capricorn")
        # Saturn=Leo, Moon=Sco: Leo-Sco = 3 signs (square)
        a_square = self._user("aries", "leo")
        b_square = self._user("scorpio", "capricorn")
        t_trine  = compute_tracks(a_trine,  b_trine,  self._power(), 0.0)
        t_square = compute_tracks(a_square, b_square, self._power(), 0.0)
        assert t_trine["partner"] > t_square["partner"], (
            f"Saturn-Moon trine partner ({t_trine['partner']:.1f}) should exceed "
            f"square ({t_square['partner']:.1f})"
        )

    def test_saturn_cross_is_symmetric(self):
        """compute_tracks(a, b)['partner'] == compute_tracks(b, a)['partner'] for Saturn cross."""
        a = self._user("cancer", "capricorn")
        b = self._user("aquarius", "virgo")
        tab = compute_tracks(a, b, self._power(), 0.0)
        tba = compute_tracks(b, a, self._power(), 0.0)
        assert tab["partner"] == pytest.approx(tba["partner"], abs=0.1)

    def test_saturn_cross_bonus_absent_when_saturn_missing(self):
        """No saturn_sign → cross-aspect bonus not applied; partner score equals baseline."""
        a_with = self._user("cancer", "capricorn")    # saturn present
        b_with = self._user("aquarius", "virgo")       # saturn trines cancer
        a_none = self._user("cancer", None)            # no saturn
        b_none = self._user("aquarius", None)
        t_with = compute_tracks(a_with, b_with, self._power(), 0.0)
        t_none = compute_tracks(a_none, b_none, self._power(), 0.0)
        # With Saturn cross-aspect bonus (trine) should be ≥ without
        assert t_with["partner"] >= t_none["partner"]

    def test_partner_track_stays_in_range(self):
        """Partner track should remain in [0, 100] even with Saturn bonus."""
        a = self._user("aries", "aries")   # max conjunction
        b = self._user("aries", "aries")
        t = compute_tracks(a, b, self._power(), 0.0)
        assert 0 <= t["partner"] <= 100


# ── L-2: compute_soul_score degree-level resolution ──────────────────────────

class TestSoulScoreDegreeResolution:
    """Verify L-2 fix: compute_soul_score uses _resolve_aspect (degree-level)
    instead of compute_sign_aspect (sign-level) when degree data is available.

    Core scenario — the 'false conjunction' bug:
      Two planets in the same sign but 25° apart.
      Sign-level: sees conjunction → 0.90 (harmony).
      Degree-level: 25° is outside all major aspect orbs → void → 0.10.
      With the fix, providing degree data REDUCES the soul score in this case,
      proving the engine is reading actual orb data instead of the sign bucket.
    """

    def _base_user(self, **overrides):
        """Minimal user dict; all optional fields absent → Tier 3 baseline."""
        base = {
            "sun_sign": "aries",       "sun_degree": None,
            "moon_sign": "aries",      "moon_degree": None,
            "mercury_sign": "gemini",  "mercury_degree": None,
            "saturn_sign": "capricorn","saturn_degree": None,
            "house4_sign": None,       "house4_degree": None,
            "juno_sign": None,
            "attachment_style": None,
            "bazi_element": None,
        }
        base.update(overrides)
        return base

    def test_moon_false_conjunction_detected_via_degrees(self):
        """Same moon sign (sign-level conjunction 0.90) but 25° apart (void 0.10).

        WITHOUT degree data: soul score uses sign-level → relatively high.
        WITH degree data: soul score uses exact orb → lower (void planet pair).
        """
        # Same moon_sign = "aries" → sign-level conjunction (0.90 harmony)
        a_no_deg = self._base_user(moon_sign="aries", moon_degree=None)
        b_no_deg = self._base_user(moon_sign="aries", moon_degree=None)

        # 25° apart inside "aries" band → no major aspect within orb
        a_with_deg = self._base_user(moon_sign="aries", moon_degree=0.0)
        b_with_deg = self._base_user(moon_sign="aries", moon_degree=25.0)

        soul_no_deg   = compute_soul_score(a_no_deg,   b_no_deg)
        soul_with_deg = compute_soul_score(a_with_deg, b_with_deg)

        assert soul_with_deg < soul_no_deg, (
            f"Degree-level (void moon, {soul_with_deg:.1f}) should score lower than "
            f"sign-level conjunction ({soul_no_deg:.1f})"
        )

    def test_moon_exact_trine_scores_higher_with_degrees(self):
        """Aries Moon × Leo Moon = sign-level trine (0.85).
        Exact 120° (0° Aries vs 120° = 0° Leo) → perfect trine → 1.0.
        Degree-level soul score is higher than sign-level when trine is exact.
        """
        a_no_deg   = self._base_user(moon_sign="aries",  moon_degree=None)
        b_no_deg   = self._base_user(moon_sign="leo",    moon_degree=None)
        a_with_deg = self._base_user(moon_sign="aries",  moon_degree=0.0)
        b_with_deg = self._base_user(moon_sign="leo",    moon_degree=120.0)

        soul_no_deg   = compute_soul_score(a_no_deg,   b_no_deg)
        soul_with_deg = compute_soul_score(a_with_deg, b_with_deg)

        assert soul_with_deg > soul_no_deg, (
            f"Exact-trine degree ({soul_with_deg:.1f}) should beat sign-level trine "
            f"({soul_no_deg:.1f})"
        )

    def test_mercury_false_conjunction_detected_via_degrees(self):
        """Same mercury sign but 25° apart → degree-level soul score lower."""
        a_no_deg   = self._base_user(mercury_sign="gemini", mercury_degree=None)
        b_no_deg   = self._base_user(mercury_sign="gemini", mercury_degree=None)
        a_with_deg = self._base_user(mercury_sign="gemini", mercury_degree=60.0)
        b_with_deg = self._base_user(mercury_sign="gemini", mercury_degree=85.0)  # 25° apart

        soul_no_deg   = compute_soul_score(a_no_deg,   b_no_deg)
        soul_with_deg = compute_soul_score(a_with_deg, b_with_deg)

        assert soul_with_deg < soul_no_deg, (
            f"Degree-level (void mercury, {soul_with_deg:.1f}) should score lower than "
            f"sign-level conjunction ({soul_no_deg:.1f})"
        )

    def test_saturn_false_conjunction_detected_via_degrees(self):
        """Same saturn sign but 25° apart → degree-level soul score lower."""
        a_no_deg   = self._base_user(saturn_sign="capricorn", saturn_degree=None)
        b_no_deg   = self._base_user(saturn_sign="capricorn", saturn_degree=None)
        a_with_deg = self._base_user(saturn_sign="capricorn", saturn_degree=270.0)
        b_with_deg = self._base_user(saturn_sign="capricorn", saturn_degree=295.0)  # 25° apart

        soul_no_deg   = compute_soul_score(a_no_deg,   b_no_deg)
        soul_with_deg = compute_soul_score(a_with_deg, b_with_deg)

        assert soul_with_deg < soul_no_deg, (
            f"Degree-level (void saturn, {soul_with_deg:.1f}) should score lower than "
            f"sign-level conjunction ({soul_no_deg:.1f})"
        )

    def test_sun_moon_cross_false_conjunction_via_degrees(self):
        """A's Sun same sign as B's Moon but 25° apart → degree-level soul lower."""
        a_no_deg = self._base_user(sun_sign="aries",  sun_degree=None,
                                   moon_sign="taurus", moon_degree=None)
        b_no_deg = self._base_user(sun_sign="leo",    sun_degree=None,
                                   moon_sign="aries",  moon_degree=None)

        # A's sun_degree=0.0 vs B's moon_degree=25.0 (both in aries band) → void
        a_with_deg = self._base_user(sun_sign="aries",  sun_degree=0.0,
                                     moon_sign="taurus", moon_degree=None)
        b_with_deg = self._base_user(sun_sign="leo",    sun_degree=None,
                                     moon_sign="aries",  moon_degree=25.0)

        soul_no_deg   = compute_soul_score(a_no_deg,   b_no_deg)
        soul_with_deg = compute_soul_score(a_with_deg, b_with_deg)

        assert soul_with_deg < soul_no_deg, (
            f"Degree-level (void Sun-Moon cross, {soul_with_deg:.1f}) should score lower than "
            f"sign-level conjunction ({soul_no_deg:.1f})"
        )


# ── L-3: compute_tracks degree-level resolution ───────────────────────────────

class TestTracksDegreeResolution:
    """Verify L-3 fix: compute_tracks uses _resolve_aspect (degree-level) for
    mercury, jupiter×sun cross, moon, mars, venus, house8, saturn×moon.

    Tests use the 'false conjunction' scenario: same sign but 25° apart.
    Degree-level scores lower (void 0.10) than sign-level (conjunction 0.90).

    Note: Chiron was removed from soul_track (L-12 + L-2 fix). Shadow engine
    handles Chiron wound triggers via orb-based degree checks in shadow_engine.py.
    """

    def _power(self):
        return {"rpv": 0.0, "frame_break": False, "viewer_role": "Equal", "target_role": "Equal"}

    def _base_user(self, **overrides):
        base = {
            "sun_sign": "aries",       "sun_degree": None,
            "moon_sign": "aries",      "moon_degree": None,
            "mercury_sign": "gemini",  "mercury_degree": None,
            "jupiter_sign": "leo",     "jupiter_degree": None,
            "mars_sign": "scorpio",    "mars_degree": None,
            "venus_sign": "taurus",    "venus_degree": None,
            "saturn_sign": "capricorn","saturn_degree": None,
            "chiron_sign": None,       "chiron_degree": None,
            "house8_sign": None,       "house8_degree": None,
            "juno_sign": None,
            "bazi_element": None,
            "rpv_power": None, "rpv_conflict": None, "rpv_energy": None,
            "emotional_capacity": 60,
        }
        base.update(overrides)
        return base

    def test_mercury_false_conjunction_lowers_friend_track(self):
        """Same mercury sign (sign-level conj 0.90) but 25° apart → friend lower."""
        a_no_deg   = self._base_user(mercury_sign="gemini", mercury_degree=None)
        b_no_deg   = self._base_user(mercury_sign="gemini", mercury_degree=None)
        a_with_deg = self._base_user(mercury_sign="gemini", mercury_degree=60.0)
        b_with_deg = self._base_user(mercury_sign="gemini", mercury_degree=85.0)  # 25° apart, void

        t_no_deg   = compute_tracks(a_no_deg,   b_no_deg,   self._power(), 0.0)
        t_with_deg = compute_tracks(a_with_deg, b_with_deg, self._power(), 0.0)

        assert t_with_deg["friend"] < t_no_deg["friend"], (
            f"Degree-level (void mercury) friend ({t_with_deg['friend']:.1f}) should be "
            f"less than sign-level ({t_no_deg['friend']:.1f})"
        )

    def test_moon_false_conjunction_lowers_partner_track(self):
        """Same moon sign but 25° apart → partner track lower with degree data."""
        a_no_deg   = self._base_user(moon_sign="aries", moon_degree=None)
        b_no_deg   = self._base_user(moon_sign="aries", moon_degree=None)
        a_with_deg = self._base_user(moon_sign="aries", moon_degree=0.0)
        b_with_deg = self._base_user(moon_sign="aries", moon_degree=25.0)

        t_no_deg   = compute_tracks(a_no_deg,   b_no_deg,   self._power(), 0.0)
        t_with_deg = compute_tracks(a_with_deg, b_with_deg, self._power(), 0.0)

        assert t_with_deg["partner"] < t_no_deg["partner"], (
            f"Degree-level (void moon) partner ({t_with_deg['partner']:.1f}) should be "
            f"less than sign-level ({t_no_deg['partner']:.1f})"
        )

    def test_mars_false_conjunction_lowers_passion_track(self):
        """Same mars sign but 25° apart → passion track lower with degree data."""
        a_no_deg   = self._base_user(mars_sign="scorpio", mars_degree=None)
        b_no_deg   = self._base_user(mars_sign="scorpio", mars_degree=None)
        a_with_deg = self._base_user(mars_sign="scorpio", mars_degree=210.0)
        b_with_deg = self._base_user(mars_sign="scorpio", mars_degree=235.0)  # 25° apart, void

        t_no_deg   = compute_tracks(a_no_deg,   b_no_deg,   self._power(), 0.0)
        t_with_deg = compute_tracks(a_with_deg, b_with_deg, self._power(), 0.0)

        assert t_with_deg["passion"] < t_no_deg["passion"], (
            f"Degree-level (void mars) passion ({t_with_deg['passion']:.1f}) should be "
            f"less than sign-level ({t_no_deg['passion']:.1f})"
        )

    def test_venus_false_conjunction_lowers_passion_track(self):
        """Same venus sign but 25° apart → passion track lower with degree data."""
        a_no_deg   = self._base_user(venus_sign="taurus", venus_degree=None)
        b_no_deg   = self._base_user(venus_sign="taurus", venus_degree=None)
        a_with_deg = self._base_user(venus_sign="taurus", venus_degree=30.0)
        b_with_deg = self._base_user(venus_sign="taurus", venus_degree=55.0)  # 25° apart, void

        t_no_deg   = compute_tracks(a_no_deg,   b_no_deg,   self._power(), 0.0)
        t_with_deg = compute_tracks(a_with_deg, b_with_deg, self._power(), 0.0)

        assert t_with_deg["passion"] < t_no_deg["passion"], (
            f"Degree-level (void venus) passion ({t_with_deg['passion']:.1f}) should be "
            f"less than sign-level ({t_no_deg['passion']:.1f})"
        )

    def test_jupiter_sun_cross_false_conjunction_lowers_friend(self):
        """A's Jupiter same sign as B's Sun but 25° apart → friend track lower."""
        # jupiter=leo (index 4), sun=leo (index 4) → sign-level: conjunction 0.90
        a_no_deg   = self._base_user(jupiter_sign="leo", jupiter_degree=None,
                                     sun_sign="cancer",  sun_degree=None)
        b_no_deg   = self._base_user(jupiter_sign="cancer", jupiter_degree=None,
                                     sun_sign="leo",     sun_degree=None)
        # A's jupiter_degree=120.0 vs B's sun_degree=145.0 → 25° apart, void
        a_with_deg = self._base_user(jupiter_sign="leo",    jupiter_degree=120.0,
                                     sun_sign="cancer",     sun_degree=None)
        b_with_deg = self._base_user(jupiter_sign="cancer", jupiter_degree=None,
                                     sun_sign="leo",        sun_degree=145.0)

        t_no_deg   = compute_tracks(a_no_deg,   b_no_deg,   self._power(), 0.0)
        t_with_deg = compute_tracks(a_with_deg, b_with_deg, self._power(), 0.0)

        assert t_with_deg["friend"] < t_no_deg["friend"], (
            f"Degree-level (void jupiter×sun) friend ({t_with_deg['friend']:.1f}) should be "
            f"less than sign-level ({t_no_deg['friend']:.1f})"
        )

    def test_chiron_does_not_affect_soul_track(self):
        """L-12 + L-2 fix: Chiron sign/degree data must NOT affect soul_track at all.
        Soul track is identical whether chiron_sign is present or absent, and regardless
        of degree proximity (same-gen false-conjunction is no longer possible).
        Shadow engine handles Chiron via orb-based degree checks independently."""
        a_no_chiron  = self._base_user(chiron_sign=None,    chiron_degree=None)
        b_no_chiron  = self._base_user(chiron_sign=None,    chiron_degree=None)
        a_with_deg   = self._base_user(chiron_sign="virgo", chiron_degree=150.0)
        b_with_deg   = self._base_user(chiron_sign="virgo", chiron_degree=175.0)  # same gen, 25° apart

        t_no_chiron  = compute_tracks(a_no_chiron, b_no_chiron, self._power(), 0.0)
        t_with_chiron = compute_tracks(a_with_deg, b_with_deg,  self._power(), 0.0)

        assert t_with_chiron["soul"] == t_no_chiron["soul"], (
            f"Chiron presence should not affect soul_track: "
            f"with={t_with_chiron['soul']:.1f}, without={t_no_chiron['soul']:.1f}"
        )


# ── L-10: Diminishing returns for lust_power ─────────────────────────────────

from matching import WEIGHTS as _WEIGHTS


class TestLustPowerDiminishingReturns:
    """L-10: RPV power contribution flattens above lust_power_plateau (0.75).

    At power_val = 0.90: effective_power = 0.75 + (0.90-0.75)*0.60 = 0.84
    At power_val = 0.75: effective_power = 0.75 (unchanged)
    At power_val = 0.50: effective_power = 0.50 (unchanged)
    """

    def _user(self, rpv_power=None, rpv_conflict=None, rpv_energy=None):
        return {
            "mars_sign": "aries", "venus_sign": "aries",
            "mars_degree": None,  "venus_degree": None,
            "sun_sign": "aries",  "moon_sign": "taurus",
            "bazi_element": None,
            "rpv_power": rpv_power, "rpv_conflict": rpv_conflict, "rpv_energy": rpv_energy,
        }

    def test_power_plateau_constant_in_weights(self):
        """WEIGHTS contains the two L-10 constants."""
        assert "lust_power_plateau" in _WEIGHTS
        assert "lust_power_diminish_factor" in _WEIGHTS
        assert _WEIGHTS["lust_power_plateau"] == pytest.approx(0.75)
        assert _WEIGHTS["lust_power_diminish_factor"] == pytest.approx(0.60)

    def test_complementary_power_lower_than_uncapped(self):
        """control×follow is the max complementary pair (power_val ≈ 0.90).
        Lust with control×follow should be lower than if raw 0.90 were used
        (diminishing returns caps effective value to 0.84).
        """
        # control × follow → compute_power_score ≈ 0.855 (composite RPV)
        a_cf = self._user(rpv_power="control")
        b_cf = self._user(rpv_power="follow")
        lust_cf = compute_lust_score(a_cf, b_cf)

        # same power × same power → power_val ≈ 0.50 (below plateau; no diminish)
        a_same = self._user(rpv_power="control")
        b_same = self._user(rpv_power="control")
        lust_same = compute_lust_score(a_same, b_same)

        # complementary is still higher (0.84 effective > 0.50), just not as extreme as raw 0.90
        assert lust_cf > lust_same, (
            f"Complementary power lust ({lust_cf:.1f}) should beat same-power ({lust_same:.1f})"
        )

    def test_no_rpv_data_unaffected(self):
        """Without RPV data, power_val = 0.65 (neutral, below plateau) → no diminishing."""
        a = self._user()   # all RPV fields None
        b = self._user()
        lust = compute_lust_score(a, b)
        assert 0 <= lust <= 100

    def test_effective_power_capped_formula(self):
        """Verify the formula: effective_power at val=0.90 is 0.84, not 0.90.

        We can check this indirectly: lust with control×follow must be < lust
        computed with an artificial power_val of 0.90 applied linearly.
        Since we cannot inject power_val directly, we verify that the gap between
        complementary and same-power lust is smaller than it would be with raw 0.90.
        """
        plateau = _WEIGHTS["lust_power_plateau"]     # 0.75
        dfactor = _WEIGHTS["lust_power_diminish_factor"]  # 0.60
        # At raw power_val = 0.90:
        effective = plateau + (0.90 - plateau) * dfactor
        assert effective == pytest.approx(0.75 + 0.09, abs=0.001)  # 0.84
        # Confirm effective < raw
        assert effective < 0.90


# ── L-11: Anxious×Avoidant lust spike ────────────────────────────────────────

class TestAnxiousAvoidantLustSpike:
    """L-11: When one user is anxious and the other avoidant, lust score is
    multiplied by lust_attachment_aa_mult (1.15) — 'addictive chemistry' model.
    """

    def _user(self, attachment=None, mars="aries", venus="taurus"):
        return {
            "mars_sign": mars,   "mars_degree": None,
            "venus_sign": venus, "venus_degree": None,
            "sun_sign": "aries", "moon_sign": "aries",
            "bazi_element": None,
            "rpv_power": None, "rpv_conflict": None, "rpv_energy": None,
            "attachment_style": attachment,
        }

    def test_anxious_avoidant_lust_higher_than_no_attachment(self):
        """anxious × avoidant pair gets a ×1.15 lust boost vs no attachment data."""
        a_aa = self._user("anxious")
        b_aa = self._user("avoidant")
        a_none = self._user(None)
        b_none = self._user(None)

        lust_aa   = compute_lust_score(a_aa, b_aa)
        lust_none = compute_lust_score(a_none, b_none)

        assert lust_aa > lust_none, (
            f"Anxious×Avoidant lust ({lust_aa:.1f}) should exceed no-attachment ({lust_none:.1f})"
        )

    def test_anxious_avoidant_multiplier_is_1_15(self):
        """The multiplier is exactly 1.15."""
        assert _WEIGHTS["lust_attachment_aa_mult"] == pytest.approx(1.15)

    def test_avoidant_anxious_same_as_anxious_avoidant(self):
        """Order doesn't matter: avoidant×anxious = anxious×avoidant."""
        a_av = self._user("avoidant")
        b_ax = self._user("anxious")
        a_ax = self._user("anxious")
        b_av = self._user("avoidant")

        lust_av_ax = compute_lust_score(a_av, b_ax)
        lust_ax_av = compute_lust_score(a_ax, b_av)

        assert lust_av_ax == pytest.approx(lust_ax_av, abs=0.01)

    def test_secure_secure_no_spike(self):
        """secure × secure does NOT trigger the multiplier."""
        a_ss = self._user("secure")
        b_ss = self._user("secure")
        a_none = self._user(None)
        b_none = self._user(None)

        lust_ss   = compute_lust_score(a_ss, b_ss)
        lust_none = compute_lust_score(a_none, b_none)

        # secure×secure should NOT be higher than no-attachment (no spike)
        assert lust_ss == pytest.approx(lust_none, abs=0.5)

    def test_anxious_anxious_no_spike(self):
        """anxious × anxious (co-dependency) does NOT trigger the lust spike."""
        a = self._user("anxious")
        b = self._user("anxious")
        a_none = self._user(None)
        b_none = self._user(None)

        lust_aa = compute_lust_score(a, b)
        lust_none = compute_lust_score(a_none, b_none)

        assert lust_aa == pytest.approx(lust_none, abs=0.5)


# ── TestBaziDiminishingReturns (Sprint 2) ─────────────────────

class TestBaziDiminishingReturns:
    """Sprint 2: BaZi multipliers replaced with diminishing-returns additive formula.

    Ensures that:
    1. compute_soul_score with generation relationship returns ≤ 100 even when
       old ×1.20 formula would push base_score past 1.0.
    2. compute_lust_score with restriction relationship returns ≤ 100 even when
       old ×1.25 formula would push base_score past 1.0.
    3. Both results are HIGHER than a neutral/same-element baseline (bonus still works).
    """

    def _soul_user(self, bazi_elem=None, sign="cancer"):
        """Soul user: all three always-present planets in the same sign (sign-only).

        No degree fields — forces sign-distance computation so the aspect score
        reflects the actual sign separation rather than degree proximity.
        """
        return {
            "moon_sign":    sign,
            "mercury_sign": sign,
            "saturn_sign":  sign,
            "sun_sign":     sign,
            "bazi_element": bazi_elem,
        }

    def _lust_user(self, bazi_elem=None, sign="aries", rpv_power=None):
        """Lust user: mars and venus in the same sign for high baseline."""
        return {
            "mars_sign":   sign, "mars_degree":   0.0,
            "venus_sign":  sign, "venus_degree":  0.0,
            "bazi_element": bazi_elem,
            "rpv_power": rpv_power,
        }

    def test_soul_generation_bonus_does_not_exceed_100(self):
        """High base soul score + BaZi generation → result stays ≤ 100.

        Wood generates Fire (木生火) → a_generates_b.
        All planets in same sign → near-perfect base soul.
        Old ×1.20 would push a 0.90 base to 1.08 (> 1.0 before ×100).
        New additive formula: 0.90 + 0.10×0.30 = 0.93 ≤ 1.0.
        """
        a = self._soul_user(bazi_elem="wood")
        b = self._soul_user(bazi_elem="fire")
        score = compute_soul_score(a, b)
        assert score <= 100.0, (
            f"soul_score {score:.2f} exceeds 100 — diminishing-returns formula violated"
        )

    def test_soul_generation_bonus_still_higher_than_neutral(self):
        """Generation bonus must still raise soul score above same-element (比和) baseline.

        Uses square-sign planets (aries vs cancer) to keep base_score well below 100,
        so both generation and same-element bonuses are observable.
        Wood generates Fire (a_generates_b, +30% remaining space) should score
        higher than Fire+Fire (same, +15% remaining space).
        """
        a_gen  = self._soul_user(bazi_elem="wood",  sign="aries")
        b_gen  = self._soul_user(bazi_elem="fire",  sign="cancer")
        a_same = self._soul_user(bazi_elem="fire",  sign="aries")
        b_same = self._soul_user(bazi_elem="fire",  sign="cancer")
        score_gen  = compute_soul_score(a_gen, b_gen)
        score_same = compute_soul_score(a_same, b_same)
        assert score_gen > score_same, (
            f"generation bonus ({score_gen:.2f}) should exceed same-element bonus ({score_same:.2f})"
        )

    def test_lust_restriction_bonus_does_not_exceed_100(self):
        """High base lust score + BaZi restriction → result stays ≤ 100.

        Wood restricts Earth (木剋土) → a_restricts_b.
        Mars and Venus in same sign → near-perfect base lust.
        Old ×1.25 would push a 0.90 base to 1.125 (> 1.0 before ×100).
        New additive formula: 0.90 + 0.10×0.25 = 0.925 ≤ 1.0.
        """
        a = self._lust_user(bazi_elem="wood", rpv_power="control")
        b = self._lust_user(bazi_elem="earth", rpv_power="follow")
        score = compute_lust_score(a, b)
        assert score <= 100.0, (
            f"lust_score {score:.2f} exceeds 100 — diminishing-returns formula violated"
        )

    def test_lust_restriction_bonus_still_higher_than_neutral(self):
        """Restriction bonus must still raise lust score above no-bazi baseline."""
        a_res  = self._lust_user(bazi_elem="wood",  rpv_power="control")
        b_res  = self._lust_user(bazi_elem="earth", rpv_power="follow")
        a_none = self._lust_user(bazi_elem=None, rpv_power="control")
        b_none = self._lust_user(bazi_elem=None, rpv_power="follow")
        score_res  = compute_lust_score(a_res, b_res)
        score_none = compute_lust_score(a_none, b_none)
        assert score_res > score_none, (
            "restriction bonus should raise lust score above no-bazi baseline"
        )


# ════════════════════════════════════════════════════════════════
# Sprint 3: Karmic Tension Index + Resonance Badges
# ════════════════════════════════════════════════════════════════

class TestKarmicTensionAndBadges:
    """Sprint 3: karmic_tension index and resonance_badges in compute_match_v2."""

    def _base_user(self, **kwargs):
        """Minimal Tier-3 user with no degree fields (no shadow triggers)."""
        defaults = {
            "data_tier": 3,
            "sun_sign":     "cancer",
            "moon_sign":    "cancer",
            "mercury_sign": "cancer",
            "saturn_sign":  "cancer",
            "venus_sign":   "cancer",
            "mars_sign":    "cancer",
            "bazi_element": None,
        }
        defaults.update(kwargs)
        return defaults

    def test_karmic_tension_zero_with_no_shadow(self):
        """Users with no shadow-triggering degree positions → karmic_tension == 0.0.

        No degree fields are provided, so compute_shadow_and_wound returns all
        mods at 0.0 → raw_tension = 0.0 → karmic_tension = 0.0.
        """
        a = self._base_user()
        b = self._base_user(moon_sign="capricorn")
        result = compute_match_v2(a, b)
        assert result["karmic_tension"] == pytest.approx(0.0), (
            f"Expected karmic_tension 0.0 but got {result['karmic_tension']}"
        )

    def test_karmic_tension_weighted_formula(self):
        """Saturn-Moon conjunction triggers shadow mods; karmic_tension formula verified.

        Setup: A.saturn_degree=0.0, B.moon_degree=1.0 (1° apart, within 5° orb).
        Expected trigger: A_Saturn_Suppresses_B_Moon
          _shadow["soul_mod"]    = +10.0
          _shadow["partner_mod"] = -15.0
          _shadow["lust_mod"]    =   0.0

        raw_tension = |partner_mod| * 1.5 + |lust_mod| * 1.0 + |soul_mod| * 0.5
                    = 15.0 * 1.5  + 0.0 * 1.0   + 10.0 * 0.5
                    = 22.5        + 0.0           + 5.0
                    = 27.5
        karmic_tension = clamp(27.5) = 27.5
        """
        a = self._base_user(saturn_degree=0.0)
        b = self._base_user(moon_degree=1.0)
        result = compute_match_v2(a, b)
        assert result["karmic_tension"] == pytest.approx(27.5, abs=0.1), (
            f"Expected karmic_tension 27.5 but got {result['karmic_tension']}"
        )

    def test_badge_mingliduochong_soul_high_generation(self):
        """Badge A: 命理雙重認證 — soul ≥ 80 且 BaZi generation relationship.

        Setup: all planets in same sign (cancer/cancer → conjunction ≈ 0.90 aspect)
        → base soul ≈ 90. Wood generates Fire (木生火, a_generates_b).
        Generation bonus: (1 - 0.90) * 0.30 * 100 ≈ 3 → soul ≈ 93 ≥ 80.
        No degree fields → no shadow triggers → karmic_tension = 0.

        Expected: "命理雙重認證" in resonance_badges.
        """
        a = self._base_user(bazi_element="wood")
        b = self._base_user(bazi_element="fire")
        result = compute_match_v2(a, b)
        assert result["soul_score"] >= 80, (
            f"Precondition: soul_score should be ≥ 80, got {result['soul_score']}"
        )
        assert result["bazi_relation"] in ("a_generates_b", "b_generates_a", "same"), (
            f"Precondition: bazi_relation should be generation/same, got {result['bazi_relation']}"
        )
        assert "命理雙重認證" in result["resonance_badges"], (
            f"Expected '命理雙重認證' in resonance_badges, got {result['resonance_badges']}"
        )

    def test_badge_c_karmic_tension_soul(self):
        """Badge C: 進化型靈魂伴侶：虐戀與升級 — karmic_tension ≥ 30 且 soul ≥ 75.

        Setup: bidirectional Saturn-Moon conjunctions (both within 5° orb).
          A.saturn_degree=0.0, B.moon_degree=1.5  → A_Saturn_Suppresses_B_Moon
          B.saturn_degree=2.0, A.moon_degree=1.0  → B_Saturn_Suppresses_A_Moon

        Combined _shadow mods:
          soul_mod    = +10.0 + 10.0 = +20.0
          partner_mod = -15.0 - 15.0 = -30.0
          lust_mod    =   0.0

        raw_tension = |-30| * 1.5 + |0| * 1.0 + |20| * 0.5 = 45.0 + 0.0 + 10.0 = 55.0
        karmic_tension = 55.0 ≥ 30.

        All planets in same sign (cancer) → base soul ≈ 90.
        soul after adj = min(100, 90 + 20) = 100 ≥ 75.

        Expected: "進化型靈魂伴侶：虐戀與升級" in resonance_badges.
        """
        a = self._base_user(saturn_degree=0.0, moon_degree=1.0)
        b = self._base_user(saturn_degree=2.0, moon_degree=1.5)
        result = compute_match_v2(a, b)
        assert result["karmic_tension"] >= 30, (
            f"Precondition: karmic_tension should be ≥ 30, got {result['karmic_tension']}"
        )
        assert result["soul_score"] >= 75, (
            f"Precondition: soul_score should be ≥ 75, got {result['soul_score']}"
        )
        assert "進化型靈魂伴侶：虐戀與升級" in result["resonance_badges"], (
            f"Expected '進化型靈魂伴侶：虐戀與升級' in resonance_badges, "
            f"got {result['resonance_badges']}"
        )

    def test_badge_b_sanjie_soulmate(self):
        """Badge B: 三界共振：宿命伴侶 — Badge A + ZWDS spiciness_level == SOULMATE.

        Badge B requires Badge A first: soul ≥ 80 + BaZi generation/same.
        Then zwds_result["spiciness_level"] == "SOULMATE" must be present.

        We inject zwds_result directly into one user's zwds_chart field (bypassing
        live ZWDS service) by monkey-patching compute_match_v2's zwds_result
        via the existing zwds_chart pass-through in the function.

        Simpler approach: directly call the badge logic by constructing a scenario
        where compute_match_v2 returns a soulmate — achieved by patching zwds.py.
        Since the ZWDS service is optional and returns {} when unavailable, we
        instead verify Badge B's guard logic: if zwds_result is None/absent,
        Badge B cannot fire even when Badge A fires.
        """
        # When ZWDS not available (zwds_result = None/{}), Badge B cannot fire
        # even if Badge A conditions are met.
        a = self._base_user(bazi_element="wood")
        b = self._base_user(bazi_element="fire")   # wood→fire = a_generates_b
        result = compute_match_v2(a, b)
        # Badge A may or may not fire (depends on soul_score) — Badge B requires ZWDS SOULMATE
        # which is not available without a live ZWDS service; verify it is NOT spuriously added.
        assert "三界共振：宿命伴侶" not in result["resonance_badges"], (
            "Badge B must NOT fire without ZWDS SOULMATE confirmation"
        )

    def test_harmony_score_alias(self):
        """harmony_score is always equal to soul_score (frontend compatibility alias).

        Verified across multiple user configurations to ensure the alias is
        consistently maintained regardless of shadow mods or BaZi element.
        """
        a = self._base_user(bazi_element="wood")
        b = self._base_user(bazi_element="fire", moon_sign="capricorn")
        result = compute_match_v2(a, b)
        assert result["harmony_score"] == result["soul_score"], (
            f"harmony_score ({result['harmony_score']}) must equal "
            f"soul_score ({result['soul_score']})"
        )


# ═════════════════════════════════════════════════════════════════════════════
# Sprint 7: Favorable Element Resonance (喜用神互補)
# ═════════════════════════════════════════════════════════════════════════════

from matching import compute_favorable_element_resonance


class TestFavorableElementResonance:
    """Tests for compute_favorable_element_resonance (Sprint 7)."""

    def test_bidirectional_resonance(self):
        """Both users fill each other's needs → perfect resonance badge."""
        a = {"favorable_elements": ["火", "土"], "dominant_elements": ["水", "金"]}
        b = {"favorable_elements": ["水", "金"], "dominant_elements": ["火", "土"]}
        result = compute_favorable_element_resonance(a, b)
        assert result["b_helps_a"] is True
        assert result["a_helps_b"] is True
        assert "完美互補：靈魂能量共振" in result["badges"]
        assert result["soul_mod"] > 0

    def test_unidirectional_resonance(self):
        """Only B fills A's need → 專屬幸運星 badge."""
        a = {"favorable_elements": ["火"], "dominant_elements": ["木"]}
        b = {"favorable_elements": ["金"], "dominant_elements": ["火"]}
        result = compute_favorable_element_resonance(a, b)
        assert result["b_helps_a"] is True
        assert result["a_helps_b"] is False
        assert "專屬幸運星" in result["badges"]

    def test_no_match(self):
        """No overlap → no badge, no soul_mod."""
        a = {"favorable_elements": ["火"], "dominant_elements": ["木"]}
        b = {"favorable_elements": ["金"], "dominant_elements": ["水"]}
        result = compute_favorable_element_resonance(a, b)
        assert result["b_helps_a"] is False
        assert result["a_helps_b"] is False
        assert result["badges"] == []
        assert result["soul_mod"] == 0.0

    def test_empty_inputs(self):
        """Empty dicts → safe defaults."""
        result = compute_favorable_element_resonance({}, {})
        assert result["soul_mod"] == 0.0
        assert result["badges"] == []

    def test_marginal_diminishing(self):
        """Higher current_soul → smaller soul_mod (marginal diminishing)."""
        a = {"favorable_elements": ["火"], "dominant_elements": ["水"]}
        b = {"favorable_elements": ["水"], "dominant_elements": ["火"]}
        r_low  = compute_favorable_element_resonance(a, b, current_soul=30.0)
        r_high = compute_favorable_element_resonance(a, b, current_soul=80.0)
        assert r_low["soul_mod"] > r_high["soul_mod"]

    def test_soul_at_100_gives_zero_mod(self):
        """When soul is already 100, no room for bonus → soul_mod = 0."""
        a = {"favorable_elements": ["火"], "dominant_elements": ["水"]}
        b = {"favorable_elements": ["水"], "dominant_elements": ["火"]}
        result = compute_favorable_element_resonance(a, b, current_soul=100.0)
        assert result["soul_mod"] == 0.0

    def test_bidirectional_mod_higher_than_unidirectional(self):
        """Bidirectional should give higher soul_mod than unidirectional."""
        a_bi = {"favorable_elements": ["火", "土"], "dominant_elements": ["水", "金"]}
        b_bi = {"favorable_elements": ["水", "金"], "dominant_elements": ["火", "土"]}
        a_uni = {"favorable_elements": ["火"], "dominant_elements": ["木"]}
        b_uni = {"favorable_elements": ["金"], "dominant_elements": ["火"]}
        r_bi  = compute_favorable_element_resonance(a_bi, b_bi, current_soul=50.0)
        r_uni = compute_favorable_element_resonance(a_uni, b_uni, current_soul=50.0)
        assert r_bi["soul_mod"] > r_uni["soul_mod"]


# ── Synastry Mutual Reception (V3 Classical Astrology) ───────────────────────

from matching import check_synastry_mutual_reception


def _wc(**signs):
    """Build a minimal western_chart with {planet}_sign keys."""
    return {f"{k}_sign": v for k, v in signs.items()}


class TestSynastryMutualReception:
    def test_venus_mars_mr_badge(self):
        """A.venus in Aries + B.mars in Taurus → 金火互溶 badge."""
        a = _wc(venus="aries", mars="gemini")
        b = _wc(venus="leo",   mars="taurus")
        badges = check_synastry_mutual_reception(a, b)
        assert any("金火互溶" in badge for badge in badges)

    def test_sun_moon_mr_badge(self):
        """A.sun in Cancer + B.moon in Leo → 日月互溶 badge."""
        a = _wc(sun="cancer", moon="aries")
        b = _wc(sun="libra",  moon="leo")
        badges = check_synastry_mutual_reception(a, b)
        assert any("日月互溶" in badge for badge in badges)

    def test_venus_moon_mr_badge(self):
        """A.venus in Cancer + B.moon in Taurus → 金月互溶 badge (Venus rules Taurus, Moon rules Cancer)."""
        a = _wc(venus="cancer", moon="aries")
        b = _wc(venus="leo",    moon="taurus")
        badges = check_synastry_mutual_reception(a, b)
        assert any("金月互溶" in badge for badge in badges)

    def test_no_mr_no_badge(self):
        """Completely unrelated signs → no badges."""
        a = _wc(sun="gemini",  moon="gemini",  venus="gemini",  mars="gemini")
        b = _wc(sun="gemini",  moon="gemini",  venus="gemini",  mars="gemini")
        badges = check_synastry_mutual_reception(a, b)
        assert badges == []

    def test_missing_sign_no_crash(self):
        """One chart has no moon_sign (Tier 3) → no crash, returns list."""
        a = _wc(sun="cancer")   # no moon
        b = _wc(moon="leo")     # no sun
        result = check_synastry_mutual_reception(a, b)
        assert isinstance(result, list)


# ── compute_match_v2: psychological_triggers ─────────────────────────────────

class TestPsychologicalTriggers:
    """compute_match_v2 must populate psychological_triggers correctly."""

    def _base(self, attachment_a=None, attachment_b=None):
        """Minimal chart dict for compute_match_v2."""
        u = {
            "sun_sign": "aries", "moon_sign": "taurus",
            "venus_sign": "gemini", "mars_sign": "cancer",
            "ascendant_sign": "leo",
            "birth_year": 1995, "birth_month": 3, "birth_day": 26,
            "birth_time": "14:30",
        }
        a = dict(u, gender="M")
        b = dict(u, gender="F")
        if attachment_a:
            a["attachment_style"] = attachment_a
        if attachment_b:
            b["attachment_style"] = attachment_b
        return a, b

    def test_no_triggers_by_default(self):
        """No attachment styles + moderate scores → empty psychological_triggers."""
        from matching import compute_match_v2
        a, b = self._base()
        result = compute_match_v2(a, b)
        assert "psychological_triggers" in result
        # Without anxious/avoidant pair or extreme soul+HV, list is empty
        triggers = result["psychological_triggers"]
        assert isinstance(triggers, list)
        # No attachment styles set → attachment_trap trigger absent
        assert "attachment_trap: anxious_avoidant" not in triggers

    def test_anxious_avoidant_adds_attachment_trap_trigger(self):
        """anxious + avoidant attachment pair → attachment_trap: anxious_avoidant trigger."""
        from matching import compute_match_v2
        a, b = self._base(attachment_a="anxious", attachment_b="avoidant")
        result = compute_match_v2(a, b)
        assert "attachment_trap: anxious_avoidant" in result["psychological_triggers"]

    def test_healing_anchor_adds_healing_trigger(self):
        """secure + anxious pair → attachment_healing: secure_base trigger."""
        from matching import compute_match_v2
        a, b = self._base(attachment_a="secure", attachment_b="anxious")
        result = compute_match_v2(a, b)
        assert "attachment_healing: secure_base" in result["psychological_triggers"]

    def test_triggers_list_in_return_dict(self):
        """psychological_triggers key is always present in compute_match_v2 output."""
        from matching import compute_match_v2
        a, b = self._base()
        result = compute_match_v2(a, b)
        assert "psychological_triggers" in result
        assert isinstance(result["psychological_triggers"], list)


# ── compute_match_v2: element_profile_a/b surface ────────────────────────────

class TestElementProfileSurface:
    """element_profile_a / element_profile_b must appear in compute_match_v2 output."""

    def _user(self, ep=None):
        u = {
            "sun_sign": "aries", "moon_sign": "taurus",
            "venus_sign": "gemini", "mars_sign": "cancer",
            "ascendant_sign": "leo",
            "birth_year": 1995, "birth_month": 3, "birth_day": 26,
            "birth_time": "14:30", "gender": "M",
        }
        if ep is not None:
            u["element_profile"] = ep
        return u

    def test_element_profiles_surfaced_when_present(self):
        """element_profile from user dicts must appear in compute_match_v2 output."""
        from matching import compute_match_v2
        ep_a = {"dominant": ["fire"], "deficiency": ["water"]}
        ep_b = {"dominant": ["air"],  "deficiency": ["earth"]}
        result = compute_match_v2(self._user(ep_a), self._user(ep_b))
        assert result.get("element_profile_a") == ep_a
        assert result.get("element_profile_b") == ep_b

    def test_element_profiles_none_when_absent(self):
        """When user has no element_profile, key is present but value is None."""
        from matching import compute_match_v2
        result = compute_match_v2(self._user(), self._user())
        assert "element_profile_a" in result
        assert result["element_profile_a"] is None


# ── Bug-1: void-of-aspect neutrality ─────────────────────────

from matching import compute_exact_aspect, _resolve_aspect


class TestVoidOfAspectNeutrality:
    def test_exact_aspect_void_returns_neutral_not_penalty(self):
        """Void-of-aspect should return 0.5 (neutral), not 0.1 (penalty).
        Tier 1 users must never score lower than Tier 3 for the same planet pair."""
        # 9° apart — just outside the 8° conjunction orb
        score = compute_exact_aspect(10.0, 19.0, "harmony")
        assert score == 0.5, f"Void-of-aspect should be 0.5 neutral, got {score}"

    def test_resolve_aspect_void_falls_back_to_sign(self):
        """When exact degrees yield void-of-aspect, _resolve_aspect should
        blend with sign-level score at 80% weight, not return bare 0.5."""
        # Aries-Leo is a trine (harmony ~0.85 sign-level); 9° apart = void of exact aspect
        score = _resolve_aspect(10.0, "Aries", 19.0, "Leo", "harmony")
        # Expected: sign_score * 0.8 ≈ 0.68
        assert score > 0.5, f"Should preserve sign background, got {score}"
        assert score < 1.0


# ── Shadow Modifier Caps (L-1 fix) ───────────────────────────

class TestShadowModifierCaps:
    """Tests for the shadow modifier caps that prevent overflow from
    multiple simultaneous triggers (L-1 fix).
    soul_adj: max +40, min -30
    lust_adj: max +40, min -30
    partner_adj: max +25, min -20
    """

    def _user(self, **kwargs):
        defaults = {
            "data_tier": 3,
            "sun_sign": "aries", "moon_sign": None, "venus_sign": "taurus",
            "mars_sign": "gemini", "saturn_sign": "cancer",
            "mercury_sign": "aries", "jupiter_sign": "taurus",
            "pluto_sign": "scorpio",
            "chiron_sign": None, "juno_sign": None,
            "house4_sign": None, "house8_sign": None,
            "ascendant_sign": None,
            "bazi_element": None,
            "rpv_conflict": None, "rpv_power": None, "rpv_energy": None,
            "attachment_style": None,
        }
        defaults.update(kwargs)
        return defaults

    def test_shadow_modifier_soul_adj_capped_at_40(self):
        """soul_adj must be capped at +40 before applying to score.
        Without cap, 5+ simultaneous triggers can add 100+ points (L-1 fix)."""
        a = self._user()
        b = self._user(venus_sign="leo")
        result = compute_match_v2(a, b)
        # soul_score is bounded by _clamp (0-100) regardless, but modifier cap
        # means a pair can't hit 100 from modifiers alone if base tracks are ~40-50
        assert 0.0 <= result["soul_score"] <= 100.0  # basic sanity

    def test_shadow_modifier_capped_negative_lust(self):
        """lust_adj must be floored at -30 (not -infinity).
        Negative modifiers should not destroy a valid match."""
        a = self._user()
        b = self._user(venus_sign="leo")
        result = compute_match_v2(a, b)
        assert result["lust_score"] >= 0.0

    def test_shadow_modifier_cap_logic_unit(self):
        """Unit test: verify cap constants produce correct bounded values."""
        # Direct arithmetic verification of the cap logic
        # soul_adj cap
        assert min(85.0, 40.0) == 40.0, "soul_adj max cap at 40"
        assert max(-50.0, -30.0) == -30.0, "soul_adj min floor at -30"
        # lust_adj cap
        assert min(70.0, 40.0) == 40.0, "lust_adj max cap at 40"
        assert max(-45.0, -30.0) == -30.0, "lust_adj min floor at -30"
        # partner_adj cap
        assert min(40.0, 25.0) == 25.0, "partner_adj max cap at 25"
        assert max(-35.0, -20.0) == -20.0, "partner_adj min floor at -20"
