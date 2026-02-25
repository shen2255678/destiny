# -*- coding: utf-8 -*-
"""
DESTINY — Tests for prompt_manager.py (Sprint 8)

Tests cover:
  - get_ideal_match_prompt avatar_summary injection
  - Backward compatibility without avatar_summary
  - All avatar_summary fields appear in prompt
  - Psychological conflict hint
"""
import pytest

from prompt_manager import get_ideal_match_prompt, get_match_report_prompt, _MATCH_ARCHETYPE_SCHEMA


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _chart():
    """Minimal chart_data for testing prompt generation."""
    return {
        "sun_sign": "aries",
        "moon_sign": "cancer",
        "venus_sign": "taurus",
        "mars_sign": "gemini",
        "ascendant_sign": "leo",
        "house7_sign": "aquarius",
        "juno_sign": "scorpio",
        "bazi": {
            "day_master": "甲",
            "day_master_element": "wood",
            "element_profile": {"desc": "直率果斷"},
        },
        "bazi_element": "wood",
        "element_profile": {
            "dominant": ["fire"],
            "deficiency": ["earth"],
        },
        "zwds": {
            "palaces": {
                "spouse": {
                    "main_stars": ["天機", "天梁"],
                    "malevolent_stars": [],
                    "is_empty": False,
                },
                "career": {"main_stars": []},
            },
        },
        "sm_tags": ["moon_square_saturn"],
        "karmic_tags": ["south_node_conjunct_venus"],
    }


def _avatar_summary():
    """Sample avatar_summary from extract_ideal_partner_profile."""
    return {
        "relationship_dynamic": "high_voltage",
        "psychological_needs": ["渴望被完全理解", "需要深度靈魂連結", "難以信任"],
        "favorable_elements": ["水", "木"],
        "attachment_style": "anxious",
        "zwds_partner_tags": ["渴望溫柔陪伴", "感情需要穩定感"],
        "venus_mars_tags": ["Venus Taurus: 重視物質安全感", "Mars Gemini: 語言調情"],
        "karmic_match_required": True,
        "psychological_conflict": False,
    }


# ═════════════════════════════════════════════════════════════════════════════
# Tests
# ═════════════════════════════════════════════════════════════════════════════

class TestGetIdealMatchPrompt:
    """Tests for get_ideal_match_prompt with avatar_summary."""

    def test_backward_compatible_no_avatar(self):
        """Without avatar_summary, prompt should still generate successfully."""
        prompt = get_ideal_match_prompt(_chart())
        assert "DESTINY" in prompt
        assert "甲" in prompt
        assert "天機" in prompt

    def test_avatar_block_injected(self):
        """With avatar_summary, prompt includes pre-computed summary block."""
        prompt = get_ideal_match_prompt(_chart(), avatar_summary=_avatar_summary())
        assert "後端預算命理摘要" in prompt

    def test_relationship_dynamic_in_prompt(self):
        prompt = get_ideal_match_prompt(_chart(), avatar_summary=_avatar_summary())
        assert "high_voltage" in prompt

    def test_psychological_needs_in_prompt(self):
        prompt = get_ideal_match_prompt(_chart(), avatar_summary=_avatar_summary())
        assert "渴望被完全理解" in prompt

    def test_favorable_elements_in_prompt(self):
        prompt = get_ideal_match_prompt(_chart(), avatar_summary=_avatar_summary())
        assert "水" in prompt
        assert "木" in prompt

    def test_attachment_style_in_prompt(self):
        prompt = get_ideal_match_prompt(_chart(), avatar_summary=_avatar_summary())
        assert "anxious" in prompt

    def test_zwds_tags_in_prompt(self):
        prompt = get_ideal_match_prompt(_chart(), avatar_summary=_avatar_summary())
        assert "渴望溫柔陪伴" in prompt

    def test_venus_mars_tags_in_prompt(self):
        prompt = get_ideal_match_prompt(_chart(), avatar_summary=_avatar_summary())
        assert "Venus Taurus" in prompt
        assert "Mars Gemini" in prompt

    def test_karmic_flag_in_prompt(self):
        prompt = get_ideal_match_prompt(_chart(), avatar_summary=_avatar_summary())
        assert "True" in prompt  # karmic_match_required = True

    def test_conflict_hint_absent_when_no_conflict(self):
        """No psychological_conflict → no conflict hint in prompt."""
        avatar = _avatar_summary()
        avatar["psychological_conflict"] = False
        prompt = get_ideal_match_prompt(_chart(), avatar_summary=avatar)
        assert "衝突格局" not in prompt

    def test_conflict_hint_present_when_conflict(self):
        """psychological_conflict = True → conflict hint injected."""
        avatar = _avatar_summary()
        avatar["psychological_conflict"] = True
        prompt = get_ideal_match_prompt(_chart(), avatar_summary=avatar)
        assert "衝突格局" in prompt
        assert "傷官見官" in prompt

    def test_avatar_none_same_as_absent(self):
        """Passing avatar_summary=None should behave same as not passing it."""
        p1 = get_ideal_match_prompt(_chart())
        p2 = get_ideal_match_prompt(_chart(), avatar_summary=None)
        assert p1 == p2

    def test_empty_avatar_summary(self):
        """Empty dict avatar_summary → block injected but with unknowns."""
        prompt = get_ideal_match_prompt(_chart(), avatar_summary={})
        assert "後端預算命理摘要" in prompt
        assert "unknown" in prompt  # defaults to unknown

    def test_prompt_still_contains_base_data(self):
        """Even with avatar_summary, base chart data sections remain."""
        prompt = get_ideal_match_prompt(_chart(), avatar_summary=_avatar_summary())
        assert "八字結構" in prompt
        assert "西占星盤" in prompt
        assert "紫微斗數" in prompt
        assert "天機, 天梁" in prompt or "天機" in prompt


# ═════════════════════════════════════════════════════════════════════════════
# Task 5: Polarizing Value Conflicts — prompt writing rule
# ═════════════════════════════════════════════════════════════════════════════

class TestPolarizingValueConflictPrompt:
    """Verify prompt_manager includes value-conflict writing rule."""

    def test_toxic_trap_rule_in_ideal_match_prompt(self):
        """get_ideal_match_prompt output should contain value-conflict writing rule."""
        chart = {"sun_sign": "aries", "moon_sign": "taurus", "venus_sign": "gemini",
                 "mars_sign": "cancer", "bazi": {}, "element_profile": {}}
        prompt = get_ideal_match_prompt(chart)
        assert "價值觀衝突" in prompt or "普世皆準" in prompt, \
            "Prompt should instruct LLM to use polarizing value conflict framing for toxic_trap"


# ═════════════════════════════════════════════════════════════════════════════
# Task 1: _MATCH_ARCHETYPE_SCHEMA — no UI markup, anti-Barnum formula
# ═════════════════════════════════════════════════════════════════════════════

def test_schema_has_no_ui_markup():
    """JSON schema must not contain emoji or numbered list prefixes."""
    assert "❌" not in _MATCH_ARCHETYPE_SCHEMA
    assert "👉" not in _MATCH_ARCHETYPE_SCHEMA
    assert "一、" not in _MATCH_ARCHETYPE_SCHEMA
    assert "二、" not in _MATCH_ARCHETYPE_SCHEMA
    assert "五、" not in _MATCH_ARCHETYPE_SCHEMA


def test_schema_has_anti_barnum_formula():
    """reality_check description must reference the A撞B collision formula."""
    assert "User A" in _MATCH_ARCHETYPE_SCHEMA
    assert "User B" in _MATCH_ARCHETYPE_SCHEMA


# ── Task 2 tests ──────────────────────────────────────────────────────────────

def _match_data():
    return {
        "lust_score": 30,
        "soul_score": 80,
        "tracks": {"friend": 40, "passion": 30, "partner": 50, "soul": 80},
        "primary_track": "soul",
        "quadrant": "partner",
        "power": {"viewer_role": "Equal", "target_role": "Equal", "rpv": 0.0, "frame_break": False},
        "high_voltage": False,
        "psychological_tags": [],
        "zwds": {},
    }


def test_no_duplicate_task_block():
    """Only one 【本次任務 block should appear in the final prompt."""
    prompt, _ = get_match_report_prompt(_match_data())
    assert prompt.count("【本次任務") == 1


def test_rpv_low_shows_equal_description():
    """For rpv=0.0 the prompt should contain the equal-balance description."""
    prompt, _ = get_match_report_prompt(_match_data())
    assert "勢均力敵" in prompt


def test_rpv_high_shows_position_description():
    """RPV > 20 should include a high-position description."""
    data = _match_data()
    data["power"]["rpv"] = 35.0
    prompt, _ = get_match_report_prompt(data)
    assert "高位" in prompt


def test_profile_injection_needs_and_dynamic():
    """psychological_needs and relationship_dynamic appear when profiles provided."""
    prof_a = {
        "psychological_needs": ["極度需要秩序", "無法忍受計畫被打破"],
        "relationship_dynamic": "stable",
        "attachment_style": "anxious",
    }
    prof_b = {
        "psychological_needs": ["需要思想自由", "討厭被框架綁死"],
        "relationship_dynamic": "high_voltage",
        "attachment_style": "avoidant",
    }
    prompt, _ = get_match_report_prompt(_match_data(), user_a_profile=prof_a, user_b_profile=prof_b)
    assert "極度需要秩序" in prompt
    assert "需要思想自由" in prompt


def test_profile_injection_includes_attachment_style():
    """attachment_style from each profile must appear in the prompt."""
    prof_a = {"psychological_needs": [], "relationship_dynamic": "stable", "attachment_style": "anxious"}
    prof_b = {"psychological_needs": [], "relationship_dynamic": "stable", "attachment_style": "avoidant"}
    prompt, _ = get_match_report_prompt(_match_data(), user_a_profile=prof_a, user_b_profile=prof_b)
    assert "anxious" in prompt or "焦慮" in prompt
    assert "avoidant" in prompt or "逃避" in prompt


def test_no_profile_block_when_absent():
    """When no profiles passed, the 雙方心理結構 block must not appear."""
    prompt, _ = get_match_report_prompt(_match_data())
    assert "雙方心理結構" not in prompt


def test_trap_tag_injected_from_psych_tags():
    """Attachment trap tag from psychological_tags appears in profile block."""
    data = _match_data()
    data["psychological_tags"] = ["Anxious_Avoidant_Trap"]
    prof_a = {"psychological_needs": [], "relationship_dynamic": "stable", "attachment_style": "anxious"}
    prof_b = {"psychological_needs": [], "relationship_dynamic": "stable", "attachment_style": "avoidant"}
    prompt, _ = get_match_report_prompt(data, user_a_profile=prof_a, user_b_profile=prof_b)
    assert "合盤依戀陷阱觸發" in prompt
    assert "Anxious_Avoidant_Trap" in prompt
