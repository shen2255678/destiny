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
