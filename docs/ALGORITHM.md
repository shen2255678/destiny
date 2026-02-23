# DESTINY 配對演算法技術規格

本文件提供 DESTINY 配對引擎完整的技術規格，適合 AI 助理、開發者在
理解、除錯或擴充演算法時參考，不需要閱讀原始碼。

---

## 系統概覽

配對引擎位於 `astro-service/matching.py`，主要入口函數為
`compute_match_v2(user_a, user_b)`，整合五個維度：

1. **西洋占星**（Western Astrology）— 行星星座相位分數
2. **八字日主五行**（BaZi Five Elements）— 相生相剋關係
3. **RPV**（Relational Power Variables）— 衝突風格 × 權力偏好 × 能量模式
4. **依戀心理學**（Attachment Theory）— 依戀風格相容矩陣
5. **紫微斗數**（ZiWei DouShu, ZWDS）— 命宮主星 × 飛星四化 × 夫妻宮
   煞星（Tier 1 only）
6. **暗黑合盤修正器**（Shadow & Synastry Modifiers）— Chiron / Vertex / Lilith /
   Lunar Nodes / 第七宮 Descendant 疊圖（v1.9）

> **Note:** ZWDS 為疊加修正器（multiplier），不覆蓋既有分數。若
> 任一方為 Tier 2/3，ZWDS 區塊回傳 `null`，配對繼續以前四個維度
> 正常計算。

**輸出結構：**

```json
{
  "lust_score":    74.3,
  "soul_score":    68.1,
  "power": {
    "rpv": 20.0,
    "frame_break": false,
    "viewer_role": "Dom",
    "target_role": "Sub"
  },
  "tracks": {
    "friend": 45.0, "passion": 78.5,
    "partner": 62.0, "soul": 55.0
  },
  "primary_track": "passion",
  "quadrant": "lover",
  "labels": ["✦ 激情型連結"],
  "bazi_relation": "a_restricts_b",
  "useful_god_complement": 0.72,
  "zwds": {
    "track_mods": {"friend": 1.0, "passion": 1.3, "partner": 0.9, "soul": 1.2},
    "rpv_modifier": 15,
    "flying_stars": { "hua_lu_a_to_b": true, "hua_ji_b_to_a": false, "..." : "..." },
    "spiciness_level": "HIGH_VOLTAGE",
    "defense_a": ["preemptive_strike"],
    "defense_b": [],
    "layered_analysis": { "..." : "..." }
  },
  "spiciness_level": "HIGH_VOLTAGE",
  "defense_mechanisms": { "viewer": ["preemptive_strike"], "target": [] },
  "layered_analysis": {
    "karmic_link":         ["one_way_hua_ji (業力單箭)"],
    "energy_dynamic":      ["A_Dom_natural (化権)"],
    "archetype_cluster_a": "殺破狼",
    "archetype_cluster_b": "機月同梁"
  }
}
```

> **Note:** `zwds`、`spiciness_level`、`defense_mechanisms`、
> `layered_analysis` 在兩人都是 Tier 1 時有完整內容；否則 `zwds`
> 為 `null`，`spiciness_level` 預設 `"STABLE"`，其他為空物件／空陣列。

---

## 輸入欄位規格

```
欄位                 型別    說明
─────────────────────────────────────────────────────────────
data_tier           int     1 | 2 | 3
birth_year          int?    出生年（ZWDS 計算必填，Tier 1）
birth_month         int?    出生月（1–12；BaZi 節氣調候 + ZWDS）
birth_day           int?    出生日（ZWDS 計算必填，Tier 1）
birth_time          str?    "HH:MM"（ZWDS 計算必填，Tier 1）
gender              str?    "M" | "F"（ZWDS 五行局計算；預設 "M"）
sun_sign            str     黃道星座名（小寫英文，如 "aries"）
moon_sign           str?    月亮星座（Tier 1/2 可用；移動慢）
venus_sign          str?
mars_sign           str?
mercury_sign        str?
jupiter_sign        str?
saturn_sign         str?
pluto_sign          str?
chiron_sign         str?    小行星，數月～數年換一次星座
juno_sign           str?    小行星，數月換一次星座 → Tier 3 可用
north_node_sign     str?    北交點星座（全 Tier 可用）
north_node_degree   float?  北交點黃道度數（全 Tier 可用）
south_node_sign     str?    南交點星座（全 Tier 可用）
south_node_degree   float?  南交點黃道度數（全 Tier 可用）
house7_sign         str?    第 7 宮宮首星座，僅 Tier 1（Descendant）
house7_degree       float?  第 7 宮宮首黃道度數，僅 Tier 1
ascendant_sign      str?    上升星座，~2 小時換一次 → 僅 Tier 1
house4_sign         str?    第 4 宮宮首，僅 Tier 1
house8_sign         str?    第 8 宮宮首，僅 Tier 1
lilith_sign         str?    暗月莉莉絲星座，Tier 1 only（swe.MEAN_APOG）
lilith_degree       float?  暗月莉莉絲黃道度數，Tier 1 only
vertex_sign         str?    宿命點星座，Tier 1 only（ascmc[3]）
vertex_degree       float?  宿命點黃道度數，Tier 1 only
emotional_capacity  int     情緒承載力分數 0–100，由日月冥土硬相位 + ZWDS規則計算
natal_aspects       list    本命相位列表（行星對），strength 0.2–1.0
bazi_element        str?    wood | fire | earth | metal | water
rpv_conflict        str?    cold_war | argue
rpv_power           str?    control | follow
rpv_energy          str?    home | out
attachment_style    str?    secure | anxious | avoidant
```

**Tier 降級策略：** `effective_tier = max(tier_a, tier_b)`（取最差的）

| Tier | 可用欄位 | ZWDS |
|---|---|---|
| 1（精確時間） | 全部欄位，含 ASC、House 4/7/8/12、Lilith、Vertex、Lunar Nodes | ✅ 完整計算 |
| 2（模糊時段） | 無 ASC / House 宮位 / Lilith / Vertex；有 Lunar Nodes | ❌ 跳過 |
| 3（僅日期）   | 太陽 + 慢速行星（Juno、Chiron、Lunar Nodes 仍可用） | ❌ 跳過 |

**ZWDS 資格判斷：**

```python
def _is_zwds_eligible(user: dict) -> bool:
    return user.get("data_tier") == 1 and bool(user.get("birth_time"))
```

---

## Step 1：雙模式相位計分

### `compute_sign_aspect(sign_a, sign_b, mode="harmony")` → float

所有行星相容性皆透過星座等分相位計算。

**距離計算：**
```
diff = abs(SIGN_INDEX[sign_a] - SIGN_INDEX[sign_b]) % 12
if diff > 6: diff = 12 - diff   # 以對分相為最大值
```

十二星座順序索引（0–11）：
aries=0, taurus=1, gemini=2, cancer=3, leo=4, virgo=5,
libra=6, scorpio=7, sagittarius=8, capricorn=9, aquarius=10, pisces=11

---

### mode="harmony"（和諧模式）

**適用對象：** Moon、Mercury、Jupiter、Saturn、Venus（核心/慾望以外）、
Juno、Sun、Asc；朋友軌、伴侶軌。

**邏輯：** 追求舒適、穩定、無壓力的互動。

| diff | 相位 | 分數 | 說明 |
|---|---|---|---|
| 0 | 合相 | 0.90 | 高度共鳴 |
| 4 | 三分相 | 0.85 | 天然順暢 |
| 2 | 六分相 | 0.75 | 輕鬆愉快 |
| 6 | 對分相 | 0.60 | 互補但需磨合 |
| 3 | 四分相 | 0.40 | 價值觀摩擦，相處累 |
| 1,5 | 半六分 / 不合相 | 0.10 | 無顯著模式 |

---

### mode="tension"（張力模式）

**適用對象：** Mars、Pluto、Chiron、House 8；激情軌、靈魂軌。

**邏輯：** 追求火花、征服慾、靈魂衝擊、宿命感。

| diff | 相位 | 分數 | 說明 |
|---|---|---|---|
| 0 | 合相 | 1.00 | 能量疊加，極度強烈 |
| 3 | 四分相 | 0.90 | 強烈摩擦、性張力爆表、控制慾 |
| 6 | 對分相 | 0.85 | 致命吸引、相愛相殺 |
| 4 | 三分相 | 0.60 | 太舒服了，缺乏激情 |
| 2 | 六分相 | 0.50 | 像朋友，沒什麼火花 |
| 1,5 | 半六分 / 不合相 | 0.10 | 無顯著模式 |

**Fallback：** 任一星座為 None 或無效 → 回傳 **0.65**（中性/未知）

---

## Step 2：慾望分數（VibeScore）

### `compute_lust_score(user_a, user_b)` → 0–100

物理/慾望吸引力分數。使用**動態權重分母**——只有在該欄位有值時才納入計算，
確保 Tier 2/3 用戶不因缺失欄位而被懲罰。

```
# ── 跨人主要相位（核心驅動，使用 _resolve_aspect 度數精確相位）─────────
cross_mv    = _resolve_aspect(mars_a, venus_b, "tension") × 0.30   # A追B
cross_vm    = _resolve_aspect(mars_b, venus_a, "tension") × 0.30   # B追A

# ── 同行星相位（美感/能量頻率同步）────────────────────────────────────
venus_sync  = _resolve_aspect(venus_a, venus_b, "harmony") × 0.15
mars_sync   = _resolve_aspect(mars_a,  mars_b,  "harmony") × 0.15

# ── Tier 1 精確宮位 / 上升（僅有精確度數時納入）────────────────────────
h8_mars_ab  = _resolve_aspect(h8_a, mars_b, "tension") × 0.10      # B的慾望撞A的第8宮
h8_mars_ba  = _resolve_aspect(h8_b, mars_a, "tension") × 0.10      # A的慾望撞B的第8宮
mars_asc_ab = _resolve_aspect(mars_a, asc_b, "tension") × 0.10     # A的衝勁被B看見
mars_asc_ba = _resolve_aspect(mars_b, asc_a, "tension") × 0.10     # B的衝勁被A看見
venus_asc_ab= _resolve_aspect(venus_a, asc_b, "harmony") × 0.10    # A的美感吸引B
venus_asc_ba= _resolve_aspect(venus_b, asc_a, "harmony") × 0.10    # B的美感吸引A

# ── 外行星業力張力（Tier 1+ 外行星有值時）─────────────────────────────
karmic      = compute_karmic_triggers(user_a, user_b) × 0.25
              （外行星 Uranus/Neptune/Pluto × 內行星 Moon/Venus/Mars，需 ≥ 0.85 才計入）

# ── RPV 權力動態（始終計算）────────────────────────────────────────────
power_fit   = compute_power_score(user_a, user_b) × 0.30

# ── BaZi 相剋乘數 ─────────────────────────────────────────────────────
if bazi 相剋（a_restricts_b 或 b_restricts_a）: score × 1.25

result = clamp(score × 100, 0, 100)
```

**行星選擇理由：**
- 跨人 Mars × Venus（tension）：「追求 vs 被吸引」的費洛蒙核心訊號
- 同行星 Venus × Venus（harmony）：美感品味同頻
- 同行星 Mars × Mars（harmony）：慾望節奏同步
- House 8 × Mars（tension）：禁忌與親密領域的碰撞（Tier 1 only）
- Mars / Venus × ASC（tension/harmony）：外在費洛蒙的化學反應（Tier 1 only）
- 外行星業力張力：宿命式的磁力，需精確相位才觸發

---

## Step 3：靈魂分數（ChemistryScore）

### `compute_soul_score(user_a, user_b)` → 0–100

情感深度與長期關係潛力。

```
moon       = aspect(moon_a,    moon_b,    "harmony") × 0.25
mercury    = aspect(merc_a,    merc_b,    "harmony") × 0.20
house4     = aspect(h4_a,      h4_b,      "harmony") × 0.15  (Tier 2/3 → 0.0)
saturn     = aspect(sat_a,     sat_b,     "harmony") × 0.20
attachment = ATTACHMENT_FIT[style_a][style_b]         × 0.20
juno       = (aspect(juno_a, moon_b, "harmony") + aspect(juno_b, moon_a, "harmony")) / 2 × 0.20
             (Cross-aspect：A 的婚神星 × B 的月亮，破除同期出生者的假性共振；缺月亮 → 跳過)

if bazi 相生（a_generates_b 或 b_generates_a）: score × 1.20

result = clamp(score × 100, 0, 100)
```

> **Note:** 權重合計 1.20（刻意超重，加深靈魂維度的鑑別力）。

### 依戀風格相容矩陣

|  | anxious | avoidant | secure |
|---|---|---|---|
| **anxious** | 0.50 | 0.70 | 0.80 |
| **avoidant** | 0.70 | 0.55 | 0.75 |
| **secure** | 0.80 | 0.75 | 0.90 |

---

## Step 4：權力動態

### `compute_power_v2(user_a, user_b, chiron_triggered, ...)` → dict

```
frame = 50
  + (rpv_power == "control" ? +20 : rpv_power == "follow" ? -20 : 0)
  + (rpv_conflict == "cold_war" ? +10 : rpv_conflict == "argue" ? -10 : 0)

frame_a = formula(user_a)
frame_b = formula(user_b)
if chiron_triggered: frame_b -= 15  # B 的框架穩定性被 A 動搖
frame_a += zwds_rpv_modifier        # ZWDS 化権 ± 15（Tier 1 only）

rpv = frame_a - frame_b
```

| rpv 值 | viewer_role | target_role |
|---|---|---|
| > +15 | Dom | Sub |
| < −15 | Sub | Dom |
| −15 ～ +15 | Equal | Equal |

### Chiron 觸發檢查

`_check_chiron_triggered(user_a, user_b)`：若 A 的 Mars 或 Pluto 對 B 的
Chiron 形成硬相位（四分相 diff=3 或對分相 diff=6）→ `frame_break=True`。

這代表 A 的慾望能量直接撞擊 B 的核心傷（Chiron）→ 靈魂震動觸發。

---

## Step 5：四軌分數

### `compute_tracks(user_a, user_b, power, useful_god_complement, zwds_mods)` → dict

```
friend  = mercury(harmony)×0.40 + jupiter_cross(harmony)×0.40 + bazi_harmony×0.20
          其中 jupiter_cross = (aspect(jup_a, sun_b) + aspect(jup_b, sun_a)) / 2
          （Cross-aspect：避免同年出生者因木星同座獲得虛假高分）

passion = mars(tension)×0.30    + venus(tension)×0.30
        + passion_extremity×0.10 + bazi_clash×0.30
  其中 passion_extremity = max(pluto_tension, house8_tension)

partner = moon(harmony)×0.35    + juno_cross(harmony)×0.35
          其中 juno_cross = (aspect(juno_a, moon_b) + aspect(juno_b, moon_a)) / 2
        + bazi_generation×0.30

soul    = chiron(tension)×0.40  + karmic_triggers×0.40
        + useful_god_complement×0.20
        (+ 0.10 bonus if frame_break=True)
  其中 karmic_triggers = compute_karmic_triggers(user_a, user_b)
      chiron = compute_sign_aspect(chiron_a, chiron_b, "tension")  ⚠️ 見已知限制 L-2

各軌 = clamp(value × 100, 0, 100)
```

**BaZi 分類對應：**

| 關係 | 元素範例 | 計入軌道 |
|---|---|---|
| 比和（same） | 木 vs 木 | friend track、soul track 的 bazi_harmony |
| 相生（generation） | 木生火 | partner track、soul_score ×1.2 |
| 相剋（restriction） | 金剋木 | passion track、lust_score ×1.2 |

---

## Step 6：ZWDS 合盤修正器（Tier 1 only）

### `compute_zwds_synastry(chart_a, birth_year_a, chart_b, birth_year_b)` → dict

兩人均為 Tier 1 時，透過三個機制計算紫微斗數對四軌的乘積修正器。

### 機制一：飛星四化（Flying Stars）

年干決定化祿 / 化権 / 化忌落在哪顆星。若 A 的化星落入 B 的關鍵宮位：

| 化星 | 影響 | 修正值 |
|---|---|---|
| 化祿（單向） | partner track ×1.2 | |
| 化祿（雙向） | partner track ×1.4（SSR 級別） | |
| 化忌（單向） | soul ×1.3，partner ×0.9 | |
| 化忌（雙向） | soul ×1.5（業力虐戀），partner ×0.9 | |
| 化権（A→B） | RPV frame_a +15（A 天生 Dom） | |
| 化権（B→A） | RPV frame_a −15（B 天生 Dom） | |

### 機制二：主星人設（Star Archetypes）

命宮主星決定這個人的「關係人設」，影響四軌乘數及 RPV 框架：

| 星群 | 主星 | 激情 | 伴侶 | 朋友 | 靈魂 | RPV |
|---|---|---|---|---|---|---|
| 殺破狼 | 七殺 / 破軍 / 貪狼 | ×1.3 | ×0.8 | ×1.0 | ×1.0 | +15 |
| 紫府武相 | 紫微 / 天府 / 武曲 / 天相 | ×1.0 | ×1.3 | ×1.0 | ×0.8 | +10 |
| 機月同梁 | 天機 / 太陰 / 天同 / 天梁 | ×0.8 | ×1.0 | ×1.3 | ×1.3 | −10 |
| 巨日 | 太陽 / 巨門 | ×1.0 | ×1.2 | ×1.1 | ×1.0 | +5 |
| 廉貞 | 廉貞 | ×1.2 | ×1.0 | ×1.0 | ×1.1 | +5 |

命宮空宮（借對宮）：全軌 ×1.0，RPV −10（變色龍體質）

### 機制三：煞星防禦（Stress Defense）

夫妻宮有煞星 → 觸發壓力防禦機制，影響四軌：

| 觸發 | 星曜 | 修正 |
|---|---|---|
| `preemptive_strike` | 擎羊 / 火星 | passion ×1.2，partner ×0.8 |
| `silent_rumination` | 陀羅 / 鈴星 | soul ×1.3，friend ×0.85 |
| `sudden_withdrawal` | 天空 / 地劫 | partner ×0.6，soul ×1.2 |

兩人合集取聯集（`set(defense_a) | set(defense_b)`），每個觸發只計一次。

### 四軌最終修正公式

```python
track_final = track_raw × (0.70 × zwds_mod + 0.30)
```

其中 `zwds_mod` 是上述三機制合計後的乘積值（預設 1.0）。
ZWDS 貢獻上限 70%，確保西洋 + 八字始終保有 30% 基礎權重。

### Spiciness Level 分類

| 等級 | 條件 |
|---|---|
| `SOULMATE` | soul_mod ≥ 1.4 且 partner_mod ≥ 1.3 |
| `HIGH_VOLTAGE` | （passion ≥ 1.3 且 soul ≥ 1.2）或有 sudden_withdrawal |
| `MEDIUM` | passion ≥ 1.2 或 soul ≥ 1.2 或 partner ≥ 1.2 |
| `STABLE` | 其他 |

---

## Step 7：象限分類

### `classify_quadrant(lust_score, soul_score, threshold=60.0)`

| lust | soul | 象限 |
|---|---|---|
| ≥ 60 | ≥ 60 | **soulmate**（靈魂愛人） |
| ≥ 60 | < 60 | **lover**（激情情人） |
| < 60 | ≥ 60 | **partner**（穩定伴侶） |
| < 60 | < 60 | **colleague**（同行夥伴） |

---

## Step 8：雙人合盤暗黑修正器（Shadow & Synastry Modifiers）

`compute_shadow_and_wound(chart_a, chart_b)` → `{soul_mod, lust_mod, partner_mod, high_voltage, shadow_tags}`

所有觸發器均以**黃道度數精確相位**計算（非星座等分）。修正值為疊加型（additive modifier），
不直接修改 lust_score / soul_score，而是透過 `compute_match_v2` 最後加乘。
`partner_mod` 會加至 `tracks["partner"]`（v1.9 新增）。

### 合盤容許度

| 觸發類型 | 容許度 | 相位 |
|---|---|---|
| 凱龍傷口觸發 | 5° | 合相 + 對分相 |
| 宿命點觸發 | 3° | 合相 only |
| 莉莉絲觸發 | 3° | 合相 only |

### 凱龍傷口觸發（_CHIRON_ORB = 5.0°）

A 的個人行星（日/月/金/火）合相或對分相 B 的凱龍星 → 靈魂傷口激活：

| 觸發行星 | soul_mod | lust_mod | high_voltage | Tag |
|---|---|---|---|---|
| 太陽 | +15 | — | ✅ | `A_Sun_Triggers_B_Chiron` |
| 月亮 | +15 | — | ✅ | `A_Moon_Triggers_B_Chiron` |
| 金星 | +15 | — | ✅ | `A_Venus_Triggers_B_Chiron` |
| 火星 | +15 | +10 | ✅ | `A_Mars_Triggers_B_Chiron` |

（B 對 A 的鏡像觸發同理，Tag 前綴為 `B_`）

### 宿命點觸發（_VERTEX_LILITH_ORB = 3.0°）

A 的個人行星（日/月/金）精準合相 B 的宿命點 → 命運之門開啟：

| 觸發行星 | soul_mod | lust_mod | high_voltage | Tag |
|---|---|---|---|---|
| 太陽 | +25 | — | ❌ | `A_Sun_Conjunct_Vertex` |
| 月亮 | +25 | — | ❌ | `A_Moon_Conjunct_Vertex` |
| 金星 | +25 | — | ❌ | `A_Venus_Conjunct_Vertex` |

（注意：宿命感是業力而非危險，不觸發 high_voltage）

### 莉莉絲觸發（_VERTEX_LILITH_ORB = 3.0°）

A 的慾望行星（金/火）精準合相 B 的暗月莉莉絲 → 禁忌吸引力：

| 觸發行星 | soul_mod | lust_mod | high_voltage | Tag |
|---|---|---|---|---|
| 金星 | — | +25 | ✅ | `A_Venus_Conjunct_Lilith` |
| 火星 | — | +25 | ✅ | `A_Mars_Conjunct_Lilith` |

### 12 宮陰影疊加

A 的太陽或火星落入 B 的第 12 宮 → soul_mod +20，high_voltage，Tag `A_Illuminates_B_Shadow`
雙向疊加時額外 +40，Tag `Mutual_Shadow_Integration`

### 南北交點觸發（_NODE_ORB = 3.0°，Algorithm v1.8）

A 的個人行星（日/月/金/火）合相 B 的南交點 / 北交點：

| 觸發 | soul_mod | high_voltage | Tag |
|---|---|---|---|
| 合相南交點 | +20 | ✅ | `A_{P}_Conjunct_SouthNode` |
| 合相北交點 | +20 | ❌ | `A_{P}_Conjunct_NorthNode` |

### 第七宮 Descendant 疊圖（_DSC_ORB = 5.0°，Algorithm v1.9，Tier 1 only）

下降點 DSC = ASC + 180°。A 的個人行星（日/月/金）精準合相 B 的 DSC：

| 觸發行星 | partner_mod | soul_mod | high_voltage | Tag |
|---|---|---|---|---|
| 太陽 | +20 | +10 | ❌ | `A_Sun_Conjunct_Descendant` |
| 月亮 | +20 | +10 | ❌ | `A_Moon_Conjunct_Descendant` |
| 金星 | +20 | +10 | ❌ | `A_Venus_Conjunct_Descendant` |

（DSC 是婚姻宮的宮首，代表靈魂渴求的「正緣形象」；partner_mod 流入 partner 軌道）

### Shadow Tags 完整清單（中文對照）

所有 Shadow Tag 在 `prompt_manager.py` 的 `_PSYCH_TAG_ZH` 中有對應中文翻譯，
供 LLM 生成「宿命感解析」文案時使用。

---

## 個人業力軸線（Karmic Axis，Algorithm v1.9）

`extract_karmic_axis(chart)` → `List[str]`，結果合併進 `karmic_tags`。

### Sign Axis（星座軸線，全 Tier）

北交點星座決定靈魂的「前世借力 vs 今生進化」方向：

| 北交點星座 | Axis Tag | 意涵 |
|---|---|---|
| Aries / Libra | `Axis_Sign_Aries_Libra` | 自我主張 ↔ 合作共贏 |
| Taurus / Scorpio | `Axis_Sign_Taurus_Scorpio` | 物質安穩 ↔ 深層轉化 |
| Gemini / Sagittarius | `Axis_Sign_Gemini_Sag` | 落地溝通 ↔ 高遠理想 |
| Cancer / Capricorn | `Axis_Sign_Cancer_Cap` | 情感柔軟 ↔ 事業使命 |
| Leo / Aquarius | `Axis_Sign_Leo_Aquarius` | 個人光芒 ↔ 群體服務 |
| Virgo / Pisces | `Axis_Sign_Virgo_Pisces` | 現實秩序 ↔ 靈性混沌 |

同時產生 `North_Node_Sign_{星座}` 精確描述標籤（12 種）。

### House Axis（宮位軸線，Tier 1 only）

使用 **Whole Sign House** 計算（ASC 星座 = 第 1 宮）：
```
house_num = (nn_sign_index - asc_sign_index) % 12 + 1
```

產生 `Axis_House_{n}_{n+6}` 與 `North_Node_House_{n}` 標籤（共 6 對軸線）。

---

## RPV 評分邏輯

三個維度由入職問卷（3 題）收集：

| 維度 | 互補分數 | 相同分數 | 權重 |
|---|---|---|---|
| rpv_conflict | 0.85 | 0.55 | 35% |
| rpv_power    | 0.90 | 0.50 | 40% |
| rpv_energy   | 0.75 | 0.65 | 25% |

`compute_power_score = conflict×0.35 + power×0.40 + energy×0.25`

**Sandbox 自動推算（非問卷）：**

在 Algorithm Validation Sandbox（Tab A）中，RPV 和依戀風格由星盤自動推算：

| 參數 | 推算依據 |
|---|---|
| attachment_style | 月亮元素：水/火象→焦慮、土象→迴避、風象→安全 |
| rpv_conflict | 太陽或火星在火象→開吵，否則冷戰 |
| rpv_power | 太陽在固定星座或日主木/火→主導，否則跟隨 |
| rpv_energy | 上升（或太陽）在火/風象→外出，否則宅家 |

---

## API 端點

**POST `/compute-match`** — 雙人合盤配對計算

```json
{
  "user_a": {
    "sun_sign": "aries", "mars_sign": "scorpio",
    "birth_year": 1990, "birth_month": 6, "birth_day": 15,
    "birth_time": "11:30", "data_tier": 1
  },
  "user_b": {
    "sun_sign": "leo",   "mars_sign": "cancer",
    "birth_year": 1992, "birth_month": 9, "birth_day": 22,
    "birth_time": "08:00", "data_tier": 1
  }
}
```

Response: 見「系統概覽」的輸出結構。

**POST `/calculate-chart`** — 單人西洋占星 + 八字計算（由
`/api/onboarding/birth-data` 自動呼叫）：

```json
{
  "birth_date": "1995-06-15",
  "birth_time_exact": "14:30",
  "birth_time": "precise",
  "lat": 25.033,
  "lng": 121.565,
  "data_tier": 1
}
```

**POST `/compute-zwds-chart`** — 單人紫微斗數命盤計算（Tier 1 only）：

```json
{
  "birth_year": 1990,
  "birth_month": 6,
  "birth_day": 15,
  "birth_time": "11:30",
  "gender": "M"
}
```

回傳：`{ "chart": { "palaces": {...}, "four_transforms": {...},
"five_element": "火六局", "body_palace_name": "財帛宮",
"life_palace_pos": 3 } }`

---

## 注意事項與已知限制

### 已部分解決

- **`_resolve_aspect` 精確度數優先**：`compute_lust_score` 的所有主要相位、
  `shadow_engine.py` 的所有觸發器均使用精確黃道度數（orb-based, 線性衰退）。
  `chart.py` 已回傳所有行星的精確度數；Tier 1 用戶享有完整度數精確計算。
- **House 4 / House 8** 在 Tier 2/3 時設為 0.0（不使用），非 0.65 中性值，
  使有精確時間的用戶分數差異更明顯。
- **Chiron 和 Juno** 移動慢（數月至數年/星座），在 Tier 3 仍有高可信度。
- **分數設計上可超出 0–1 範圍**（例如 soul_score 權重合計 1.20），
  最終統一由 `_clamp(value × 100, 0, 100)` 限縮。
- **`natal_aspects`** 使用 orb-based 精確相位，線性強度衰退公式：
  `strength = 0.2 + 0.8 × (1 - orb/max_orb)`，合相 orb 8°。
- **Lilith / Vertex** 僅 Tier 1 有值，shadow_engine 做 None 防護（觸發器直接跳過）。
- **Jupiter / Juno** 使用跨人相位修正，消除同齡人假性高分。
- **ZWDS** 修正器採乘積疊加，不直接修改 lust/soul 分數，只調整四軌與 RPV frame。
- **v1.9（2026-02-23）：** Descendant 疊圖（`partner_mod`）、南北交點業力觸發（v1.8）、
  業力軸線 `extract_karmic_axis`（Sign Axis 全 Tier + House Axis Tier 1 Whole Sign）。

---

### 已知限制與待優化清單（Code Review 2026-02-24）

優先級 **P1（影響評分準確度）**：

| # | 問題 | 影響 | 位置 |
|---|---|---|---|
| **L-1** | Shadow modifier 無累計上限：soul_adj / lust_adj 可累加超過 +100，使影子引擎變成分數覆蓋器而非鑑別器 | C | `matching.py:1167` |
| **L-2** | Chiron 在 soul track 使用同星座比較（非跨人度數相位）：同期出生者（Chiron 同座數年）會獲得虛假最高分 | C | `matching.py:906` |
| **L-3** | `compute_soul_score` 的 Moon / Mercury / Saturn 仍使用 `compute_sign_aspect`（星座等分），非 `_resolve_aspect`（度數精確）：兩人 Moon 相差 27° 但同座時會被算成合相 | C | `matching.py:703-714` |

優先級 **P2（缺失重要因素）**：

| # | 問題 | 影響 | 建議修法 |
|---|---|---|---|
| **L-4** | **缺 Sun-Moon 跨人相位**：A 的太陽 × B 的月亮（雙向）是占星傳統中最重要的合盤指標，目前完全缺席 | I | 加入 `compute_soul_score`，建議 weight `"soul_sun_moon": 0.20` |
| **L-5** | **缺 Saturn 跨人相位**：A 的土星 × B 的月亮/金星（雙向）是長期承諾與業力束縛的核心指標 | I | 加入 `compute_tracks` partner track |
| **L-6** | **缺 Moon-Pluto 合盤觸發**：A 的冥王星合相/四分相/對分相 B 的月亮 → 情感操控/深度蛻變/obsessive attachment，與本平台 D/s 主題高度相關 | I | 加入 `shadow_engine.py`，soul_mod +15, lust_mod +10, high_voltage |
| **L-7** | **缺 Venus-Saturn 合盤觸發**：一方的土星束縛另一方的金星 → 義務感、延遲滿足、業力感情 | I | 加入 `shadow_engine.py` |
| **L-8** | **外行星業力觸發閾值 0.85 過高**：0.84 的近精確四分相被整個丟棄，造成非線性分數懸崖 | I | 降至 0.70 或改為漸進式貢獻 |

優先級 **P3（校準 / 小問題）**：

| # | 問題 | 影響 | 備注 |
|---|---|---|---|
| **L-9** | ZWDS 化科（hua_ke）已計算但未使用於合盤 | M | 可貢獻 friend track ×1.1 |
| **L-10** | `compute_power_v2` 的 `zwds_rpv_modifier` 只加到 `frame_a`，若未來需獨立顯示雙方 frame 值，邏輯會有誤 | M | 建議改為 ±frame_a/frame_b 分開儲存 |
| **L-11** | `compute_soul_score` 文件中 weight 合計 1.20，應補充說明動態正規化機制，避免開發者誤以為需要加總 = 1.00 | M | 文件修正 |
| **L-12** | soul track 的 Chiron 同座比較 與 shadow_engine 的 Chiron 跨人度數觸發走兩條路徑但都加進 `tracks["soul"]`，造成 Chiron 因子被雙重計算 | M | 文件說明或從 track 中移除 |

---

### 其他固定注意事項

- ZWDS 計算依賴 `lunardate` 套件，支援 1900–2100 年；範圍外回傳 `None`（非阻塞）。
- `soul_adj` / `lust_adj` 同時套用至 Y 軸分數與對應 track，設計意圖是保持方向一致；
  但因為 `compute_tracks` 和 `compute_shadow_and_wound` 計算的是不同行星組合，
  兩者可能在高修正器下產生分歧。此為已知設計取捨，非 bug。
