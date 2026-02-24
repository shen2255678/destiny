# -*- coding: utf-8 -*-
"""
DESTINY — Tests for BaZi Ten Gods Engine (Sprint 5)

Tests cover:
  - HIDDEN_STEMS completeness
  - get_ten_god for all 10 relationships
  - compute_ten_gods pillar analysis
  - evaluate_day_master_strength scoring + favorable elements
  - Tier 3 degradation (no hour pillar)
  - Empty input safety
"""
import pytest

from bazi import (
    HIDDEN_STEMS,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    STEM_ELEMENTS,
    get_ten_god,
    compute_ten_gods,
    evaluate_day_master_strength,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_bazi(day_stem, pillars, hour_known=True):
    """Helper: build a minimal bazi_chart dict for testing."""
    return {
        "day_master": day_stem,
        "day_master_element": STEM_ELEMENTS.get(day_stem, ""),
        "hour_known": hour_known,
        "four_pillars": pillars,
    }


# ── HIDDEN_STEMS ──────────────────────────────────────────────────────────────

class TestHiddenStems:
    def test_all_12_branches_present(self):
        for branch in EARTHLY_BRANCHES:
            assert branch in HIDDEN_STEMS, f"Missing branch: {branch}"

    def test_dominant_stem_is_first(self):
        """子 dominant is 癸 (water), 午 dominant is 丁 (fire)."""
        assert HIDDEN_STEMS["子"][0] == "癸"
        assert HIDDEN_STEMS["午"][0] == "丁"

    def test_all_stems_are_valid(self):
        valid = set(HEAVENLY_STEMS)
        for branch, stems in HIDDEN_STEMS.items():
            for s in stems:
                assert s in valid, f"Invalid stem {s} in branch {branch}"


# ── get_ten_god ───────────────────────────────────────────────────────────────

class TestGetTenGod:
    """Verify all 10 god relationships for 甲 (yang wood) day master."""

    def test_bi_jian(self):
        """甲 vs 甲 → same stem = 比肩."""
        assert get_ten_god("甲", "甲") == "比肩"

    def test_jie_cai(self):
        """甲 vs 乙 → same element diff polarity = 劫財."""
        assert get_ten_god("甲", "乙") == "劫財"

    def test_shi_shen(self):
        """甲生火 → 丙(yang fire) same polarity = 食神."""
        assert get_ten_god("甲", "丙") == "食神"

    def test_shang_guan(self):
        """甲生火 → 丁(yin fire) diff polarity = 傷官."""
        assert get_ten_god("甲", "丁") == "傷官"

    def test_pian_cai(self):
        """甲剋土 → 戊(yang earth) same polarity = 偏財."""
        assert get_ten_god("甲", "戊") == "偏財"

    def test_zheng_cai(self):
        """甲剋土 → 己(yin earth) diff polarity = 正財."""
        assert get_ten_god("甲", "己") == "正財"

    def test_qi_sha(self):
        """金剋甲 → 庚(yang metal) same polarity = 七殺."""
        assert get_ten_god("甲", "庚") == "七殺"

    def test_zheng_guan(self):
        """金剋甲 → 辛(yin metal) diff polarity = 正官."""
        assert get_ten_god("甲", "辛") == "正官"

    def test_pian_yin(self):
        """水生甲 → 壬(yang water) same polarity = 偏印."""
        assert get_ten_god("甲", "壬") == "偏印"

    def test_zheng_yin(self):
        """水生甲 → 癸(yin water) diff polarity = 正印."""
        assert get_ten_god("甲", "癸") == "正印"

    def test_yin_day_master_bing(self):
        """丙(yang fire) vs 辛(yin metal) → 丙剋金, diff polarity = 正財."""
        assert get_ten_god("丙", "辛") == "正財"


# ── compute_ten_gods ──────────────────────────────────────────────────────────

class TestComputeTenGods:
    def test_basic_chart(self):
        """甲日主, 年柱庚子, 月柱丙寅, 日柱甲午, 時柱壬申."""
        chart = _make_bazi("甲", {
            "year":  {"stem": "庚", "branch": "子"},
            "month": {"stem": "丙", "branch": "寅"},
            "day":   {"stem": "甲", "branch": "午"},
            "hour":  {"stem": "壬", "branch": "申"},
        })
        result = compute_ten_gods(chart)

        assert result["stem_gods"]["year"] == "七殺"     # 庚 vs 甲
        assert result["stem_gods"]["month"] == "食神"    # 丙 vs 甲
        assert result["stem_gods"]["day"] == "日主"
        assert result["stem_gods"]["hour"] == "偏印"     # 壬 vs 甲

        # Branch gods (dominant hidden stems)
        assert result["branch_gods"]["year"] == "正印"   # 子→癸 vs 甲
        assert result["branch_gods"]["month"] == "比肩"  # 寅→甲 vs 甲
        assert result["branch_gods"]["day"]              # 午→丁 vs 甲 = 傷官
        assert result["branch_gods"]["hour"]             # 申→庚 vs 甲 = 七殺

        assert result["spouse_palace_god"] is not None
        assert result["month_god"] == "食神"

    def test_no_hour_pillar(self):
        """Tier 3: hour is None → hour positions should be None."""
        chart = _make_bazi("甲", {
            "year":  {"stem": "庚", "branch": "子"},
            "month": {"stem": "丙", "branch": "寅"},
            "day":   {"stem": "甲", "branch": "午"},
            "hour":  None,
        }, hour_known=False)
        result = compute_ten_gods(chart)
        assert result["stem_gods"]["hour"] is None
        assert result["branch_gods"]["hour"] is None

    def test_empty_chart(self):
        result = compute_ten_gods({})
        assert result["stem_gods"] == {}
        assert result["god_counts"] == {}
        assert result["spouse_palace_god"] is None


class TestDayMasterStrength:
    def test_strong_chart_gets_drain_favorable(self):
        """甲日主, month branch 寅(甲=比肩→得令), year 甲, hour 乙 → definitely strong.
        身強 → 喜: 財(土), 食傷(火), 官殺(金)."""
        chart = _make_bazi("甲", {
            "year":  {"stem": "甲", "branch": "卯"},  # 比肩 + 比肩
            "month": {"stem": "壬", "branch": "寅"},  # 偏印 + 比肩(得令)
            "day":   {"stem": "甲", "branch": "寅"},
            "hour":  {"stem": "甲", "branch": "卯"},  # 比肩 + 比肩
        })
        result = evaluate_day_master_strength(chart)
        assert result["is_strong"] is True
        assert "土" in result["favorable_elements"]  # 財星
        assert "火" in result["favorable_elements"]  # 食傷
        assert result["score"] > 50

    def test_weak_chart_gets_support_favorable(self):
        """甲日主, all pillars are 金/土 → 身弱.
        身弱 → 喜: 比劫(木), 印星(水)."""
        chart = _make_bazi("甲", {
            "year":  {"stem": "庚", "branch": "申"},  # 七殺 + 七殺
            "month": {"stem": "辛", "branch": "酉"},  # 正官 + 正官
            "day":   {"stem": "甲", "branch": "戌"},
            "hour":  {"stem": "戊", "branch": "辰"},  # 偏財 + 偏財
        })
        result = evaluate_day_master_strength(chart)
        assert result["is_strong"] is False
        assert "木" in result["favorable_elements"]  # 比劫
        assert "水" in result["favorable_elements"]  # 印星

    def test_tier3_lower_threshold(self):
        """Without hour pillar, threshold is 40 instead of 50."""
        chart = _make_bazi("甲", {
            "year":  {"stem": "甲", "branch": "寅"},  # 比肩
            "month": {"stem": "壬", "branch": "寅"},  # 偏印 + 比肩(得令)
            "day":   {"stem": "甲", "branch": "午"},
            "hour":  None,
        }, hour_known=False)
        result = evaluate_day_master_strength(chart)
        # Score = 40(得令) + 8(year stem 比肩) + 8(year branch 比肩) + 10(month stem 偏印) - ...
        # Should be strong with lower threshold
        assert result["is_strong"] is True

    def test_empty_chart(self):
        result = evaluate_day_master_strength({})
        assert result["is_strong"] is False
        assert result["favorable_elements"] == []
        assert result["score"] == 0

    def test_dominant_elements_detected(self):
        """With an imbalanced chart, dominant elements should be detected."""
        chart = _make_bazi("甲", {
            "year":  {"stem": "甲", "branch": "寅"},
            "month": {"stem": "乙", "branch": "卯"},
            "day":   {"stem": "甲", "branch": "寅"},
            "hour":  {"stem": "甲", "branch": "卯"},
        })
        result = evaluate_day_master_strength(chart)
        assert len(result["dominant_elements"]) >= 1
        assert "木" in result["dominant_elements"]
