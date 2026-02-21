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
        """When house8_sign is present and matching (conjunction), score should be higher."""
        a_no  = self._user(house8=None)
        b_no  = self._user(house8=None)
        a_yes = self._user(house8="scorpio")
        b_yes = self._user(house8="scorpio")
        score_without = compute_lust_score(a_no, b_no)
        score_with    = compute_lust_score(a_yes, b_yes)
        # conjunction = 0.90, 0.0 < 0.90 → having house8 raises score
        assert score_with > score_without

    def test_power_control_follow_increases_lust(self):
        """Complementary RPV power → higher power_fit → higher lust score."""
        a_comp = self._user(rpv_power="control")
        b_comp = self._user(rpv_power="follow")
        a_same = self._user(rpv_power="control")
        b_same = self._user(rpv_power="control")
        assert compute_lust_score(a_comp, b_comp) > compute_lust_score(a_same, b_same)


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

    def test_useful_god_complement_summer_winter(self):
        """Summer (month 6) ↔ Winter (month 12) → useful_god_complement = 1.0."""
        a = self._user(birth_month=6)
        b = self._user(birth_month=12)
        result = compute_match_v2(a, b)
        assert result["useful_god_complement"] == pytest.approx(1.0)

    def test_useful_god_complement_same_season(self):
        """Same season → useful_god_complement = 0.0."""
        a = self._user(birth_month=6)
        b = self._user(birth_month=7)
        result = compute_match_v2(a, b)
        assert result["useful_god_complement"] == pytest.approx(0.0)

    def test_useful_god_complement_missing_month(self):
        """No birth_month → useful_god_complement = 0.0 (neutral)."""
        a = self._user()
        b = self._user()
        result = compute_match_v2(a, b)
        assert result["useful_god_complement"] == pytest.approx(0.0)

    def test_summer_winter_raises_soul_track(self):
        """Summer ↔ Winter complement (1.0) should give higher soul track
        than same-season pair (0.0)."""
        a_sw = self._user(birth_month=6)
        b_sw = self._user(birth_month=12)
        a_ss = self._user(birth_month=6)
        b_ss = self._user(birth_month=7)
        soul_sw = compute_match_v2(a_sw, b_sw)["tracks"]["soul"]
        soul_ss = compute_match_v2(a_ss, b_ss)["tracks"]["soul"]
        assert soul_sw > soul_ss


# ── bazi.py: seasonal complement functions ────────────────────

from bazi import get_season_type, compute_bazi_season_complement


class TestGetSeasonType:
    def test_summer_months(self):
        for m in (5, 6, 7):
            assert get_season_type(m) == "hot"

    def test_winter_months(self):
        for m in (11, 12, 1):
            assert get_season_type(m) == "cold"

    def test_spring_months(self):
        for m in (2, 3, 4):
            assert get_season_type(m) == "warm"

    def test_autumn_months(self):
        for m in (8, 9, 10):
            assert get_season_type(m) == "cool"


class TestBaziSeasonComplement:
    def test_hot_cold_is_perfect(self):
        """Summer ↔ Winter = 1.0 (水火既濟)."""
        assert compute_bazi_season_complement(6, 12) == pytest.approx(1.0)
        assert compute_bazi_season_complement(12, 6) == pytest.approx(1.0)

    def test_warm_cool_is_good(self):
        """Spring ↔ Autumn = 0.8 (金木相成)."""
        assert compute_bazi_season_complement(3, 9) == pytest.approx(0.8)
        assert compute_bazi_season_complement(9, 3) == pytest.approx(0.8)

    def test_extreme_moderate_is_partial(self):
        """Summer ↔ Autumn = 0.5 (partial)."""
        assert compute_bazi_season_complement(6, 9) == pytest.approx(0.5)

    def test_same_season_is_zero(self):
        """Same season = 0.0 (no complement)."""
        assert compute_bazi_season_complement(5, 7) == pytest.approx(0.0)
        assert compute_bazi_season_complement(1, 12) == pytest.approx(0.0)

    def test_symmetric(self):
        """Complement score is symmetric: A↔B == B↔A."""
        assert compute_bazi_season_complement(6, 12) == \
               compute_bazi_season_complement(12, 6)
