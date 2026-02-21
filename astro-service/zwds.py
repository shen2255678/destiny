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
    if y1 < len(STAR_B06[0]):
        malevolent[STAR_B06[0][y1]].append("擎羊")
    if y1 < len(STAR_B06[1]):
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
