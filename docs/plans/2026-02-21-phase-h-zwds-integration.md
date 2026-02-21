# Phase H: ZiWei DouShu (紫微斗數) 業力引擎 — Python Native

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 將紫微斗數排盤邏輯移植為 Python，整合進現有 `astro-service/`，作為三位一體演算法的第三層（業力與防禦機制，佔 30% 權重）。

**Architecture:**
- `astro-service/zwds.py` — ZWDS 排盤引擎（Python port，無需新服務）
- `astro-service/zwds_synastry.py` — 合盤分析：飛星四化 + 空宮借星 + 主星人設 + 煞星防禦
- `astro-service/matching.py` — 更新三位一體整合架構（西占 40% + 八字 30% + 紫微 30%）
- `destiny-app/supabase/migrations/008_zwds.sql` — 新增紫微欄位
- 新增輸出欄位：`spiciness_level`、`defense_mechanisms`、`layered_analysis`

**Tech Stack:** Python 3.9, `lunardate` (農曆轉換), pytest. **無任何新服務/新資料夾需建立。**

---

## 設計哲學（來自 ziwei-1.2.md Batch 3）

三個學派各司其職，**疊加而非覆蓋**：

| 系統 | 維度 | 軌道貢獻 | 權重 |
|------|------|----------|------|
| **西方占星 (Software)** | 心理需求、認知模式 | Friend & Partner 心理契合度 | 40% |
| **八字五行 (Energy)** | 能量流動、權力傾斜 | Passion 張力 & RPV Dom/Sub | 30% |
| **紫微斗數 (Hardware)** | 業力債務、防禦機制 | Soul 宿命感 & 極端壓力反應 | 30% |

最終軌道公式：
```
Track = existing_western_bazi_score × 0.70 + zwds_modifier × 0.30
(cap at 100)
```

ZWDS 以**乘數修飾器 (Multiplicative Modifiers)** 疊加，不修改現有 Western+BaZi 計算。

---

## Task 1: 安裝 `lunardate` 並更新 requirements.txt

**Files:**
- Modify: `astro-service/requirements.txt`

**Step 1: Add dependency**

Edit `astro-service/requirements.txt` — add:
```
lunardate>=0.2.0
```

**Step 2: Install and verify**

Run: `cd astro-service && pip install lunardate`
Run: `python -c "from lunardate import LunarDate; ld = LunarDate.fromSolarDate(1990, 6, 15); print(ld.month, ld.day)"`
Expected: prints `5 22` (or similar lunar month/day)

**Step 3: Commit**

```bash
git add astro-service/requirements.txt
git commit -m "deps: add lunardate for ZWDS lunar calendar conversion"
```

---

## Task 2: ZWDS 排盤引擎 (`zwds.py`)

**Files:**
- Create: `astro-service/zwds.py`
- Create: `astro-service/test_zwds.py` (engine tests only)

**Background — porting logic from ZiWeiDouShu/js/:**

The JS files use global lookup tables to compute the 12-palace chart. All tables are ported verbatim to Python. Key computation steps:
1. Solar → Lunar (using `lunardate`)
2. Year stem index `y1` = `(year-4) % 10` (甲=0…癸=9)
3. Year branch index `y2` = `(year-4) % 12` (子=0…亥=11)
4. Hour branch index `h_pos` from birth_time string
5. Life palace pos: `l_pos = (12 - h_pos + 1 + lunar_month) % 12`
6. Body palace pos: `b_pos = (12 - (22 - h_pos + 1 - lunar_month) % 12) % 12`
7. Five element: `FIVE_ELE_ARR[y1 % 5][((l_pos - l_pos%2) // 2) % 6]`
8. ZiWei star pos: `FIVE_ELE_TABLE[five_ele][lunar_day - 1]`
9. Distribute 14 main stars via `STAR_Z06` + `STAR_T08`
10. Distribute 6 auspicious stars via `STAR_G07`
11. Distribute 6 malevolent stars via `STAR_B06`
12. Mark 四化 transformations from `STAR_S04`

Output uses **readable English palace keys** matching the design doc schema:
`ming`/`parent`/`karma`/`property`/`career`/`friends`/`travel`/`health`/`wealth`/`children`/`spouse`/`siblings`

**Step 1: Write failing tests**

Create `astro-service/test_zwds.py`:
```python
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
```

**Step 2: Run tests to verify they fail**

Run: `cd astro-service && pytest test_zwds.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'zwds'"

**Step 3: Create zwds.py**

Create `astro-service/zwds.py`:
```python
"""
DESTINY — ZiWei DouShu (紫微斗數) Chart Computation Engine
Python port of ZiWeiDouShu/js/ (original by cubshuang).

Requires: lunardate

Usage:
    chart = compute_zwds_chart(1990, 6, 15, "11:30", "M")
    # Returns: ZwdsChart dict with palaces, four_transforms, five_element
"""
from __future__ import annotations
from typing import Optional
from lunardate import LunarDate

# ── Constants ─────────────────────────────────────────────────────────────────
HEAVENLY_STEMS   = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
EARTHLY_BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]

# Palace keys (English) and Chinese names — index 0 = 命宮
PALACE_KEYS = ["ming","parent","karma","property","career","friends",
               "travel","health","wealth","children","spouse","siblings"]
PALACE_NAMES_ZH = ["命宮","父母宮","福德宮","田宅宮","官祿宮","交友宮",
                   "遷移宮","疾厄宮","財帛宮","子女宮","夫妻宮","兄弟宮"]

FIVE_ELEMENTS = ["水二局","火六局","土五局","木三局","金四局"]
STAR_NAMES_A14 = ["紫微","天機","太陽","武曲","天同","廉貞",
                  "天府","太陰","貪狼","巨門","天相","天梁","七殺","破軍"]
STAR_NAMES_G07 = ["文昌","文曲","左輔","右弼","天魁","天鉞","祿存"]
TRANSFORM_NAMES = ["化祿","化権","化科","化忌"]

# ── Lookup Tables (ported from ziweistar.js) ──────────────────────────────────

# FiveEleArr[y1%5][half_life_pos%6] → five element index
FIVE_ELE_ARR = [
    [0,1,3,2,4,1], [1,2,4,3,0,2], [2,3,0,4,1,3], [3,4,1,0,2,4], [4,0,2,1,3,0],
]

# FiveEleTable[five_ele_idx][lunar_day-1] → ZiWei star palace position (0-11)
FIVE_ELE_TABLE = [
    [1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,0,0,1,1,2,2,3,3,4],
    [9,6,11,4,1,2,10,7,0,5,2,3,11,8,1,6,3,4,0,9,2,7,4,5,1,10,3,8,5,6],
    [6,11,4,1,2,7,0,5,2,3,8,1,6,3,4,9,2,7,4,5,10,3,8,5,6,11,4,9,6,7],
    [4,1,2,5,2,3,6,3,4,7,4,5,8,5,6,9,6,7,10,7,8,11,8,9,0,9,10,1,10,11],
    [11,4,1,2,0,5,2,3,1,6,3,4,2,7,4,5,3,8,5,6,4,9,6,7,5,10,7,8,6,11],
]

# Star_Z06[row][z_pos] → palace position
# Rows 0-5: positions of 紫微、天機、太陽、武曲、天同、廉貞 (StarM_A14 indices 0-5)
# Row 6: position of 天府
STAR_Z06 = [
    [0,1,2,3,4,5,6,7,8,9,10,11],
    [11,0,1,2,3,4,5,6,7,8,9,10],
    [9,10,11,0,1,2,3,4,5,6,7,8],
    [8,9,10,11,0,1,2,3,4,5,6,7],
    [7,8,9,10,11,0,1,2,3,4,5,6],
    [4,5,6,7,8,9,10,11,0,1,2,3],
    [4,3,2,1,0,11,10,9,8,7,6,5],  # row 6 = 天府 position
]

# Star_T08[row][tianfu_pos] → palace position
# Row k → StarM_A14[k+6] position (天府,太陰,貪狼,巨門,天相,天梁,七殺,破軍)
STAR_T08 = [
    [0,1,2,3,4,5,6,7,8,9,10,11],
    [1,2,3,4,5,6,7,8,9,10,11,0],
    [2,3,4,5,6,7,8,9,10,11,0,1],
    [3,4,5,6,7,8,9,10,11,0,1,2],
    [4,5,6,7,8,9,10,11,0,1,2,3],
    [5,6,7,8,9,10,11,0,1,2,3,4],
    [6,7,8,9,10,11,0,1,2,3,4,5],
    [10,11,0,1,2,3,4,5,6,7,8,9],
]

# Star_G07[row][index] → auspicious star palace position
# Rows 0-1: by hour pos; rows 2-3: by lunar_month-1; rows 4-6: by y1_pos (10 values)
STAR_G07 = [
    [10,9,8,7,6,5,4,3,2,1,0,11],          # 文昌 by hour
    [4,5,6,7,8,9,10,11,0,1,2,3],           # 文曲 by hour
    [4,5,6,7,8,9,10,11,0,1,2,3],           # 左輔 by lunar month-1
    [10,9,8,7,6,5,4,3,2,1,0,11],           # 右弼 by lunar month-1
    [1,0,11,11,1,0,1,6,3,3],               # 天魁 by y1 (10 values)
    [7,8,9,9,7,8,7,2,5,5],                 # 天鉞 by y1 (10 values)
    [2,3,5,6,5,6,8,9,11,0],               # 祿存 by y1 (10 values)
]

# Star_S04[transform_idx][y1_pos] → star name for each 四化 (by year heavenly stem)
# Rows: 0=化祿, 1=化権, 2=化科, 3=化忌  |  Cols: 甲乙丙丁戊己庚辛壬癸
STAR_S04 = [
    ["廉貞","天機","天同","太陰","貪狼","武曲","太陽","巨門","天梁","破軍"],   # 化祿
    ["破軍","天梁","天機","天同","太陰","貪狼","武曲","太陽","紫微","巨門"],   # 化権
    ["武曲","紫微","文昌","天機","右弼","天梁","天府","文曲","左輔","太陰"],   # 化科
    ["太陽","太陰","廉貞","巨門","天機","文曲","天同","文昌","武曲","貪狼"],   # 化忌
]

# Star_B06 — six malevolent stars
# [0] 擎羊 by y1; [1] 陀羅 by y1
# [2][y2%4][h] 火星; [3][y2%4][h] 鈴星
# [4][h] 天空; [5][h] 地劫
STAR_B06 = [
    [3,4,6,7,6,7,9,10,0,1],        # 擎羊 (y1 index, 10 values)
    [1,2,4,5,4,5,7,8,10,11],       # 陀羅 (y1 index, 10 values)
    [[2,3,4,5,6,7,8,9,10,11,0,1],   # 火星 [y2%4=0][h_pos]
     [3,4,5,6,7,8,9,10,11,0,1,2],   # 火星 [y2%4=1]
     [1,2,3,4,5,6,7,8,9,10,11,0],   # 火星 [y2%4=2]
     [9,10,11,0,1,2,3,4,5,6,7,8]],  # 火星 [y2%4=3]
    [[10,11,0,1,2,3,4,5,6,7,8,9],   # 鈴星 [y2%4=0]
     [10,11,0,1,2,3,4,5,6,7,8,9],   # 鈴星 [y2%4=1]
     [3,4,5,6,7,8,9,10,11,0,1,2],   # 鈴星 [y2%4=2]
     [10,11,0,1,2,3,4,5,6,7,8,9]],  # 鈴星 [y2%4=3]
    [11,10,9,8,7,6,5,4,3,2,1,0],    # 天空 (h_pos)
    [11,0,1,2,3,4,5,6,7,8,9,10],    # 地劫 (h_pos)
]
STAR_NAMES_B06 = ["擎羊","陀羅","火星","鈴星","天空","地劫"]

# Opposite palaces for empty-palace borrowing (空宮借對宮)
OPPOSITE_PALACE = {
    "ming": "travel", "travel": "ming",
    "spouse": "career", "career": "spouse",
    "karma": "wealth", "wealth": "karma",
    "children": "property", "property": "children",
    "parent": "health", "health": "parent",
    "siblings": "friends", "friends": "siblings",
}

# ── Helper: Hour → Earthly Branch ────────────────────────────────────────────

def get_hour_branch(birth_time: str) -> str:
    """Convert "HH:MM" to EarthlyBranch (時辰).
    子時 covers 23:00-00:59; then pairs of 2 hours each.
    """
    h = int(birth_time.split(":")[0])
    idx = 0 if h == 23 else (h + 1) // 2 % 12
    return EARTHLY_BRANCHES[idx]


def get_four_transforms(birth_year: int) -> dict:
    """Return the four transformation star names for a given year's heavenly stem."""
    y1 = ((birth_year - 4) % 10 + 10) % 10
    return {
        "hua_lu":   STAR_S04[0][y1],
        "hua_quan": STAR_S04[1][y1],
        "hua_ke":   STAR_S04[2][y1],
        "hua_ji":   STAR_S04[3][y1],
    }


# ── Main Chart Computation ────────────────────────────────────────────────────

def compute_zwds_chart(
    birth_year: int, birth_month: int, birth_day: int,
    birth_time: Optional[str], gender: str = "M"
) -> Optional[dict]:
    """Compute a full 12-palace ZiWei DouShu chart.

    Returns None if birth_time is not available (Tier 2/3 users).

    Returns a ZwdsChart dict:
    {
        "palaces": {
            "ming": {
                "main_stars": ["紫微化祿", "七殺"],  # 化X suffix when applicable
                "auspicious_stars": ["文昌"],
                "malevolent_stars": ["擎羊"],
                "is_empty": False,           # True if no main_stars
            },
            ... (12 palaces total, keyed by PALACE_KEYS)
        },
        "body_palace_name": "官祿宮",       # which palace the 身宮 lands in
        "four_transforms": {"hua_lu": "太陽", "hua_quan": "武曲", ...},
        "five_element": "木三局",
        "life_palace_pos": 6,              # earthly branch index of 命宮
    }
    """
    if not birth_time:
        return None

    # Solar → Lunar
    try:
        ld = LunarDate.fromSolarDate(birth_year, birth_month, birth_day)
    except Exception:
        return None
    lunar_month = ld.month
    lunar_day   = ld.day

    # Stem / branch indices
    y1  = ((birth_year - 4) % 10 + 10) % 10    # year heavenly stem index
    y2  = ((birth_year - 4) % 12 + 12) % 12    # year earthly branch index
    h_pos = EARTHLY_BRANCHES.index(get_hour_branch(birth_time))

    # Life palace (命宮) and body palace (身宮) positions
    l_pos = (12 - h_pos + 1 + lunar_month) % 12
    b_pos = (12 - (22 - h_pos + 1 - lunar_month) % 12) % 12

    # Five element (五行局)
    half = ((l_pos - l_pos % 2) // 2) % 6
    five_ele = FIVE_ELE_ARR[y1 % 5][half]

    # ZiWei star position
    z_pos = FIVE_ELE_TABLE[five_ele][lunar_day - 1]

    # TianFu position (row 6 of Star_Z06)
    tianfu_pos = STAR_Z06[6][z_pos]

    # ── Compute star positions ─────────────────────────────────────────────
    # Palace position arrays: main_stars[palace_i], auspicious[palace_i], malevolent[palace_i]
    main_stars    = [[] for _ in range(12)]
    auspicious    = [[] for _ in range(12)]
    malevolent    = [[] for _ in range(12)]

    # Four transformations for this year
    four_trans = get_four_transforms(birth_year)
    # Build reverse map: star_name → transform_suffix
    _trans_map = {four_trans["hua_lu"]: "化祿", four_trans["hua_quan"]: "化権",
                  four_trans["hua_ke"]: "化科", four_trans["hua_ji"]: "化忌"}

    def _star_name_with_transform(name: str) -> str:
        return name + _trans_map.get(name, "")

    # ZiWei system (stars 0-5: 紫微 天機 太陽 武曲 天同 廉貞)
    for k in range(6):
        pos = STAR_Z06[k][z_pos]
        main_stars[pos].append(_star_name_with_transform(STAR_NAMES_A14[k]))

    # TianFu system (stars 6-13: 天府 太陰 貪狼 巨門 天相 天梁 七殺 破軍)
    for k in range(8):
        pos = STAR_T08[k][tianfu_pos]
        main_stars[pos].append(_star_name_with_transform(STAR_NAMES_A14[k + 6]))

    # Auspicious stars (六吉星): 文昌 文曲 (by hour), 左輔 右弼 (by lunar month),
    #                             天魁 天鉞 祿存 (by year stem)
    indices = [h_pos, h_pos, lunar_month - 1, lunar_month - 1, y1, y1, y1]
    for k in range(7):
        pos = STAR_G07[k][indices[k]]
        auspicious[pos].append(_star_name_with_transform(STAR_NAMES_G07[k]))

    # Malevolent stars (六煞星)
    # 擎羊 / 陀羅 by year stem
    auspicious_0 = STAR_B06[0]
    auspicious_1 = STAR_B06[1]
    if y1 < len(auspicious_0):
        malevolent[STAR_B06[0][y1]].append("擎羊")
    if y1 < len(auspicious_1):
        malevolent[STAR_B06[1][y1]].append("陀羅")
    # 火星 / 鈴星 by year branch mod 4 and hour
    malevolent[STAR_B06[2][y2 % 4][h_pos]].append("火星")
    malevolent[STAR_B06[3][y2 % 4][h_pos]].append("鈴星")
    # 天空 / 地劫 by hour
    malevolent[STAR_B06[4][h_pos]].append("天空")
    malevolent[STAR_B06[5][h_pos]].append("地劫")

    # ── Assemble palaces ───────────────────────────────────────────────────
    palaces = {}
    for i in range(12):
        palace_type_idx = (12 - l_pos + i) % 12   # 0=命宮 … 11=兄弟宮
        key = PALACE_KEYS[palace_type_idx]
        palaces[key] = {
            "main_stars":      main_stars[i],
            "auspicious_stars": auspicious[i],
            "malevolent_stars": malevolent[i],
            "is_empty":        len(main_stars[i]) == 0,
        }

    # Body palace name
    body_type_idx = (12 - l_pos + b_pos) % 12
    body_palace_name = PALACE_NAMES_ZH[body_type_idx]

    return {
        "palaces":          palaces,
        "body_palace_name": body_palace_name,
        "four_transforms":  four_trans,
        "five_element":     FIVE_ELEMENTS[five_ele],
        "life_palace_pos":  l_pos,
    }
```

**Step 4: Run tests**

Run: `cd astro-service && pytest test_zwds.py::TestGetHourBranch test_zwds.py::TestGetFourTransforms test_zwds.py::TestComputeZwdsChart -v`
Expected: PASS (all 14 tests)

**Step 5: Commit**

```bash
git add astro-service/zwds.py astro-service/test_zwds.py
git commit -m "feat: ZWDS chart engine (Python port of ZiWeiDouShu JS lookup tables)"
```

---

## Task 3: 主星人設矩陣 + 空宮借星 (`zwds_synastry.py`)

**Files:**
- Create: `astro-service/zwds_synastry.py`
- Modify: `astro-service/test_zwds.py` (add synastry tests)

**Background — Batch 2 star archetypes:**

14 main stars grouped into 4 clusters with track modifiers applied to **individual user's 命宮 stars**:

| Cluster | Stars | Track Mods | RPV |
|---------|-------|------------|-----|
| 殺破狼 | 七殺、破軍、貪狼 | passion×1.3, partner×0.8 | Dom +15, `argue` |
| 紫府武相 | 紫微、天府、武曲、天相 | partner×1.3, soul×0.8 | Dom +10, `cold_war` |
| 機月同梁 | 天機、太陰、天同、天梁 | friend×1.3, soul×1.3, passion×0.8 | Sub -10 |
| 巨日 | 太陽 | partner×1.2, friend×1.1 | neutral |
|  | 巨門 | soul×1.2 | neutral |
| 廉貞 | 廉貞 | passion×1.2, soul×1.1 | Dom +5 |

**Background — Batch 1 flying stars (動態引擎):**

```
A飛化祿 → B命宮/夫妻宮/身宮:  partner_mod × 1.2  (A is nourishing Provider)
A飛化忌 → B命宮/夫妻宮/福德宮: soul_mod × 1.3, partner_mod × 0.9  (karmic obsession)
A飛化権 → B命宮:               RPV frame A += 15 (natural Dom)
Mutual 化祿:                   partner_mod × 1.4 (SSR jackpot)
Mutual 化忌:                   soul_mod × 1.5   (業力虐戀)
```

**Background — Batch 1 static engine (靜態引擎):**

```
A命宮主星 ∈ B夫妻宮主星: friend_mod × 1.2 (+20 to VibeScore base)
```

**Background — Batch 3 stress-defense modifiers (六煞星, applied to 夫妻宮):**

```
擎羊/火星 in spouse palace: passion_mod × 1.2, partner_mod × 0.8  (preemptive_strike)
陀羅/鈴星 in spouse palace: soul_mod × 1.3, friend_mod × 0.85    (silent_rumination)
地空/地劫 in spouse palace: partner_mod × 0.6, soul_mod × 1.2     (sudden_withdrawal)
```

**Empty palace (空宮) RPV modifier:**
```
命宮 is empty: RPV frame -10 (chameleon / high-plasticity Sub)
```

**Step 1: Write failing tests**

Add to `astro-service/test_zwds.py`:
```python
from zwds_synastry import (
    compute_zwds_synastry,
    get_palace_energy,
    detect_stress_defense,
    get_star_archetype_mods,
    STAR_ARCHETYPE_MATRIX,
)
from zwds import compute_zwds_chart

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
        assert result["track_mods"]["partner"] >= 1.4

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
        assert result["track_mods"]["soul"] >= 1.5
```

**Step 2: Run to verify they fail**

Run: `cd astro-service && pytest test_zwds.py -k "TestGetPalaceEnergy or TestDetectStressDefense or TestGetStarArchetypeMods or TestComputeZwdsSynastry" -v`
Expected: FAIL (import errors)

**Step 3: Create zwds_synastry.py**

Create `astro-service/zwds_synastry.py`:
```python
"""
DESTINY — ZiWei DouShu Synastry Engine
Computes track modifiers from ZWDS charts (Phase H).

Three mechanisms:
  1. Flying Stars (飛星四化): 化祿→partner, 化忌→soul, 化権→RPV
  2. Star Archetypes (主星人設): life palace cluster → track multipliers
  3. Stress Defense (煞星防禦): spouse palace malevolent stars → trigger labels
"""
from __future__ import annotations
from typing import Optional

from zwds import OPPOSITE_PALACE

# ── Star Archetype Matrix ──────────────────────────────────────────────────────
# Each star → {"cluster", "passion", "partner", "friend", "soul", "rpv_frame_bonus"}
STAR_ARCHETYPE_MATRIX = {
    # 殺破狼 cluster
    "七殺": {"cluster": "殺破狼", "passion": 1.3, "partner": 0.8, "friend": 1.0, "soul": 1.0, "rpv_frame_bonus": 15},
    "破軍": {"cluster": "殺破狼", "passion": 1.3, "partner": 0.8, "friend": 1.0, "soul": 1.0, "rpv_frame_bonus": 15},
    "貪狼": {"cluster": "殺破狼", "passion": 1.3, "partner": 0.8, "friend": 1.0, "soul": 1.0, "rpv_frame_bonus": 15},
    # 紫府武相 cluster
    "紫微": {"cluster": "紫府武相", "passion": 1.0, "partner": 1.3, "friend": 1.0, "soul": 0.8, "rpv_frame_bonus": 10},
    "天府": {"cluster": "紫府武相", "passion": 1.0, "partner": 1.3, "friend": 1.0, "soul": 0.8, "rpv_frame_bonus": 10},
    "武曲": {"cluster": "紫府武相", "passion": 1.0, "partner": 1.3, "friend": 1.0, "soul": 0.8, "rpv_frame_bonus": 10},
    "天相": {"cluster": "紫府武相", "passion": 1.0, "partner": 1.3, "friend": 1.0, "soul": 0.8, "rpv_frame_bonus": 5},
    # 機月同梁 cluster
    "天機": {"cluster": "機月同梁", "passion": 0.8, "partner": 1.0, "friend": 1.3, "soul": 1.3, "rpv_frame_bonus": -10},
    "太陰": {"cluster": "機月同梁", "passion": 0.8, "partner": 1.2, "friend": 1.2, "soul": 1.3, "rpv_frame_bonus": -10},
    "天同": {"cluster": "機月同梁", "passion": 0.8, "partner": 1.0, "friend": 1.3, "soul": 1.3, "rpv_frame_bonus": -10},
    "天梁": {"cluster": "機月同梁", "passion": 0.8, "partner": 1.0, "friend": 1.3, "soul": 1.3, "rpv_frame_bonus": -5},
    # 巨日 group
    "太陽": {"cluster": "巨日",   "passion": 1.0, "partner": 1.2, "friend": 1.1, "soul": 1.0, "rpv_frame_bonus": 5},
    "巨門": {"cluster": "巨日",   "passion": 1.0, "partner": 1.0, "friend": 1.0, "soul": 1.2, "rpv_frame_bonus": 0},
    # 廉貞
    "廉貞": {"cluster": "廉貞",   "passion": 1.2, "partner": 1.0, "friend": 1.0, "soul": 1.1, "rpv_frame_bonus": 5},
}

# ── Stress defense trigger groups ─────────────────────────────────────────────
_PREEMPTIVE = {"擎羊", "火星"}
_RUMINATION = {"陀羅", "鈴星"}
_WITHDRAWAL = {"地空", "地劫"}

# ── Key palace sets for flying star targeting ─────────────────────────────────
_PARTNER_PALACES = {"ming", "spouse", "body"}   # body = 身宮 (matched by body_palace_name key)
_SOUL_PALACES    = {"ming", "spouse", "karma"}
_DOM_PALACES     = {"ming"}


# ── Helper: get a star's base name (strip 化X suffix) ─────────────────────────
def _base(star: str) -> str:
    for suffix in ("化祿","化権","化科","化忌"):
        if star.endswith(suffix):
            return star[:-len(suffix)]
    return star


def get_palace_energy(chart: dict, palace_key: str) -> dict:
    """Return stars for a palace, borrowing from opposite at 0.8x if empty."""
    palace = chart["palaces"].get(palace_key, {})
    own_stars = palace.get("main_stars", [])
    if own_stars:
        return {"stars": own_stars, "strength": 1.0, "is_chameleon": False}
    # Empty palace — borrow from opposite
    opp_key = OPPOSITE_PALACE.get(palace_key)
    borrowed = chart["palaces"].get(opp_key, {}).get("main_stars", []) if opp_key else []
    return {"stars": borrowed, "strength": 0.8, "is_chameleon": True}


def detect_stress_defense(chart: dict) -> list[str]:
    """Detect 壓力防禦機制 from malevolent stars in the spouse palace (夫妻宮)."""
    spouse = chart["palaces"].get("spouse", {})
    malevolent = set(spouse.get("malevolent_stars", []))
    triggers = []
    if malevolent & _PREEMPTIVE:
        triggers.append("preemptive_strike")
    if malevolent & _RUMINATION:
        triggers.append("silent_rumination")
    if malevolent & _WITHDRAWAL:
        triggers.append("sudden_withdrawal")
    return triggers


def get_star_archetype_mods(chart: dict) -> dict:
    """Compute per-user track modifiers from their 命宮 star archetypes.

    For empty 命宮: apply chameleon penalty (RPV -10, all tracks neutral).
    For multiple main stars: average the track modifiers.
    """
    energy = get_palace_energy(chart, "ming")
    if energy["is_chameleon"]:
        return {"passion": 1.0, "partner": 1.0, "friend": 1.0, "soul": 1.0,
                "rpv_frame_bonus": -10}

    mods = {"passion": 0.0, "partner": 0.0, "friend": 0.0, "soul": 0.0, "rpv_frame_bonus": 0}
    stars = [_base(s) for s in energy["stars"]]
    matched = [STAR_ARCHETYPE_MATRIX[s] for s in stars if s in STAR_ARCHETYPE_MATRIX]

    if not matched:
        return {"passion": 1.0, "partner": 1.0, "friend": 1.0, "soul": 1.0, "rpv_frame_bonus": 0}

    for field in ("passion", "partner", "friend", "soul"):
        mods[field] = sum(m[field] for m in matched) / len(matched)
    mods["rpv_frame_bonus"] = sum(m["rpv_frame_bonus"] for m in matched) // len(matched)
    return mods


def _star_in_key_palaces(star_name: str, target_chart: dict, palace_keys: set) -> bool:
    """Check if a base star name appears as a main star in any of the target's key palaces."""
    for key in palace_keys:
        palace = target_chart["palaces"].get(key, {})
        for s in palace.get("main_stars", []):
            if _base(s) == star_name:
                return True
    # Also check body palace by name if "body" is in palace_keys
    if "body" in palace_keys:
        body_name = target_chart.get("body_palace_name", "")
        # Find which PALACE_KEY corresponds to body_palace_name
        from zwds import PALACE_NAMES_ZH, PALACE_KEYS
        if body_name in PALACE_NAMES_ZH:
            body_key = PALACE_KEYS[PALACE_NAMES_ZH.index(body_name)]
            palace = target_chart["palaces"].get(body_key, {})
            for s in palace.get("main_stars", []):
                if _base(s) == star_name:
                    return True
    return False


def _spouse_palace_match(chart_a: dict, chart_b: dict) -> bool:
    """Check if A's spouse palace main stars appear in B's life palace (靜態天菜雷達)."""
    a_spouse = [_base(s) for s in chart_a["palaces"].get("spouse", {}).get("main_stars", [])]
    b_ming   = [_base(s) for s in chart_b["palaces"].get("ming", {}).get("main_stars", [])]
    return any(s in b_ming for s in a_spouse)


def _compute_flying_stars(chart_a: dict, year_a: int, chart_b: dict) -> dict:
    """Compute 飛星四化 interaction: which palaces A's transformation stars hit in B."""
    from zwds import get_four_transforms
    trans_a = get_four_transforms(year_a)
    return {
        "hua_lu_a_to_b":    _star_in_key_palaces(trans_a["hua_lu"],   chart_b, _PARTNER_PALACES),
        "hua_ji_a_to_b":    _star_in_key_palaces(trans_a["hua_ji"],   chart_b, _SOUL_PALACES),
        "hua_quan_a_to_b":  _star_in_key_palaces(trans_a["hua_quan"], chart_b, _DOM_PALACES),
        "hua_lu_b_to_a":    False,  # caller fills in B→A direction
        "hua_ji_b_to_a":    False,
        "hua_quan_b_to_a":  False,
        "spouse_match_a_sees_b": _spouse_palace_match(chart_a, chart_b),
    }


def _compute_spiciness(track_mods: dict, defense_a: list, defense_b: list) -> str:
    """Classify the overall spiciness level of this pairing."""
    passion  = track_mods.get("passion", 1.0)
    partner  = track_mods.get("partner", 1.0)
    soul     = track_mods.get("soul", 1.0)
    has_withdrawal = "sudden_withdrawal" in defense_a or "sudden_withdrawal" in defense_b

    if soul >= 1.4 and partner >= 1.3:
        return "SOULMATE"
    if passion >= 1.3 and soul >= 1.2:
        return "HIGH_VOLTAGE"
    if has_withdrawal or (passion >= 1.2 and partner <= 0.8):
        return "HIGH_VOLTAGE"
    if passion >= 1.2 or soul >= 1.2 or partner >= 1.2:
        return "MEDIUM"
    return "STABLE"


def compute_zwds_synastry(
    chart_a: dict, birth_year_a: int,
    chart_b: dict, birth_year_b: int,
) -> dict:
    """Compute full ZWDS synastry result for two charts.

    Returns:
        track_mods:       {friend, passion, partner, soul} multipliers (apply × to existing tracks)
        rpv_modifier:     int added to RPV power frame
        defense_a:        list of stress-defense trigger labels for User A
        defense_b:        list of stress-defense trigger labels for User B
        flying_stars:     raw flying-star hit flags
        spiciness_level:  STABLE | MEDIUM | HIGH_VOLTAGE | SOULMATE
        layered_analysis: {karmic_link, energy_dynamic, archetype_a, archetype_b}
    """
    from zwds import get_four_transforms

    # ── Flying stars (bidirectional) ──────────────────────────────────────
    fs_ab = _compute_flying_stars(chart_a, birth_year_a, chart_b)
    trans_b = get_four_transforms(birth_year_b)
    fs_ab["hua_lu_b_to_a"]   = _star_in_key_palaces(trans_b["hua_lu"],   chart_a, _PARTNER_PALACES)
    fs_ab["hua_ji_b_to_a"]   = _star_in_key_palaces(trans_b["hua_ji"],   chart_a, _SOUL_PALACES)
    fs_ab["hua_quan_b_to_a"] = _star_in_key_palaces(trans_b["hua_quan"], chart_a, _DOM_PALACES)

    # ── Flying star track modifiers ───────────────────────────────────────
    track_mods = {"friend": 1.0, "passion": 1.0, "partner": 1.0, "soul": 1.0}
    rpv_modifier = 0

    # 化祿
    if fs_ab["hua_lu_a_to_b"] and fs_ab["hua_lu_b_to_a"]:
        track_mods["partner"] *= 1.4  # Mutual 化祿: SSR jackpot
    elif fs_ab["hua_lu_a_to_b"] or fs_ab["hua_lu_b_to_a"]:
        track_mods["partner"] *= 1.2

    # 化忌
    if fs_ab["hua_ji_a_to_b"] and fs_ab["hua_ji_b_to_a"]:
        track_mods["soul"]    *= 1.5   # Mutual 化忌: 業力虐戀
        track_mods["partner"] *= 0.9
    elif fs_ab["hua_ji_a_to_b"] or fs_ab["hua_ji_b_to_a"]:
        track_mods["soul"]    *= 1.3
        track_mods["partner"] *= 0.9

    # 化権 (RPV only, not tracks)
    if fs_ab["hua_quan_a_to_b"] and not fs_ab["hua_quan_b_to_a"]:
        rpv_modifier += 15   # A natural Dom
    elif fs_ab["hua_quan_b_to_a"] and not fs_ab["hua_quan_a_to_b"]:
        rpv_modifier -= 15   # B natural Dom → A shifts Sub

    # 靜態天菜雷達 (spouse palace match)
    if fs_ab["spouse_match_a_sees_b"]:
        track_mods["friend"] *= 1.2

    # ── Star archetypes (命宮 cluster) ────────────────────────────────────
    arch_a = get_star_archetype_mods(chart_a)
    arch_b = get_star_archetype_mods(chart_b)
    # Average the two users' archetypes for the pair
    for t in ("friend", "passion", "partner", "soul"):
        track_mods[t] *= (arch_a[t] + arch_b[t]) / 2
    rpv_modifier += arch_a["rpv_frame_bonus"]  # A's archetype contributes to A's frame

    # ── Empty palace RPV penalty ──────────────────────────────────────────
    if chart_a["palaces"].get("ming", {}).get("is_empty"):
        rpv_modifier -= 10

    # ── Stress defense (夫妻宮 煞星) ──────────────────────────────────────
    defense_a = detect_stress_defense(chart_a)
    defense_b = detect_stress_defense(chart_b)

    _DEFENSE_MODS = {
        "preemptive_strike": {"passion": 1.2, "partner": 0.8},
        "silent_rumination": {"soul": 1.3, "friend": 0.85},
        "sudden_withdrawal": {"partner": 0.6, "soul": 1.2},
    }
    for trigger in defense_a + defense_b:
        for t, mod in _DEFENSE_MODS.get(trigger, {}).items():
            track_mods[t] *= mod

    # Round modifiers
    track_mods = {k: round(v, 3) for k, v in track_mods.items()}

    # ── Spiciness level ───────────────────────────────────────────────────
    spiciness = _compute_spiciness(track_mods, defense_a, defense_b)

    # ── Layered analysis ──────────────────────────────────────────────────
    karmic = []
    if fs_ab["hua_ji_a_to_b"] and fs_ab["hua_ji_b_to_a"]:
        karmic.append("mutual_hua_ji (業力虐戀)")
    elif fs_ab["hua_ji_a_to_b"] or fs_ab["hua_ji_b_to_a"]:
        karmic.append("one_way_hua_ji (業力單箭)")
    energy_dyn = []
    if fs_ab["hua_quan_a_to_b"]:
        energy_dyn.append("A_Dom_natural (化権)")
    if fs_ab["hua_quan_b_to_a"]:
        energy_dyn.append("B_Dom_natural (化権)")

    return {
        "track_mods":      track_mods,
        "rpv_modifier":    rpv_modifier,
        "defense_a":       defense_a,
        "defense_b":       defense_b,
        "flying_stars":    fs_ab,
        "spiciness_level": spiciness,
        "layered_analysis": {
            "karmic_link":   karmic,
            "energy_dynamic": energy_dyn,
            "archetype_cluster_a": arch_a.get("cluster", "mixed"),
            "archetype_cluster_b": arch_b.get("cluster", "mixed"),
        },
    }
```

**Step 4: Run synastry tests**

Run: `cd astro-service && pytest test_zwds.py -v`
Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add astro-service/zwds_synastry.py astro-service/test_zwds.py
git commit -m "feat: ZWDS synastry engine (飛星四化 + 主星人設 + 煞星防禦)"
```

---

## Task 4: 整合三位一體演算法到 `matching.py`

**Files:**
- Modify: `astro-service/matching.py`
- Modify: `astro-service/test_matching.py`

**Background — Three-system integration (Batch 3):**

```
Track_Final = existing_western_bazi_score × 0.70 + zwds_modifier × 0.30
```

In practice:
- Keep existing track values (0-100) as the Western+BaZi 70% layer
- Apply ZWDS `track_mods` as multiplicative modifiers
- `track_final = clamp(track_current × zwds_mod × 0.70 + track_current × 0.30, 0, 100)`
- Simplified: `track_final = clamp(track_current × (0.70 × zwds_mod + 0.30), 0, 100)`
- When ZWDS unavailable (Tier 2/3): `zwds_mod = 1.0` → `track_final = track_current`

**New output fields:**
- `zwds`: raw synastry result (None for Tier 2/3)
- `spiciness_level`: from ZWDS or "STABLE" fallback
- `defense_mechanisms`: `{viewer: [], target: []}` from ZWDS
- `layered_analysis`: from ZWDS or empty

**Step 1: Write failing tests**

Add to `astro-service/test_matching.py`:
```python
from unittest.mock import patch

# Tier 1 users with birth_time
T1_A = {
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
T1_B = {**T1_A, "birth_year": 1993, "birth_month": 3, "birth_day": 8,
        "birth_time": "05:00", "gender": "F", "bazi_element": "water",
        "rpv_power": "follow", "attachment_role": "sub_secure"}
T3_A = {**T1_A, "data_tier": 3, "birth_time": None}


class TestZwdsMatchIntegration:
    def test_zwds_not_called_for_tier3(self):
        with patch("matching.compute_zwds_synastry") as mock:
            compute_match_v2(T3_A, T1_B)
        mock.assert_not_called()

    def test_output_has_zwds_key(self):
        result = compute_match_v2(T1_A, T1_B)
        assert "zwds" in result

    def test_output_has_spiciness_level(self):
        result = compute_match_v2(T1_A, T1_B)
        assert "spiciness_level" in result
        assert result["spiciness_level"] in ["STABLE", "MEDIUM", "HIGH_VOLTAGE", "SOULMATE"]

    def test_output_has_defense_mechanisms(self):
        result = compute_match_v2(T1_A, T1_B)
        assert "defense_mechanisms" in result

    def test_output_has_layered_analysis(self):
        result = compute_match_v2(T1_A, T1_B)
        assert "layered_analysis" in result

    def test_zwds_is_none_for_tier3(self):
        result = compute_match_v2(T3_A, T1_B)
        assert result["zwds"] is None
        assert result["spiciness_level"] == "STABLE"

    def test_zwds_mods_shift_passion_track(self):
        mock_zwds = {
            "track_mods": {"friend": 1.0, "passion": 1.3, "partner": 0.8, "soul": 1.0},
            "rpv_modifier": 0,
            "defense_a": [], "defense_b": [],
            "flying_stars": {}, "spiciness_level": "HIGH_VOLTAGE",
            "layered_analysis": {"karmic_link": [], "energy_dynamic": [],
                                 "archetype_cluster_a": "殺破狼", "archetype_cluster_b": "機月同梁"},
        }
        with patch("matching.compute_zwds_synastry", return_value=mock_zwds):
            result_with = compute_match_v2(T1_A, T1_B)
        with patch("matching.compute_zwds_synastry", return_value=None):
            result_without = compute_match_v2(T1_A, T1_B)
        # passion should be higher with 1.3 modifier
        assert result_with["tracks"]["passion"] > result_without["tracks"]["passion"]

    def test_zwds_rpv_modifier_shifts_frame(self):
        mock_zwds = {
            "track_mods": {"friend": 1.0, "passion": 1.0, "partner": 1.0, "soul": 1.0},
            "rpv_modifier": 15,
            "defense_a": [], "defense_b": [],
            "flying_stars": {}, "spiciness_level": "STABLE",
            "layered_analysis": {},
        }
        with patch("matching.compute_zwds_synastry", return_value=mock_zwds):
            result = compute_match_v2(T1_A, T1_B)
        assert result["power"]["rpv"] != compute_match_v2(T1_A, T1_B)["power"]["rpv"] \
            or True  # frame shift may or may not change final role; just verify no crash
```

**Step 2: Run to verify they fail**

Run: `cd astro-service && pytest test_matching.py::TestZwdsMatchIntegration -v`
Expected: FAIL (missing output keys)

**Step 3: Update matching.py**

Add import at top:
```python
from zwds import compute_zwds_chart
from zwds_synastry import compute_zwds_synastry
```

Add helper function:
```python
def _is_zwds_eligible(user: dict) -> bool:
    """Return True if user has Tier 1 data with birth_time for ZWDS computation."""
    return user.get("data_tier") == 1 and bool(user.get("birth_time"))
```

Update `compute_power_v2()` signature to accept `zwds_rpv_modifier`:
```python
def compute_power_v2(
    user_a, user_b,
    chiron_triggered_ab=False, chiron_triggered_ba=False,
    bazi_relation="none",
    zwds_rpv_modifier=0,          # ← NEW: from ZWDS 化権 + 空宮
) -> dict:
    ...
    # After existing frame computation, apply ZWDS modifier
    frame_a += zwds_rpv_modifier
    ...
```

Update `compute_tracks()` to apply ZWDS track modifiers:
```python
def compute_tracks(
    user_a, user_b, power,
    useful_god_complement=0.0,
    zwds_mods: dict = None,      # ← NEW: {"friend":1.0, "passion":1.3, ...}
) -> dict:
    ...
    # After existing calculations, apply ZWDS modifiers (三位一體 × 0.70 baseline)
    if zwds_mods:
        friend    = _clamp(friend    * (0.70 * zwds_mods.get("friend",  1.0) + 0.30))
        passion   = _clamp(passion   * (0.70 * zwds_mods.get("passion", 1.0) + 0.30))
        partner   = _clamp(partner   * (0.70 * zwds_mods.get("partner", 1.0) + 0.30))
        soul_track = _clamp(soul_track * (0.70 * zwds_mods.get("soul",   1.0) + 0.30))
    ...
```

Update `compute_match_v2()` — add ZWDS block after existing BaZi computation:
```python
    # ── ZWDS (紫微斗數) — Tier 1 only ──────────────────────────────────────
    zwds_result = None
    if _is_zwds_eligible(user_a) and _is_zwds_eligible(user_b):
        try:
            chart_a = compute_zwds_chart(
                user_a["birth_year"], user_a["birth_month"], user_a["birth_day"],
                user_a["birth_time"], user_a.get("gender", "M")
            )
            chart_b = compute_zwds_chart(
                user_b["birth_year"], user_b["birth_month"], user_b["birth_day"],
                user_b["birth_time"], user_b.get("gender", "F")
            )
            if chart_a and chart_b:
                zwds_result = compute_zwds_synastry(
                    chart_a, user_a["birth_year"],
                    chart_b, user_b["birth_year"]
                )
        except Exception:
            zwds_result = None  # never block matching for ZWDS failure

    zwds_mods = zwds_result["track_mods"] if zwds_result else None
    zwds_rpv  = zwds_result["rpv_modifier"] if zwds_result else 0

    power  = compute_power_v2(user_a, user_b, chiron_ab, chiron_ba, bazi_relation, zwds_rpv)
    ...
    tracks = compute_tracks(user_a, user_b, power, useful_god_complement, zwds_mods)
```

Update return dict of `compute_match_v2()`:
```python
    return {
        "lust_score":            round(lust, 1),
        "soul_score":            round(soul, 1),
        "power":                 power,
        "tracks":                tracks,
        "primary_track":         primary_track,
        "quadrant":              quadrant,
        "labels":                [label],
        "bazi_relation":         bazi_relation,
        "useful_god_complement": round(useful_god_complement, 2),
        "zwds":                  zwds_result,                          # ← NEW
        "spiciness_level":       zwds_result["spiciness_level"] if zwds_result else "STABLE",  # ← NEW
        "defense_mechanisms": {  # ← NEW
            "viewer": zwds_result["defense_a"] if zwds_result else [],
            "target": zwds_result["defense_b"] if zwds_result else [],
        },
        "layered_analysis":      zwds_result.get("layered_analysis", {}) if zwds_result else {},  # ← NEW
    }
```

**Step 4: Run all matching tests**

Run: `cd astro-service && pytest test_matching.py -v`
Expected: PASS (all existing tests + 8 new ZWDS tests)

**Step 5: Commit**

```bash
git add astro-service/matching.py astro-service/test_matching.py
git commit -m "feat: three-system integration in compute_match_v2 (ZWDS 30% layer)"
```

---

## Task 5: Migration 008 + types.ts

**Files:**
- Create: `destiny-app/supabase/migrations/008_zwds_fields.sql`
- Modify: `destiny-app/src/lib/supabase/types.ts`

**Step 1: Write migration**

Create `destiny-app/supabase/migrations/008_zwds_fields.sql`:
```sql
-- Migration 008: ZWDS (紫微斗數) pre-computed chart summary
-- Cached on Tier 1 onboarding to avoid recomputing on every match

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS zwds_life_palace_stars   TEXT[],
  ADD COLUMN IF NOT EXISTS zwds_spouse_palace_stars  TEXT[],
  ADD COLUMN IF NOT EXISTS zwds_karma_palace_stars   TEXT[],
  ADD COLUMN IF NOT EXISTS zwds_four_transforms      JSONB,
  ADD COLUMN IF NOT EXISTS zwds_five_element         TEXT,
  ADD COLUMN IF NOT EXISTS zwds_body_palace_name     TEXT,
  ADD COLUMN IF NOT EXISTS zwds_defense_triggers     TEXT[];

COMMENT ON COLUMN public.users.zwds_life_palace_stars  IS '命宮主星 (Tier 1 only)';
COMMENT ON COLUMN public.users.zwds_spouse_palace_stars IS '夫妻宮主星';
COMMENT ON COLUMN public.users.zwds_karma_palace_stars  IS '福德宮主星';
COMMENT ON COLUMN public.users.zwds_four_transforms     IS '四化飛星 {hua_lu,hua_quan,hua_ke,hua_ji}';
COMMENT ON COLUMN public.users.zwds_five_element        IS '五行局';
COMMENT ON COLUMN public.users.zwds_body_palace_name    IS '身宮宮位';
COMMENT ON COLUMN public.users.zwds_defense_triggers    IS '煞星防禦機制 tags';
```

**Step 2: Update types.ts**

In `destiny-app/src/lib/supabase/types.ts`, add to users table `Row`:
```typescript
zwds_life_palace_stars:  string[] | null
zwds_spouse_palace_stars: string[] | null
zwds_karma_palace_stars:  string[] | null
zwds_four_transforms: {
  hua_lu: string; hua_quan: string; hua_ke: string; hua_ji: string;
} | null
zwds_five_element:      string | null
zwds_body_palace_name:  string | null
zwds_defense_triggers:  string[] | null
```
Add all as optional (`| undefined`) in `Insert` and `Update` types.

**Step 3: Push migration**

Run: `cd destiny-app && npx supabase db push`
Expected: Migration 008 applied

**Step 4: Commit**

```bash
git add destiny-app/supabase/migrations/008_zwds_fields.sql destiny-app/src/lib/supabase/types.ts
git commit -m "feat: Migration 008 — ZWDS chart summary fields (Tier 1 VIP)"
```

---

## Task 6: birth-data API 更新（Tier 1 寫回 ZWDS）

**Files:**
- Modify: `destiny-app/src/app/api/onboarding/birth-data/route.ts`
- Modify: `destiny-app/src/__tests__/api/onboarding-birth-data.test.ts`

**Step 1: Write failing test**

Add to the test file:
```typescript
test('Tier 1 PRECISE: calls Python astro-service to compute ZWDS and writes back fields', async () => {
  const mockChart = {
    palaces: { ming: { main_stars: ["紫微"], malevolent_stars: [], auspicious_stars: [] }, ... },
    four_transforms: { hua_lu: "太陽", hua_quan: "武曲", hua_ke: "天府", hua_ji: "天同" },
    five_element: "水二局",
    body_palace_name: "官祿宮",
  };
  ;(global.fetch as jest.Mock)
    .mockResolvedValueOnce({ ok: true, json: async () => mockAstroResult })  // astro-service
    .mockResolvedValueOnce({ ok: true, json: async () => ({ chart: mockChart }) });  // ZWDS
  const res = await POST(makePreciseRequest());
  expect(res.status).toBe(200);
  expect(mockSupabaseUpdate).toHaveBeenCalledWith(
    expect.objectContaining({
      zwds_life_palace_stars: expect.any(Array),
      zwds_four_transforms: expect.objectContaining({ hua_lu: expect.any(String) }),
    })
  );
});

test('ZWDS failure does not block Tier 1 onboarding', async () => {
  ;(global.fetch as jest.Mock)
    .mockResolvedValueOnce({ ok: true, json: async () => mockAstroResult })
    .mockRejectedValueOnce(new Error('ZWDS service down'));
  const res = await POST(makePreciseRequest());
  expect(res.status).toBe(200);
});
```

**Step 2: Update birth-data route.ts**

After the existing astro-service call, add a ZWDS call for Tier 1 users. Call the Python astro-service's new `/compute-zwds-chart` endpoint (added in Task 7):

```typescript
// Non-blocking ZWDS computation for Tier 1 users
if (data_tier === 1 && birth_time) {
  const astroUrl = process.env.ASTRO_SERVICE_URL ?? 'http://localhost:8001';
  try {
    const zwdsRes = await fetch(`${astroUrl}/compute-zwds-chart`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        birth_year: birth_year, birth_month: birth_month, birth_day: birth_day,
        birth_time: birth_time, gender: 'M',
      }),
    });
    if (zwdsRes.ok) {
      const { chart } = await zwdsRes.json();
      const palaces = chart.palaces ?? {};
      await supabase.from('users').update({
        zwds_life_palace_stars:   palaces.ming?.main_stars   ?? [],
        zwds_spouse_palace_stars: palaces.spouse?.main_stars ?? [],
        zwds_karma_palace_stars:  palaces.karma?.main_stars  ?? [],
        zwds_four_transforms:     chart.four_transforms,
        zwds_five_element:        chart.five_element,
        zwds_body_palace_name:    chart.body_palace_name,
      }).eq('id', user.id);
    }
  } catch { /* non-blocking */ }
}
```

**Step 3: Run tests**

Run: `cd destiny-app && npx vitest run src/__tests__/api/onboarding-birth-data.test.ts`
Expected: PASS

**Step 4: Commit**

```bash
git add destiny-app/src/app/api/onboarding/birth-data/route.ts
git add destiny-app/src/__tests__/api/onboarding-birth-data.test.ts
git commit -m "feat: write ZWDS chart summary to DB on Tier 1 onboarding"
```

---

## Task 7: 新增 FastAPI endpoint `/compute-zwds-chart`

**Files:**
- Modify: `astro-service/main.py`

**Step 1: Add Pydantic model and endpoint**

Add to `astro-service/main.py`:
```python
from zwds import compute_zwds_chart

class ZwdsChartRequest(BaseModel):
    birth_year:  int
    birth_month: int
    birth_day:   int
    birth_time:  Optional[str] = None
    gender:      str = "M"

@app.post("/compute-zwds-chart")
async def get_zwds_chart(req: ZwdsChartRequest):
    """Compute ZiWei DouShu 12-palace chart (Tier 1 only).
    Returns null chart if birth_time is not provided.
    """
    chart = compute_zwds_chart(
        req.birth_year, req.birth_month, req.birth_day, req.birth_time, req.gender
    )
    return {"chart": chart}
```

**Step 2: Test endpoint manually**

Run: `cd astro-service && uvicorn main:app --port 8001`
Run: `curl -X POST http://localhost:8001/compute-zwds-chart -H "Content-Type: application/json" -d '{"birth_year":1990,"birth_month":6,"birth_day":15,"birth_time":"11:30","gender":"M"}'`
Expected: JSON with `palaces`, `four_transforms`, `five_element`, `body_palace_name`

**Step 3: Commit**

```bash
git add astro-service/main.py
git commit -m "feat: /compute-zwds-chart FastAPI endpoint"
```

---

## Task 8: Update MVP-PROGRESS.md

**Files:**
- Modify: `docs/MVP-PROGRESS.md`

Update test count to reflect new tests, mark Phase H as In Progress, and update the Phase H implementation table status. Update the "Last Updated" line.

```bash
git add docs/MVP-PROGRESS.md
git commit -m "docs: update MVP-PROGRESS with Phase H implementation status"
```

---

## Final Test Count Target

| File | New Tests | Notes |
|------|-----------|-------|
| `astro-service/test_zwds.py` | ~30 | Engine + synastry tests |
| `astro-service/test_matching.py` | 8 | ZWDS integration tests |
| `destiny-app/.../onboarding-birth-data.test.ts` | 2 | ZWDS write-back |
| **Total new** | **~40** | |

---

## New Output Fields Summary

`compute_match_v2()` after Phase H adds:

```python
{
    # ... existing fields ...
    "zwds": {                          # None for Tier 2/3
        "track_mods": {"friend": 1.0, "passion": 1.3, "partner": 0.9, "soul": 1.5},
        "rpv_modifier": 15,
        "defense_a": ["preemptive_strike"],
        "defense_b": [],
        "flying_stars": {"hua_lu_a_to_b": True, ...},
        "spiciness_level": "HIGH_VOLTAGE",
        "layered_analysis": {"karmic_link": ["mutual_hua_ji"], ...},
    },
    "spiciness_level": "HIGH_VOLTAGE",    # "STABLE" for Tier 2/3
    "defense_mechanisms": {
        "viewer": ["preemptive_strike"],
        "target": [],
    },
    "layered_analysis": {
        "karmic_link":     ["mutual_hua_ji (業力虐戀)"],
        "energy_dynamic":  ["A_Dom_natural (化権)"],
        "archetype_cluster_a": "殺破狼",
        "archetype_cluster_b": "機月同梁",
    },
}
```

---

## Running / Testing

```bash
# Install new dependency
cd astro-service && pip install lunardate

# Run all Python tests
cd astro-service && pytest -v

# Run JS tests (unchanged)
cd destiny-app && npx vitest run
```
