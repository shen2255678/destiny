# DESTINY 配對演算法技術規格

本文件提供 DESTINY 配對引擎完整的技術規格，適合 AI 助理、開發者在
理解、除錯或擴充演算法時參考，不需要閱讀原始碼。

---

## 系統概覽

配對引擎位於 `astro-service/matching.py`，主要入口函數為
`compute_match_v2(user_a, user_b)`，整合四個維度：

1. **西洋占星**（Western Astrology）— 行星星座相位分數
2. **八字日主五行**（BaZi Five Elements）— 相生相剋關係
3. **RPV**（Relational Power Variables）— 衝突風格 × 權力偏好 × 能量模式
4. **依戀心理學**（Attachment Theory）— 依戀風格相容矩陣

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
  "labels": ["✦ 激情型連結"]
}
```

---

## 輸入欄位規格

```
欄位                 型別    說明
─────────────────────────────────────────────────
data_tier           int     1 | 2 | 3
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
ascendant_sign      str?    上升星座，~2 小時換一次 → 僅 Tier 1
house4_sign         str?    第 4 宮宮首，僅 Tier 1
house8_sign         str?    第 8 宮宮首，僅 Tier 1
bazi_element        str?    wood | fire | earth | metal | water
rpv_conflict        str?    cold_war | argue
rpv_power           str?    control | follow
rpv_energy          str?    home | out
attachment_style    str?    secure | anxious | avoidant
```

**Tier 降級策略：** `effective_tier = max(tier_a, tier_b)`（取最差的）

| Tier | 可用欄位 |
|---|---|
| 1（精確時間） | 全部欄位，含 ASC、House 4、House 8 |
| 2（模糊時段） | 無 ASC / House 宮位 |
| 3（僅日期）   | 太陽 + 慢速行星（Juno、Chiron 仍可用） |

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

物理/慾望吸引力分數。

```
venus       = aspect(venus_a,  venus_b,  "harmony") × 0.20
mars        = aspect(mars_a,   mars_b,   "tension")  × 0.25
pluto       = aspect(pluto_a,  pluto_b,  "tension")  × 0.25
house8      = aspect(h8_a,     h8_b,     "tension")  × 0.15  (Tier 2/3 → 0.0)
power_fit   = compute_power_score(user_a, user_b)    × 0.30

if bazi 相剋（a_restricts_b 或 b_restricts_a）: score × 1.20

result = clamp(score × 100, 0, 100)
```

**行星選擇理由：**
- Venus harmony：美感 / 品味吸引（舒適感）
- Mars tension：主動慾望 / 主導動能（摩擦感）
- Pluto tension：執念 / 磁性吸引（深層慾望）
- House 8 tension：性吸引 / 禁忌領域（僅 Tier 1）

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
juno       = aspect(juno_a,    juno_b,    "harmony") × 0.20  (缺失 → 0.65)

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

### `compute_power_v2(user_a, user_b, chiron_triggered)` → dict

```
frame = 50
  + (rpv_power == "control" ? +20 : rpv_power == "follow" ? -20 : 0)
  + (rpv_conflict == "cold_war" ? +10 : rpv_conflict == "argue" ? -10 : 0)

frame_a = formula(user_a)
frame_b = formula(user_b)
if chiron_triggered: frame_b -= 15  # B 的框架穩定性被 A 動搖

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

### `compute_tracks(user_a, user_b, power)` → dict

```
friend  = mercury(harmony)×0.40 + jupiter(harmony)×0.40 + bazi_harmony×0.20

passion = mars(tension)×0.30    + venus(tension)×0.30
        + passion_extremity×0.10 + bazi_clash×0.30
  其中 passion_extremity = max(pluto_tension, house8_tension)

partner = moon(harmony)×0.35    + juno(harmony)×0.35
        + bazi_generation×0.30

soul    = chiron(tension)×0.40  + pluto(tension)×0.40
        + bazi_harmony×0.20
        (+ 0.10 bonus if frame_break=True)

各軌 = clamp(value × 100, 0, 100)
```

**BaZi 分類對應：**

| 關係 | 元素範例 | 計入軌道 |
|---|---|---|
| 比和（same） | 木 vs 木 | friend track、soul track 的 bazi_harmony |
| 相生（generation） | 木生火 | partner track、soul_score ×1.2 |
| 相剋（restriction） | 金剋木 | passion track、lust_score ×1.2 |

**Venus 在 passion track 中使用 tension mode：** 在激情情境下，金星的
「慾望感」比「舒適感」更重要。

---

## Step 6：象限分類

### `classify_quadrant(lust_score, soul_score, threshold=60.0)`

| lust | soul | 象限 |
|---|---|---|
| ≥ 60 | ≥ 60 | **soulmate**（靈魂愛人） |
| ≥ 60 | < 60 | **lover**（激情情人） |
| < 60 | ≥ 60 | **partner**（穩定伴侶） |
| < 60 | < 60 | **colleague**（同行夥伴） |

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

**POST `/compute-match`**

```json
{
  "user_a": { "sun_sign": "aries", "mars_sign": "scorpio", ... },
  "user_b": { "sun_sign": "leo",   "mars_sign": "cancer",  ... }
}
```

Response: 見「系統概覽」的輸出結構。

**POST `/calculate-chart`** — 計算單人星盤（由 `/api/onboarding/birth-data`
自動呼叫）：

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

---

## 注意事項與已知限制

- 目前使用**星座等分相位**（sign-level），非度數精確相位（degree-level）。
  升級路徑：`chart.py` 回傳行星精確黃道度數後可改用 orb-based aspect。
- House 4 / House 8 在 Tier 2/3 時設為 0.0（不使用），非 0.65 中性值，
  這使得有精確時間的用戶分數區別更明顯。
- Chiron 和 Juno 移動慢（數月至數年/星座），在 Tier 3 仍有高可信度。
- 分數有意設計為可能超出 0–1 範圍（例如 soul_score 權重合計 1.20），
  最終統一由 `_clamp(value × 100, 0, 100)` 限縮。
