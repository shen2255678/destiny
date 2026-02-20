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
    ASPECT_SCORES,
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
        """Aries (0) and Cancer (3) → square = 0.50"""
        assert compute_sign_aspect("aries", "cancer") == pytest.approx(0.50)

    def test_opposition_6_houses_apart(self):
        """Aries (0) and Libra (6) → opposition = 0.60"""
        assert compute_sign_aspect("aries", "libra") == pytest.approx(0.60)

    def test_wraps_correctly_beyond_6(self):
        """Distance 7 wraps to 5 (quincunx = 0.65)"""
        # Scorpio(7) vs Aries(0): distance=7, wraps to 12-7=5 → quincunx
        assert compute_sign_aspect("scorpio", "aries") == pytest.approx(0.65)

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
        """Perfect sign matches → glitch close to 0.90"""
        a = {"mars_sign": "aries", "saturn_sign": "leo"}
        b = {"mars_sign": "aries", "saturn_sign": "leo"}
        score = compute_glitch_score(a, b)
        # mars(0.90) + saturn(0.90) + mars_a vs sat_b(0.90) + mars_b vs sat_a(0.90)
        # but aries vs leo = trine(4) = 0.85
        expected = (
            compute_sign_aspect("aries", "aries") * 0.25 +
            compute_sign_aspect("leo", "leo") * 0.25 +
            compute_sign_aspect("aries", "leo") * 0.25 +  # mars_a vs sat_b
            compute_sign_aspect("aries", "leo") * 0.25    # mars_b vs sat_a
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
