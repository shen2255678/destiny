# Phase G：Expanded Matching Algorithm v2 設計文件

**日期：** 2026-02-20
**狀態：** 設計完成，待實作
**參考：** `docs/DESTINY Algorithm Implementation Spec (Full).md`

---

## 0) 背景

當前 `matching.py` 使用單一 `Match_Score` 公式：

```
Match_Score = Kernel(0.5) + Power(0.3) + Glitch(0.2)
```

此架構只輸出一個數字，無法表達「這段關係到底是激情、是靈魂共鳴、是穩定伴侶、還是朋友」。

**Phase G 目標：** 將配對引擎升級為雙軸（Lust × Soul）+ 四軌評分系統，輸出豐富的關係類型標籤，讓用戶用潛意識選擇配對對象。

---

## 1) 新增星體（chart.py）

### 1.1 新增行星（pyswisseph 內建，無需額外檔案）

| 星體 | `swe` ID | 層次 | 用途 |
|------|----------|------|------|
| 水星 Mercury | `swe.MERCURY` | 靈魂軸 / 朋友軌 | 溝通相容性 |
| 木星 Jupiter | `swe.JUPITER` | 朋友軌 | 玩樂、擴張能量 |
| 冥王星 Pluto | `swe.PLUTO` | 慾望軸 / 靈魂軌 | 執念、致命吸引 |

### 1.2 新增小行星（需 `./ephe/` 星曆檔）

| 星體 | `swe` ID | 層次 | 用途 |
|------|----------|------|------|
| 凱龍星 Chiron | `swe.CHIRON` | 靈魂軌 / Power | 童年創傷點、療癒觸發 |
| 婚神星 Juno | `swe.AST_OFFSET + 3` | 靈魂軸 / 伴侶軌 | 承諾、長期配對信號 |

> **ephe 檔案：** `seas_18.se1`、`sepl_18.se1`、`semo_18.se1` 已下載至 `astro-service/ephe/`
> 需在 `chart.py` / `bazi.py` 入口加 `swe.set_ephe_path('./ephe')`

### 1.3 宮位計算（House 4 / House 8 宮頭星座）

**用途：**
- House 4（家宅宮）→ 內在安全感基地，對應 Soul Score
- House 8（死亡宮）→ 禁忌、性欲、極限體驗，對應 Lust Score

**計算方式：** 使用現有 `swe.houses(jd, lat, lng, b"P")` Placidus 系統，取第 4、第 8 宮頭黃經 → 換算星座。

**降級策略：**

| 資料狀況 | 處理方式 |
|---------|---------|
| `data_tier == 1`（精確時間） | 正常計算 house4/8 星座 |
| `data_tier == 2/3`（無精確時間） | `house4_sign = null`，`house8_sign = null` |
| 配對時 house signal 為 null | `house8_signal = pluto_signal`（冥王星替代） |

### 1.4 未來擴充（本次不實作）

- **愛神星 Eros**（Asteroid 433）— 需下載 `se00433s.se1`（29GB 資料庫，暫缺）
- **莉莉絲 Black Moon Lilith** — 代表壓抑的原始本能與禁忌吸引力，比 Eros 更野蠻

---

## 2) 新輸出 Schema

```json
{
  "lust_score": 72,
  "soul_score": 85,
  "power": {
    "rpv": 18,
    "frame_break": false,
    "viewer_role": "Dom",
    "target_role": "Sub"
  },
  "tracks": {
    "friend": 45,
    "passion": 78,
    "partner": 82,
    "soul": 90
  },
  "primary_track": "soul",
  "quadrant": "partner",
  "labels": ["#深度連結", "#療癒系"],
  "reasons": [
    {"code": "chiron_synastry", "weight": 0.4, "note": "凱龍共鳴"}
  ]
}
```

---

## 3) Lust Score（X 軸，生理/慾望吸引）

**公式（Eros 缺席版本）：**

```python
def calculate_lust_score(f):
    score = 0
    score += f.venus_synastry    * 0.20   # 原 0.15，吸收 Eros 部分權重
    score += f.mars_synastry     * 0.25   # 原 0.20
    score += f.house8_connection * 0.15   # 禁忌感（無出生時間時 = 0）
    score += f.pluto_intensity   * 0.25   # 原 0.20，執念主力
    score += f.power_fit         * 0.30   # S/M 動力契合度

    if f.bazi_clash:
        score *= 1.2  # 相剋高張力加成

    return clamp(score * 100, 0, 100)
```

> **House 8 降級：** `house8_connection = 0` 時，`passion_extremity = pluto_signal`（冥王星補位）

**未來升級：** 加入 Eros(0.15)，Venus/Mars/Pluto 同步縮減回原權重。

---

## 4) Soul Score（Y 軸，靈魂深度/長期承諾）

```python
def calculate_soul_score(f):
    score = 0
    score += f.moon_synastry      * 0.25  # 情感安全感
    score += f.mercury_synastry   * 0.20  # 溝通頻率
    score += f.house4_connection  * 0.15  # 內在安全基地（無時間時 = 0）
    score += f.saturn_stability   * 0.20  # 長期結構穩定性
    score += f.attachment_fit     * 0.20  # 依附風格契合（見第 6 節）
    score += f.juno_synastry      * 0.20  # 承諾信號

    if f.bazi_generation:
        score *= 1.2  # 相生滋養加成

    return clamp(score * 100, 0, 100)
```

---

## 5) Power：D/s Frame 計算（含 Chiron 規則）

```python
def calculate_power(f, context="neutral"):
    # 從 RPV 映射 frame score
    # rpv_power: control → +20, follow → -20
    # rpv_conflict: cold_war → +10, argue → -10
    frame_A = rpv_to_frame(A.rpv_power, A.rpv_conflict)
    frame_B = rpv_to_frame(B.rpv_power, B.rpv_conflict)

    # Chiron 觸發規則：A 的 Mars/Pluto 強硬相位踩到 B 的 Chiron
    # → B 的框架穩定性被動搖（-15），frame_break = true
    if f.chiron_triggered_on_B:
        frame_B -= 15

    rpv = frame_A - frame_B

    if rpv > 15:
        viewer_role, target_role = "Dom", "Sub"
    elif rpv < -15:
        viewer_role, target_role = "Sub", "Dom"
    else:
        viewer_role, target_role = "Equal", "Equal"

    return {
        "rpv": rpv,
        "frame_break": f.chiron_triggered_on_B,
        "viewer_role": viewer_role,
        "target_role": target_role
    }
```

**Chiron 觸發判定：** A 的 Mars 或 Pluto 與 B 的 Chiron 形成 square（90°）或 opposition（180°）相位（容許度 ±10°）。

---

## 6) Attachment 依附風格問卷（2 題新問卷）

**目的：** 提供 `attachment_fit` 信號（Soul Score 的 0.20 權重）。

---

**Q_A1：「當你喜歡上一個人，你更像⋯⋯」**

| 選項 | 類型 |
|------|------|
| A. 主動靠近確認，心裡會怕對方突然消失 | `anxious` |
| B. 習慣保持距離，讓感情自然發展 | `avoidant` |
| C. 自然流動，不強求也不逃避 | `secure` |

**Q_A2：「在親密關係裡，你更渴望⋯⋯」**

| 選項 | 類型 |
|------|------|
| A. 成為對方的依靠，被人需要的感覺 | `dom_secure` |
| B. 找到一個能讓你完全放下防備的人 | `sub_secure` |
| C. 兩個獨立個體，有黏著也有空間 | `balanced` |

---

**AttachmentFit 配對矩陣（0.0–1.0）：**

|  | anxious | avoidant | secure |
|--|---------|---------|--------|
| **anxious** | 0.50 | 0.70（張力吸引） | 0.80 |
| **avoidant** | 0.70 | 0.55 | 0.75 |
| **secure** | 0.80 | 0.75 | 0.90 |

> dom/sub 細分在未來 Mode Selector 啟用時加入。

---

## 7) 四軌評分（Tracks）

```python
def calculate_tracks(f, lust, soul, power):
    # 朋友軌：水星溝通 + 木星玩樂 + 八字平和
    friend = (
        0.40 * f.mercury_signal +
        0.40 * f.jupiter_signal +
        0.20 * (1 if f.bazi_harmony else 0)
    )

    # 激情軌：金火吸引 + 冥/八宮極端張力 + 八字相剋
    passion_extremity = max(f.pluto_signal, f.house8_signal or 0)
    passion = (
        0.30 * f.mars_signal +
        0.30 * f.venus_signal +
        0.10 * passion_extremity +
        0.30 * (1 if f.bazi_clash else 0)
    )

    # 伴侶軌：月亮安全感 + 婚神承諾 + 八字相生
    partner = (
        0.35 * f.moon_signal +
        0.35 * f.juno_signal +
        0.30 * (1 if f.bazi_generation else 0)
    )

    # 靈魂軌：凱龍療癒 + 冥王執念 + 喜用神互補
    soul_track = (
        0.40 * f.chiron_signal +
        0.40 * f.pluto_signal +
        0.20 * (1 if f.useful_god_complement else 0)
    )

    # Chiron 觸發 → 靈魂軌加成（傷痛即連結）
    if power["frame_break"]:
        soul_track += 0.10

    return {
        "friend":  clamp(friend * 100, 0, 100),
        "passion": clamp(passion * 100, 0, 100),
        "partner": clamp(partner * 100, 0, 100),
        "soul":    clamp(soul_track * 100, 0, 100),
    }
```

---

## 8) 象限分類（Quadrant）

```
Lust vs Soul 二維矩陣（threshold = 60）：

              Soul < 60     Soul ≥ 60
Lust ≥ 60  →  Lover         Soulmate
Lust < 60  →  Colleague     Partner
```

**卡片主導標籤（primary_track）：** `argmax(friend, passion, partner, soul)` → 顯示一個標籤：
- `friend` → 「✦ 朋友型連結」
- `passion` → 「✦ 激情型連結」
- `partner` → 「✦ 伴侶型連結」
- `soul` → 「✦ 靈魂型連結」

---

## 9) 降級策略總表

| 缺失資料 | 降級方式 |
|---------|---------|
| 無出生時間（Tier 2/3） | `house4_signal = 0`，`house8_signal = 0`，`passion_extremity = pluto_signal` |
| Juno 資料缺失 | `juno_signal = 0.65`（neutral 預設） |
| Chiron 資料缺失 | `chiron_signal = 0.65`，`frame_break = false` |
| attachment 未填 | `attachment_fit = 0.65`（neutral） |
| Eros 未實作 | 由 Venus/Mars/Pluto 補足，passion track 不設 `eros_signal` |

---

## 10) DB 變更（Migration 007）

```sql
-- 新增星體欄位
ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS mercury_sign     TEXT,
  ADD COLUMN IF NOT EXISTS jupiter_sign     TEXT,
  ADD COLUMN IF NOT EXISTS pluto_sign       TEXT,
  ADD COLUMN IF NOT EXISTS chiron_sign      TEXT,
  ADD COLUMN IF NOT EXISTS juno_sign        TEXT,
  ADD COLUMN IF NOT EXISTS house4_sign      TEXT,
  ADD COLUMN IF NOT EXISTS house8_sign      TEXT;

-- 新增 Attachment 問卷欄位
ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS attachment_style TEXT
    CHECK (attachment_style IN ('anxious', 'avoidant', 'secure')),
  ADD COLUMN IF NOT EXISTS attachment_role  TEXT
    CHECK (attachment_role IN ('dom_secure', 'sub_secure', 'balanced'));
```

---

## 11) API 變更

### 11.1 `POST /calculate-chart`（astro-service）

新增回傳欄位：

```json
{
  "mercury_sign": "pisces",
  "jupiter_sign": "aquarius",
  "pluto_sign":   "sagittarius",
  "chiron_sign":  "scorpio",
  "juno_sign":    "taurus",
  "house4_sign":  "cancer",
  "house8_sign":  "scorpio"
}
```

### 11.2 `POST /compute-match`（astro-service）

輸入新增 `mercury_sign, jupiter_sign, pluto_sign, chiron_sign, juno_sign, house4_sign, house8_sign, attachment_style`。

輸出改為新 Schema（見第 2 節），廢棄舊 `Match_Score`。

### 11.3 `POST /api/onboarding/attachment`（Next.js，新增）

接受 Q_A1 + Q_A2 回答，回寫 `users.attachment_style` + `users.attachment_role`。

---

## 12) 出生時間校正整合

出生時間透過 **Phase B.5 Rectification** 問卷逐步校正（已實作）。

校正流程影響配對精度：
- `PRECISE` / 信心值 ≥ 0.80 → House 4/8 完整計算 → Lust/Soul 精準
- `TWO_HOUR_SLOT` → house4/8 = null → 降級策略生效
- `FUZZY_DAY` / `UNKNOWN` → 無宮位 → Pluto/Moon 補位

**關鍵：** 校正後 `tier_upgraded = true` → 需觸發重新計算星盤並回寫新欄位。

---

## 13) 測試要求

| 測試項目 | 數量 |
|---------|------|
| 新星體計算（Mercury/Jupiter/Pluto/Chiron/Juno）正確星座 | 5 |
| House 4/8 宮頭計算（Tier 1 精確時間） | 3 |
| Tier 2/3 降級：house signal = 0 | 2 |
| Lust Score 公式 + BaziClash 乘數 | 4 |
| Soul Score 公式 + BaziGeneration 乘數 | 4 |
| Power：Chiron 觸發 frame_break | 3 |
| 四軌 argmax 穩定性 | 4 |
| Quadrant 分類邊界值 | 4 |
| Attachment 配對矩陣 | 3 |
| 完整 integration test（end-to-end） | 5 |
| **總計** | **~37** |

---

## 14) 未來擴充（Phase G+）

| 功能 | 說明 |
|------|------|
| Eros（愛神星 433）| 下載 `se00433s.se1` → 加入 Lust/Passion，權重 0.15 |
| Lilith（黑月莉莉絲）| 代表壓抑本能與禁忌吸引，比 Eros 更原始 |
| Mode Selector（Hunt/Nest/War）| 不改基礎分，只在排序 score 做 mode reweight |
| 喜用神互補（useful_god_complement）| 進階八字，`soul_track` 的 0.20 |
