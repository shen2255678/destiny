import pytest
from zwds import (
    compute_zwds_chart,
    get_hour_branch,
    get_four_transforms,
    PALACE_KEYS,
)


class TestGetHourBranch:
    def test_23_00_is_zi(self):   assert get_hour_branch("23:00") == "子"
    def test_01_30_is_chou(self): assert get_hour_branch("01:30") == "丑"
    def test_11_00_is_wu(self):   assert get_hour_branch("11:00") == "午"
    def test_00_30_is_zi(self):   assert get_hour_branch("00:30") == "子"
    def test_22_59_is_hai(self):  assert get_hour_branch("22:59") == "亥"


class TestGetFourTransforms:
    def test_geng_year_1990(self):
        # 1990 = 庚年 (y1=6): 化祿=太陽, 化権=武曲, 化科=天府, 化忌=天同
        t = get_four_transforms(1990)
        assert t["hua_lu"]   == "太陽"
        assert t["hua_quan"] == "武曲"
        assert t["hua_ke"]   == "天府"
        assert t["hua_ji"]   == "天同"

    def test_jia_year_1984(self):
        # 1984 = 甲年 (y1=0): 化祿=廉貞, 化権=破軍, 化科=武曲, 化忌=太陽
        t = get_four_transforms(1984)
        assert t["hua_lu"]   == "廉貞"
        assert t["hua_quan"] == "破軍"
        assert t["hua_ke"]   == "武曲"
        assert t["hua_ji"]   == "太陽"


class TestComputeZwdsChart:
    def setup_method(self):
        self.chart = compute_zwds_chart(1990, 6, 15, "11:30", "M")

    def test_returns_dict_with_palaces(self):
        assert "palaces" in self.chart
        assert "four_transforms" in self.chart
        assert "five_element" in self.chart
        assert "body_palace_name" in self.chart

    def test_palaces_has_all_12_keys(self):
        for key in PALACE_KEYS:
            assert key in self.chart["palaces"], f"Missing palace: {key}"

    def test_each_palace_has_required_fields(self):
        for key in PALACE_KEYS:
            p = self.chart["palaces"][key]
            assert "main_stars" in p
            assert "malevolent_stars" in p
            assert "auspicious_stars" in p
            assert isinstance(p["main_stars"], list)

    def test_all_14_main_stars_placed(self):
        all_stars = []
        for p in self.chart["palaces"].values():
            all_stars.extend(p["main_stars"])
        MAIN_STARS = ["紫微","天機","太陽","武曲","天同","廉貞","天府","太陰","貪狼","巨門","天相","天梁","七殺","破軍"]
        for star in MAIN_STARS:
            assert any(star in s for s in all_stars), f"Star {star} not placed"

    def test_four_transforms_in_output(self):
        t = self.chart["four_transforms"]
        assert all(k in t for k in ["hua_lu", "hua_quan", "hua_ke", "hua_ji"])
        assert all(len(v) > 0 for v in t.values())

    def test_five_element_is_valid(self):
        valid = ["水二局","火六局","土五局","木三局","金四局"]
        assert self.chart["five_element"] in valid

    def test_transform_markers_appear_in_star_names(self):
        # At least one palace should have a star with a 化X marker
        all_stars = []
        for p in self.chart["palaces"].values():
            all_stars.extend(p["main_stars"])
        has_marker = any(any(m in s for m in ["化祿","化権","化科","化忌"]) for s in all_stars)
        assert has_marker

    def test_none_birth_time_returns_none(self):
        result = compute_zwds_chart(1990, 6, 15, None, "M")
        assert result is None


from zwds_synastry import (
    compute_zwds_synastry,
    get_palace_energy,
    detect_stress_defense,
    get_star_archetype_mods,
    STAR_ARCHETYPE_MATRIX,
)

CHART_A = compute_zwds_chart(1990, 6, 15, "11:30", "M")
CHART_B = compute_zwds_chart(1993, 3, 8,  "05:00", "F")


class TestGetPalaceEnergy:
    def test_non_empty_palace_returns_own_stars(self):
        result = get_palace_energy(CHART_A, "ming")
        assert result["strength"] == 1.0
        assert result["is_chameleon"] == False

    def test_empty_palace_borrows_opposite_at_08(self):
        # Create a chart with empty 命宮 (ming)
        mock_chart = {**CHART_A, "palaces": {
            **CHART_A["palaces"],
            "ming": {**CHART_A["palaces"]["ming"], "main_stars": [], "is_empty": True}
        }}
        result = get_palace_energy(mock_chart, "ming")
        assert result["strength"] == 0.8
        assert result["is_chameleon"] == True
        # Should have borrowed from travel palace (遷移宮)
        travel_stars = CHART_A["palaces"]["travel"]["main_stars"]
        assert result["stars"] == travel_stars


class TestDetectStressDefense:
    def test_returns_empty_list_when_no_malevolent_in_spouse(self):
        mock_chart = {**CHART_A, "palaces": {
            **CHART_A["palaces"],
            "spouse": {**CHART_A["palaces"]["spouse"], "malevolent_stars": []}
        }}
        triggers = detect_stress_defense(mock_chart)
        assert triggers == []

    def test_qing_yang_triggers_preemptive_strike(self):
        mock_chart = {**CHART_A, "palaces": {
            **CHART_A["palaces"],
            "spouse": {**CHART_A["palaces"]["spouse"], "malevolent_stars": ["擎羊"]}
        }}
        triggers = detect_stress_defense(mock_chart)
        assert "preemptive_strike" in triggers

    def test_tuo_luo_triggers_silent_rumination(self):
        mock_chart = {**CHART_A, "palaces": {
            **CHART_A["palaces"],
            "spouse": {**CHART_A["palaces"]["spouse"], "malevolent_stars": ["陀羅"]}
        }}
        triggers = detect_stress_defense(mock_chart)
        assert "silent_rumination" in triggers

    def test_di_kong_triggers_sudden_withdrawal(self):
        mock_chart = {**CHART_A, "palaces": {
            **CHART_A["palaces"],
            "spouse": {**CHART_A["palaces"]["spouse"], "malevolent_stars": ["地空"]}
        }}
        triggers = detect_stress_defense(mock_chart)
        assert "sudden_withdrawal" in triggers


class TestGetStarArchetypeMods:
    def test_returns_default_mods_for_empty_palace(self):
        mock_chart = {**CHART_A, "palaces": {
            **CHART_A["palaces"],
            "ming": {**CHART_A["palaces"]["ming"], "main_stars": [], "is_empty": True}
        }}
        mods = get_star_archetype_mods(mock_chart)
        assert mods["passion"] == 1.0
        assert mods["rpv_frame_bonus"] == -10  # chameleon penalty

    def test_sha_po_lang_boosts_passion(self):
        mock_chart = {**CHART_A, "palaces": {
            **CHART_A["palaces"],
            "ming": {**CHART_A["palaces"]["ming"], "main_stars": ["七殺"], "is_empty": False}
        }}
        mods = get_star_archetype_mods(mock_chart)
        assert mods["passion"] == pytest.approx(1.3)
        assert mods["partner"] == pytest.approx(0.8)


class TestComputeZwdsSynastry:
    def test_returns_all_required_keys(self):
        result = compute_zwds_synastry(CHART_A, 1990, CHART_B, 1993)
        for key in ["track_mods", "rpv_modifier", "defense_a", "defense_b",
                    "flying_stars", "spiciness_level", "layered_analysis"]:
            assert key in result, f"Missing key: {key}"

    def test_track_mods_have_four_tracks(self):
        result = compute_zwds_synastry(CHART_A, 1990, CHART_B, 1993)
        for t in ["friend", "passion", "partner", "soul"]:
            assert t in result["track_mods"]

    def test_all_track_mods_are_positive(self):
        result = compute_zwds_synastry(CHART_A, 1990, CHART_B, 1993)
        for v in result["track_mods"].values():
            assert v > 0, f"Negative track modifier: {v}"

    def test_rpv_modifier_is_valid(self):
        result = compute_zwds_synastry(CHART_A, 1990, CHART_B, 1993)
        assert isinstance(result["rpv_modifier"], (int, float))

    def test_spiciness_level_is_string(self):
        result = compute_zwds_synastry(CHART_A, 1990, CHART_B, 1993)
        assert isinstance(result["spiciness_level"], str)
        assert result["spiciness_level"] in ["STABLE", "MEDIUM", "HIGH_VOLTAGE", "SOULMATE"]

    def test_defense_lists_are_lists(self):
        result = compute_zwds_synastry(CHART_A, 1990, CHART_B, 1993)
        assert isinstance(result["defense_a"], list)
        assert isinstance(result["defense_b"], list)

    def test_mutual_hua_lu_boosts_partner_mod(self):
        # Create scenario with mutual 化祿 by patching flying star result
        from unittest.mock import patch
        mock_flying = {
            "hua_lu_a_to_b": True, "hua_lu_b_to_a": True,
            "hua_ji_a_to_b": False, "hua_ji_b_to_a": False,
            "hua_quan_a_to_b": False, "hua_quan_b_to_a": False,
            "spouse_match_a_sees_b": False,
        }
        with patch("zwds_synastry._compute_flying_stars", return_value=mock_flying):
            result = compute_zwds_synastry(CHART_A, 1990, CHART_B, 1993)
        assert result["track_mods"]["partner"] >= 1.2

    def test_mutual_hua_ji_boosts_soul_mod(self):
        from unittest.mock import patch
        mock_flying = {
            "hua_lu_a_to_b": False, "hua_lu_b_to_a": False,
            "hua_ji_a_to_b": True, "hua_ji_b_to_a": True,
            "hua_quan_a_to_b": False, "hua_quan_b_to_a": False,
            "spouse_match_a_sees_b": False,
        }
        with patch("zwds_synastry._compute_flying_stars", return_value=mock_flying):
            result = compute_zwds_synastry(CHART_A, 1990, CHART_B, 1993)
        assert result["track_mods"]["soul"] >= 1.3
