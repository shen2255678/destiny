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
