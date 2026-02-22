# DESTINY 演算法權重調整指南 (WEIGHTS Tuning Guide)

> **版本：** v1.6（2026-02-22）
> **對應檔案：** `astro-service/matching.py` → 頂部 `WEIGHTS` dict

---

## 概覽

所有評分權重集中在 `matching.py` 頂部的 `WEIGHTS` dict。修改此 dict 即可調整演算法行為，**無需深入函數內部**。

```python
# astro-service/matching.py（大約第 40 行）
WEIGHTS = {
    "lust_cross_mars_venus": 0.30,   # 改這裡就能調整吸引力權重
    ...
}
```

---

## 架構圖

```
compute_match_v2()
├── compute_lust_score()      ← WEIGHTS["lust_*"]
├── compute_soul_score()      ← WEIGHTS["soul_*"]
├── compute_tracks()          ← WEIGHTS["track_*"]
├── compute_power_v2()
│   └── compute_power_score() ← WEIGHTS["power_*"]
└── compute_karmic_triggers()
    └── compute_exact_aspect()  ← ASPECT_RULES (module constant)

compute_match_score() (v1)
├── compute_kernel_score()    ← WEIGHTS["kernel_*"]
├── compute_power_score()     ← WEIGHTS["power_*"]
└── compute_glitch_score()    ← WEIGHTS["glitch_*"]
```

---

## 各區塊說明

### 1. Lust Score（X 軸：生理吸引力）

```python
"lust_cross_mars_venus":   0.30,   # A 的火星 × B 的金星（主攻訊號）
"lust_cross_venus_mars":   0.30,   # B 的火星 × A 的金星（反向）
# ⚠️ 以上兩者必須保持相等，否則 swapAB 後分數不對稱
"lust_same_venus":         0.15,   # A 金星 × B 金星（美感同步）
"lust_same_mars":          0.15,   # A 火星 × B 火星（節奏同步）
"lust_house8_ab":          0.10,   # A 第 8 宮 × B 火星（精確度數才生效）
"lust_house8_ba":          0.10,   # B 第 8 宮 × A 火星
"lust_karmic":             0.25,   # 外行星 vs 內行星業力觸發
"lust_power":              0.30,   # RPV 權力動態
"lust_bazi_restrict_mult": 1.25,   # 八字相剋乘數（×）
```

**調整建議：**
- 想加強「跨人吸引力」訊號 → 調高 `lust_cross_mars_venus` / `lust_cross_venus_mars`（記得兩者保持相等）
- 想降低業力/RPV 影響 → 調低 `lust_karmic` / `lust_power`
- 想讓八字相剋效果更強烈 → 調高 `lust_bazi_restrict_mult`（e.g. 1.35）

---

### 2. Soul Score（Y 軸：靈魂深度 / 長期承諾）

```python
"soul_moon":              0.25,   # 月亮（情感核心）— 必有
"soul_mercury":           0.20,   # 水星（溝通方式）— 必有
"soul_saturn":            0.20,   # 土星（邊界/承諾）— 必有
"soul_house4":            0.15,   # 第 4 宮（家的概念）— Tier 1 才有
"soul_juno":              0.20,   # 婚神星（婚姻承諾）— 有星曆才有
"soul_attachment":        0.20,   # 依戀風格（問卷填寫後才有）
"soul_generation_mult":   1.20,   # 八字相生乘數（×）
```

**調整建議：**
- 想讓月亮相位更重要 → 調高 `soul_moon`，對應降低其他值（保持 Tier 3 三項加總 ≈ 0.65）
- 想讓婚神星更有影響力 → 調高 `soul_juno`
- 相生乘數建議範圍：1.10 ~ 1.30

---

### 3. Kernel Score（v1 核心相容性）

| 鍵名 | 預設 | 說明 |
|------|------|------|
| `kernel_t1_sun` | 0.20 | Tier 1：太陽 |
| `kernel_t1_moon` | 0.25 | Tier 1：月亮 |
| `kernel_t1_venus` | 0.25 | Tier 1：金星 |
| `kernel_t1_asc` | 0.15 | Tier 1：上升 |
| `kernel_t1_bazi` | 0.15 | Tier 1：八字 |
| `kernel_t2_*` | 0.25/0.20/0.25/0.30 | Tier 2（無上升） |
| `kernel_t3_*` | 0.30/0.30/0.40 | Tier 3（僅太陽+金星+八字） |

**⚠️ 規則：** 同 Tier 的所有鍵值加總必須 = 1.00。

---

### 4. Four Tracks（四軌：friend / passion / partner / soul）

```python
# 朋友軌
"track_friend_mercury": 0.40,  "track_friend_jupiter": 0.40,  "track_friend_bazi": 0.20,

# 激情軌
"track_passion_mars": 0.30,    "track_passion_venus": 0.30,
"track_passion_extreme": 0.10, "track_passion_bazi": 0.30,

# 伴侶軌（有婚神星）
"track_partner_moon": 0.35,    "track_partner_juno": 0.35,    "track_partner_bazi": 0.30,
# 伴侶軌（無婚神星）
"track_partner_nojuno_moon": 0.55,  "track_partner_nojuno_bazi": 0.45,

# 靈魂軌（有凱龍）
"track_soul_chiron": 0.40,     "track_soul_karmic": 0.40,     "track_soul_useful_god": 0.20,
# 靈魂軌（無凱龍）
"track_soul_nochiron_karmic": 0.60,  "track_soul_nochiron_useful_god": 0.40,
```

**⚠️ 規則：**
- 每軌的所有鍵值加總必須 = 1.00（有/無婚神星兩個 branch 各自加總）
- `track_passion_extreme` 是 `max(karmic, house8)` 的加成項，非獨立相位

---

### 5. Power Score（RPV 動力）

```python
"power_conflict": 0.35,   # 衝突風格（互補 vs 相同）
"power_power":    0.40,   # 主從關係（控制 vs 跟隨）
"power_energy":   0.25,   # 能量方式（外出 vs 宅）
```

**⚠️ 規則：** 三者加總 = 1.00。

---

### 6. Glitch Score（摩擦容忍度）

```python
"glitch_mars":      0.25,   # 火星 vs 火星
"glitch_saturn":    0.25,   # 土星 vs 土星
"glitch_mars_sat_ab": 0.25, # A 火星 vs B 土星
"glitch_mars_sat_ba": 0.25, # B 火星 vs A 土星
```

**⚠️ 規則：** 四者加總 = 1.00。

---

### 7. Match Score v1（頂層加權）

```python
"match_kernel": 0.50,   # 核心相容性佔比
"match_power":  0.30,   # 動力佔比
"match_glitch": 0.20,   # 摩擦容忍佔比
```

**⚠️ 規則：** 三者加總 = 1.00。

---

## 快速修改流程

```bash
# 1. 開啟 matching.py
code astro-service/matching.py

# 2. 跳到 WEIGHTS dict（約第 40 行）
# 3. 修改想調整的值

# 4. 驗證測試全過
cd astro-service
pytest test_matching.py -v

# 5. Commit
cd ..
git add astro-service/matching.py
git commit -m "tune: adjust WEIGHTS for [描述調整原因]"
```

---

## 相位評分系統（ASPECT_RULES）

相位的「精準度」由 `ASPECT_RULES` 控制（module-level constant，非 WEIGHTS）：

| 相位 | 中心度數 | 容許度 (Orb) | Harmony 最高分 | Tension 最高分 |
|------|----------|-------------|--------------|--------------|
| 合相 | 0° | 8° | 1.0 | 1.0 |
| 六分相 | 60° | 6° | 0.8 | 0.3 |
| 四分相 | 90° | 8° | 0.2 | 0.9 |
| 三分相 | 120° | 8° | 1.0 | 0.2 |
| 對分相 | 180° | 8° | 0.4 | 1.0 |

**線性衰減公式：**
```
strength_ratio = 1.0 - (diff / orb)
final_score = 0.2 + (max_score - 0.2) × strength_ratio
```

0° 合相得 1.0；7° 合相只得 ~0.30。

要修改 Orb 大小或最高分，直接編輯 `matching.py` 的 `ASPECT_RULES` 列表（位於 WEIGHTS dict 下方）。

---

## 常見調整情境

### 情境 A：想讓「激情型」配對更少見

降低 `lust_cross_mars_venus` / `lust_cross_venus_mars`，或降低 `lust_bazi_restrict_mult`。

### 情境 B：想讓「靈魂型」配對更多

調高 `track_soul_chiron` / `track_soul_karmic`，或提高 `soul_generation_mult`。

### 情境 C：想讓 RPV 問卷的影響力下降

同時降低 `lust_power`（在 Lust Score 裡）和 `power_power`（在 Power Score 裡）。

### 情境 D：想讓精確出生時間（Tier 1）的優勢更大

調高 `kernel_t1_asc`（上升點）、`soul_house4`（第 4 宮），這兩個欄位只有 Tier 1 才有。

---

*最後更新：2026-02-22 | 演算法版本：v1.6*
