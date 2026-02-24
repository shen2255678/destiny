# -*- coding: utf-8 -*-
"""
DESTINY — Tests for Ideal Partner Avatar Profiler (Sprint 4)

20 tests covering:
  Rule 1: Western → DSC, Venus, Mars, natal_aspects hard aspect, sign-level fallback
  Rule 2: BaZi → Day Master complement, Day Branch 偏印
  Rule 3: ZWDS → main star groups, empty palace borrowing, sha-stars, 四化 stripping
  Edge cases: Tier 3 degradation, all-empty input, partial inputs
"""
import pytest
from ideal_avatar import extract_ideal_partner_profile


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _western(*, house7_sign=None, venus_sign=None, mars_sign=None,
             moon_sign=None, pluto_sign=None, uranus_sign=None,
             chiron_sign=None, natal_aspects=None, **kw):
    chart = {}
    if house7_sign:   chart["house7_sign"] = house7_sign
    if venus_sign:    chart["venus_sign"] = venus_sign
    if mars_sign:     chart["mars_sign"] = mars_sign
    if moon_sign:     chart["moon_sign"] = moon_sign
    if pluto_sign:    chart["pluto_sign"] = pluto_sign
    if uranus_sign:   chart["uranus_sign"] = uranus_sign
    if chiron_sign:   chart["chiron_sign"] = chiron_sign
    if natal_aspects is not None:
        chart["natal_aspects"] = natal_aspects
    chart.update(kw)
    return chart


def _bazi(*, day_master_element=None, bazi_day_branch=None, **kw):
    chart = {}
    if day_master_element:
        chart["day_master_element"] = day_master_element
    if bazi_day_branch:
        chart["bazi_day_branch"] = bazi_day_branch
    chart.update(kw)
    return chart


def _zwds(*, spouse_main=None, spouse_malevolent=None, spouse_empty=False,
          career_main=None):
    palaces = {}
    if spouse_main is not None or spouse_malevolent is not None or spouse_empty:
        palaces["spouse"] = {
            "main_stars": spouse_main or [],
            "malevolent_stars": spouse_malevolent or [],
            "is_empty": spouse_empty,
        }
    if career_main is not None:
        palaces["career"] = {"main_stars": career_main}
    return {"palaces": palaces}


# ═════════════════════════════════════════════════════════════════════════════
# Rule 1: Western Astrology
# ═════════════════════════════════════════════════════════════════════════════

class TestWesternExtraction:
    """Tests for DSC, Venus, Mars, and hard aspect detection."""

    def test_dsc_highest_priority(self):
        """DSC (house7_sign) should appear first in target signs."""
        w = _western(house7_sign="pisces", venus_sign="leo", mars_sign="scorpio")
        res = extract_ideal_partner_profile(w, {}, {})
        assert res["target_western_signs"][0] == "Pisces"
        assert "Leo" in res["target_western_signs"]
        assert "Scorpio" in res["target_western_signs"]

    def test_venus_mars_only_when_no_dsc(self):
        """Without DSC, Venus and Mars still populate target signs."""
        w = _western(venus_sign="taurus", mars_sign="aries")
        res = extract_ideal_partner_profile(w, {}, {})
        assert "Taurus" in res["target_western_signs"]
        assert "Aries" in res["target_western_signs"]
        assert res["relationship_dynamic"] == "stable"

    def test_no_duplicate_signs(self):
        """Same sign from Venus and Mars should not duplicate."""
        w = _western(venus_sign="leo", mars_sign="leo")
        res = extract_ideal_partner_profile(w, {}, {})
        assert res["target_western_signs"].count("Leo") == 1

    def test_natal_aspects_hard_aspect_triggers_hv(self):
        """Venus conjunct Pluto in natal_aspects → high_voltage."""
        aspects = [{"a": "venus", "b": "pluto", "aspect": "conjunction", "orb": 2.0}]
        w = _western(venus_sign="scorpio", pluto_sign="scorpio", natal_aspects=aspects)
        res = extract_ideal_partner_profile(w, {}, {})
        assert res["relationship_dynamic"] == "high_voltage"
        assert "潛意識被高波動、非常規的對象吸引" in res["psychological_needs"]

    def test_moon_square_uranus_triggers_hv(self):
        """Moon square Uranus → high_voltage."""
        aspects = [{"a": "moon", "b": "uranus", "aspect": "square", "orb": 3.5}]
        w = _western(moon_sign="cancer", uranus_sign="aries", natal_aspects=aspects)
        res = extract_ideal_partner_profile(w, {}, {})
        assert res["relationship_dynamic"] == "high_voltage"

    def test_sign_level_fallback_when_no_natal_aspects(self):
        """Sign-level hard aspect detection when natal_aspects key missing."""
        # Moon in Cancer, Pluto in Libra → 3 signs apart → square → HV
        w = _western(moon_sign="cancer", pluto_sign="libra")
        res = extract_ideal_partner_profile(w, {}, {})
        assert res["relationship_dynamic"] == "high_voltage"

    def test_trine_does_not_trigger_hv(self):
        """Non-hard natal aspects should NOT trigger high_voltage."""
        aspects = [{"a": "venus", "b": "pluto", "aspect": "trine", "orb": 1.0}]
        w = _western(venus_sign="taurus", pluto_sign="virgo", natal_aspects=aspects)
        res = extract_ideal_partner_profile(w, {}, {})
        assert res["relationship_dynamic"] == "stable"

    def test_descendant_sign_key_also_works(self):
        """descendant_sign key (without house7_sign) should also be picked up."""
        w = {"descendant_sign": "gemini", "venus_sign": "leo"}
        res = extract_ideal_partner_profile(w, {}, {})
        assert "Gemini" in res["target_western_signs"]


# ═════════════════════════════════════════════════════════════════════════════
# Rule 2: BaZi
# ═════════════════════════════════════════════════════════════════════════════

class TestBaziExtraction:
    """Tests for Day Master complement and Day Branch 偏印."""

    def test_wood_complement(self):
        """Wood day master → needs 水(water nurtures) + 金(metal prunes)."""
        b = _bazi(day_master_element="wood")
        res = extract_ideal_partner_profile({}, b, {})
        assert "火" in res["target_bazi_elements"]  # wood generates fire
        assert "水" in res["target_bazi_elements"]  # water generates wood

    def test_fire_complement(self):
        """Fire day master → needs 木(wood feeds) + 土(fire generates)."""
        b = _bazi(day_master_element="fire")
        res = extract_ideal_partner_profile({}, b, {})
        assert "土" in res["target_bazi_elements"]  # fire generates earth
        assert "木" in res["target_bazi_elements"]  # wood generates fire

    def test_day_branch_pian_yin(self):
        """Day branch 巳 → unconventional attraction need."""
        b = _bazi(day_master_element="metal", bazi_day_branch="巳")
        res = extract_ideal_partner_profile({}, b, {})
        assert "容易被古怪、有獨特邏輯的人吸引" in res["psychological_needs"]

    def test_day_branch_non_pian_yin(self):
        """Day branch 午 should NOT trigger 偏印 need."""
        b = _bazi(day_master_element="metal", bazi_day_branch="午")
        res = extract_ideal_partner_profile({}, b, {})
        assert "容易被古怪、有獨特邏輯的人吸引" not in res["psychological_needs"]


# ═════════════════════════════════════════════════════════════════════════════
# Rule 3: ZWDS
# ═════════════════════════════════════════════════════════════════════════════

class TestZwdsExtraction:
    """Tests for ZWDS spouse palace star groups, sha-stars, empty palace."""

    def test_sha_po_lang_group(self):
        """七殺 in spouse palace → 殺破狼 tags."""
        z = _zwds(spouse_main=["七殺"])
        res = extract_ideal_partner_profile({}, {}, z)
        assert "感情波動大" in res["zwds_partner_tags"]
        assert "喜歡充滿魅力與挑戰性的對象" in res["zwds_partner_tags"]

    def test_ji_yue_tong_liang_group(self):
        """天機 + 天梁 → 機月同梁 tags."""
        z = _zwds(spouse_main=["天機", "天梁"])
        res = extract_ideal_partner_profile({}, {}, z)
        assert "渴望溫柔陪伴" in res["zwds_partner_tags"]

    def test_empty_palace_borrows_career(self):
        """Empty spouse palace → borrow from career palace + flexibility note."""
        z = _zwds(spouse_main=[], spouse_empty=True, career_main=["紫微", "天府"])
        res = extract_ideal_partner_profile({}, {}, z)
        assert "感情觀較具彈性，容易受環境或伴侶狀態影響" in res["psychological_needs"]
        assert "喜歡氣場強大、能帶領自己的人" in res["zwds_partner_tags"]

    def test_sha_star_qingyang(self):
        """擎羊 in malevolent_stars → HV tags + need."""
        z = _zwds(spouse_main=["天同"], spouse_malevolent=["擎羊"])
        res = extract_ideal_partner_profile({}, {}, z)
        assert "氣場強" in res["zwds_partner_tags"]
        assert "直接不扭捏" in res["zwds_partner_tags"]
        assert res["relationship_dynamic"] == "high_voltage"

    def test_sha_star_dikong(self):
        """地空 → non-traditional relationship tags."""
        z = _zwds(spouse_main=["太陰"], spouse_malevolent=["地空"])
        res = extract_ideal_partner_profile({}, {}, z)
        assert "靈魂共鳴" in res["zwds_partner_tags"]
        assert "非傳統關係" in res["zwds_partner_tags"]

    def test_hua_stripping(self):
        """'天府化科' should be stripped to '天府' and match 紫府日 group."""
        z = _zwds(spouse_main=["天府化科"])
        res = extract_ideal_partner_profile({}, {}, z)
        assert "喜歡氣場強大、能帶領自己的人" in res["zwds_partner_tags"]


# ═════════════════════════════════════════════════════════════════════════════
# Edge Cases & Degradation
# ═════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Tier 3 degradation, all-empty, partial, karmic flag."""

    def test_all_empty_returns_safe_structure(self):
        """({}, {}, {}) must return valid dict, never crash."""
        res = extract_ideal_partner_profile({}, {}, {})
        assert res["target_western_signs"] == []
        assert res["target_bazi_elements"] == []
        assert res["relationship_dynamic"] == "stable"
        assert res["psychological_needs"] == []
        assert res["zwds_partner_tags"] == []
        assert res["karmic_match_required"] is False

    def test_none_inputs(self):
        """None inputs should be treated as empty dicts."""
        res = extract_ideal_partner_profile(None, None, None)
        assert isinstance(res, dict)
        assert res["relationship_dynamic"] == "stable"

    def test_karmic_flag_requires_both(self):
        """karmic_match_required only when BOTH Western AND ZWDS signal HV."""
        # Western HV (Moon square Pluto) + ZWDS HV (擎羊)
        aspects = [{"a": "moon", "b": "pluto", "aspect": "square", "orb": 1.0}]
        w = _western(moon_sign="aries", pluto_sign="cancer", natal_aspects=aspects)
        z = _zwds(spouse_main=["天同"], spouse_malevolent=["擎羊"])
        res = extract_ideal_partner_profile(w, {}, z)
        assert res["karmic_match_required"] is True

    def test_karmic_flag_false_when_only_western_hv(self):
        """karmic_match_required should be False if only Western is HV."""
        aspects = [{"a": "venus", "b": "pluto", "aspect": "conjunction", "orb": 1.0}]
        w = _western(venus_sign="scorpio", pluto_sign="scorpio", natal_aspects=aspects)
        z = _zwds(spouse_main=["天同"])  # no sha stars → not HV
        res = extract_ideal_partner_profile(w, {}, z)
        assert res["karmic_match_required"] is False
        assert res["relationship_dynamic"] == "high_voltage"  # Western alone is enough for dynamic
