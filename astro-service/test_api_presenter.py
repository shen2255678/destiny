# -*- coding: utf-8 -*-
"""
DESTINY — Security Audit Tests for api_presenter.py

Ensures that the DTO sanitization layer NEVER exposes raw astrology,
BaZi, or ZWDS data to the frontend.

Tests cover:
  - format_safe_match_response strips all sensitive keys
  - format_safe_onboard_response strips all sensitive keys
  - tension_level is always 1-5
  - track scores are always integers
  - No sensitive Chinese astrology terms in response
  - assert_no_sensitive_data utility works correctly
"""
import pytest

from api_presenter import (
    format_safe_match_response,
    format_safe_onboard_response,
    assert_no_sensitive_data,
    _karmic_tension_to_level,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _raw_match_data():
    """Simulated output from compute_match_v2()."""
    return {
        "lust_score": 72.3,
        "soul_score": 85.5,
        "harmony_score": 85.5,
        "karmic_tension": 45.2,
        "resonance_badges": ["命理雙重認證", "進化型靈魂伴侶：虐戀與升級"],
        "power": {
            "rpv": 15.0,
            "frame_break": True,
            "viewer_role": "Dom",
            "target_role": "Sub",
        },
        "tracks": {
            "friend": 62.3,
            "passion": 78.9,
            "partner": 55.1,
            "soul": 88.7,
        },
        "primary_track": "soul",
        "quadrant": "soulmate",
        "labels": ["靈魂軌"],
        "bazi_relation": "a_generates_b",
        "bazi_day_branch_relation": "neutral",
        "useful_god_complement": 0.75,
        "zwds": {
            "spiciness_level": "HIGH_VOLTAGE",
            "track_mods": {"friend": 1.0, "passion": 1.2, "partner": 0.8, "soul": 1.1},
            "rpv_modifier": 5,
            "defense_a": ["擎羊衝命"],
            "defense_b": [],
            "layered_analysis": {"western": "some data"},
        },
        "spiciness_level": "HIGH_VOLTAGE",
        "psychological_tags": ["Anxious_Avoidant_Trap", "A_Sun_Triggers_B_Chiron"],
        "high_voltage": True,
        "defense_mechanisms": {
            "viewer": ["擎羊衝命"],
            "target": [],
        },
        "layered_analysis": {"western": "secret_data"},
    }


def _psychology_profile():
    """Simulated output from extract_ideal_partner_profile()."""
    return {
        "relationship_dynamic": "high_voltage",
        "psychological_needs": ["渴望被完全理解", "需要深度靈魂連結"],
        "favorable_elements": ["水", "木"],
        "attachment_style": "anxious",
        "target_western_signs": ["cancer", "pisces"],
        "target_bazi_elements": ["水", "木"],
        "zwds_partner_tags": ["渴望溫柔陪伴"],
    }


# ═════════════════════════════════════════════════════════════════════════════
# Test: tension_level conversion
# ═════════════════════════════════════════════════════════════════════════════

class TestKarmicTensionToLevel:
    def test_zero(self):
        assert _karmic_tension_to_level(0) == 1

    def test_low(self):
        assert _karmic_tension_to_level(15) == 1

    def test_medium(self):
        assert _karmic_tension_to_level(45) == 3

    def test_high(self):
        assert _karmic_tension_to_level(75) == 4

    def test_max(self):
        assert _karmic_tension_to_level(100) == 5

    def test_negative_clamped(self):
        assert _karmic_tension_to_level(-10) == 1

    def test_over_100_clamped(self):
        assert _karmic_tension_to_level(150) == 5


# ═════════════════════════════════════════════════════════════════════════════
# Test: format_safe_match_response
# ═════════════════════════════════════════════════════════════════════════════

class TestFormatSafeMatchResponse:

    def test_returns_success_status(self):
        result = format_safe_match_response(_raw_match_data(), "test report")
        assert result["status"] == "success"

    def test_harmony_score_is_integer(self):
        result = format_safe_match_response(_raw_match_data())
        assert isinstance(result["data"]["harmony_score"], int)
        assert result["data"]["harmony_score"] == 86  # round(85.5)

    def test_tension_level_in_range(self):
        result = format_safe_match_response(_raw_match_data())
        level = result["data"]["tension_level"]
        assert 1 <= level <= 5

    def test_track_scores_are_integers(self):
        result = format_safe_match_response(_raw_match_data())
        for key, val in result["data"]["tracks"].items():
            assert isinstance(val, int), f"Track '{key}' should be int, got {type(val)}"

    def test_badges_preserved(self):
        result = format_safe_match_response(_raw_match_data())
        assert "命理雙重認證" in result["data"]["badges"]

    def test_llm_report_included(self):
        result = format_safe_match_response(_raw_match_data(), "這是一段深刻的關係...")
        assert result["data"]["ai_insight_report"] == "這是一段深刻的關係..."

    def test_no_sensitive_keys(self):
        result = format_safe_match_response(_raw_match_data(), "report text")
        assert_no_sensitive_data(result)

    def test_no_raw_bazi_data(self):
        result = format_safe_match_response(_raw_match_data())
        assert "bazi_relation" not in result["data"]
        assert "bazi" not in result["data"]

    def test_no_zwds_data(self):
        result = format_safe_match_response(_raw_match_data())
        assert "zwds" not in result["data"]
        assert "spiciness_level" not in result["data"]

    def test_no_power_data(self):
        result = format_safe_match_response(_raw_match_data())
        assert "power" not in result["data"]

    def test_no_lust_score(self):
        result = format_safe_match_response(_raw_match_data())
        assert "lust_score" not in result["data"]

    def test_no_defense_mechanisms(self):
        result = format_safe_match_response(_raw_match_data())
        assert "defense_mechanisms" not in result["data"]
        assert "layered_analysis" not in result["data"]

    def test_primary_track_and_quadrant_safe(self):
        result = format_safe_match_response(_raw_match_data())
        assert result["data"]["primary_track"] == "soul"
        assert result["data"]["quadrant"] == "soulmate"


# ═════════════════════════════════════════════════════════════════════════════
# Test: format_safe_onboard_response
# ═════════════════════════════════════════════════════════════════════════════

class TestFormatSafeOnboardResponse:

    def test_returns_success_status(self):
        result = format_safe_onboard_response(_psychology_profile())
        assert result["status"] == "success"

    def test_relationship_dynamic_included(self):
        result = format_safe_onboard_response(_psychology_profile())
        assert result["data"]["relationship_dynamic"] == "high_voltage"

    def test_psychological_needs_included(self):
        result = format_safe_onboard_response(_psychology_profile())
        assert "渴望被完全理解" in result["data"]["psychological_needs"]

    def test_favorable_elements_included(self):
        result = format_safe_onboard_response(_psychology_profile())
        assert "水" in result["data"]["favorable_elements"]

    def test_no_target_signs_leaked(self):
        result = format_safe_onboard_response(_psychology_profile())
        assert "target_western_signs" not in result["data"]
        assert "target_bazi_elements" not in result["data"]

    def test_no_zwds_tags_leaked(self):
        result = format_safe_onboard_response(_psychology_profile())
        assert "zwds_partner_tags" not in result["data"]

    def test_llm_report_included(self):
        result = format_safe_onboard_response(_psychology_profile(), "你擁有極強的保護慾...")
        assert result["data"]["ai_natal_report"] == "你擁有極強的保護慾..."

    def test_no_sensitive_data(self):
        result = format_safe_onboard_response(_psychology_profile(), "report")
        assert_no_sensitive_data(result)


# ═════════════════════════════════════════════════════════════════════════════
# Test: assert_no_sensitive_data utility
# ═════════════════════════════════════════════════════════════════════════════

class TestAssertNoSensitiveData:

    def test_clean_data_passes(self):
        clean = {"data": {"harmony_score": 85, "badges": ["test"]}}
        assert assert_no_sensitive_data(clean) is True

    def test_sensitive_key_raises(self):
        dirty = {"data": {"bazi": {"day_master": "甲"}}}
        with pytest.raises(AssertionError, match="SECURITY LEAK"):
            assert_no_sensitive_data(dirty)

    def test_sensitive_value_raises(self):
        dirty = {"data": {"report": "你的偏印帶來了..."}}
        with pytest.raises(AssertionError, match="SECURITY LEAK"):
            assert_no_sensitive_data(dirty)

    def test_nested_sensitive_key_raises(self):
        dirty = {"data": {"inner": {"zwds": {"palaces": {}}}}}
        with pytest.raises(AssertionError, match="SECURITY LEAK"):
            assert_no_sensitive_data(dirty)

    def test_degree_value_raises(self):
        dirty = {"data": {"info": "sun_degree is 15.3"}}
        with pytest.raises(AssertionError, match="SECURITY LEAK"):
            assert_no_sensitive_data(dirty)

    def test_chinese_astro_term_raises(self):
        dirty = {"data": {"info": "你的貪狼化忌..."}}
        with pytest.raises(AssertionError, match="SECURITY LEAK"):
            assert_no_sensitive_data(dirty)
