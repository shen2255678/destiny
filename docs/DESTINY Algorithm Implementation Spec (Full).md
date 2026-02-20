# DESTINY Algorithm Implementation Spec (Full)

<aside>
🧬

**目的**：完整版規格，包含新星體（Eros/Juno/Chiron）、八字、四軌輸出、模式切換、以及較完整 RPV。

這份是給 AI 生成「完整模組拆分、資料表、API、測試集」用的。

</aside>

## 0) 文件使用規則（避免 AI 讀錯）

- **本文件只保留每個函數的「最終版本」**，不再保留 v0/v1 重複定義。
- 所有權重以「權重表」為準。
- 任何敘事/商業/UI 文案全部放在 Appendix。

---

## 1) Inputs（資料欄位）

### 1.1 Profile

- `birth_date`
- `birth_time`（允許 unknown；若 unknown 走降級策略）
- `birth_place`（lat/lng/timezone）
- `voice_sample_id`（可選）
- `questionnaire`
    - attachment
    - power_preference
    - energy_mode

### 1.2 Astrology (Western)

- Planets: Sun, Moon, Mercury, Venus, Mars, Saturn, Pluto
- Asteroids: **Eros, Juno, Chiron**
- Houses: 4, 8, 5, 7, 10, 12（依需求）
- Aspects: conjunction/opposition/square/trine/sextile

### 1.3 Bazi（八字）

- `day_master_element`
- `five_elements_balance`
- Relations between A/B:
    - `bazi_generation`（相生）
    - `bazi_clash`（相剋）
    - `bazi_harmony`（平和）
    - `useful_god_complement`（喜用神互補，可選進階）

---

## 2) Outputs（統一回傳 Schema）

```json
{
  "lust_score": 0,
  "soul_score": 0,
  "power": {
    "rpv": 0,
    "frame_break": false,
    "viewer_role": "Dom|Sub|Switch|Equal",
    "target_role": "Dom|Sub|Switch|Equal"
  },
  "tracks": {
    "friend": 0,
    "passion": 0,
    "partner": 0,
    "soul": 0
  },
  "primary_track": "friend|passion|partner|soul",
  "quadrant": "friend|lover|partner|colleague",
  "labels": ["#..."],
  "reasons": [{"code": "...", "weight": 0.2, "note": "..."}]
}
```

---

## 3) 權重表（Single Source of Truth）

### 3.1 Axis scoring

#### Lust（X）

- Venus: 0.15
- Mars: 0.20
- House8: 0.15
- Pluto: 0.20
- **Eros: 0.15**
- PowerFit: 0.30
- **BaziClashMultiplier: 1.2**

#### Soul（Y）

- Moon: 0.25
- Mercury: 0.20
- House4: 0.15
- Saturn: 0.20
- Attachment: 0.20
- **Juno: 0.20**
- **BaziGenerationMultiplier: 1.2**

### 3.2 Four-track scoring（可配置）

- `friend = 0.4*water + 0.4*jupiter + 0.2*bazi_harmony`
- `passion = 0.25*mars + 0.25*venus + 0.2*eros + 0.3*bazi_clash`
- `partner = 0.35*moon + 0.35*juno + 0.3*bazi_generation`
- `soul = 0.4*chiron + 0.4*pluto + 0.2*useful_god_complement`

---

## 4) 核心流程（Backend Logic Flow）

```python
f = extract_features(A, B)

lust = calculate_lust_score(f)
soul = calculate_soul_score(f)

power = calculate_power(f, context="neutral")

tracks = calculate_tracks(f, lust, soul, power)
primary_track = argmax(tracks)

quadrant = classify_quadrant(lust, soul)
labels = build_labels(primary_track, quadrant, power)

return build_output(lust, soul, power, tracks, primary_track, quadrant, labels)
```

---

## 5) Scoring：最終版函數（不重複）

### 5.1 Lust（含 Eros + 八字相剋乘數）

```python
def calculate_lust_score(f):
    score = 0

    score += f.venus_synastry * 0.15
    score += f.mars_synastry * 0.20
    score += f.house8_connection * 0.15
    score += f.pluto_intensity * 0.20

    # Upgrade
    score += f.eros_synastry * 0.15

    score += f.power_fit * 0.30

    # multiplier
    if f.bazi_clash:
        score *= 1.2

    return clamp(score * 100, 0, 100)
```

### 5.2 Soul（含 Juno + 八字相生乘數）

```python
def calculate_soul_score(f):
    score = 0

    score += f.moon_synastry * 0.25
    score += f.mercury_synastry * 0.20
    score += f.house4_connection * 0.15
    score += f.saturn_stability * 0.20
    score += f.attachment_fit * 0.20

    # Upgrade
    score += f.juno_synastry * 0.20

    # multiplier
    if f.bazi_generation:
        score *= 1.2

    return clamp(score * 100, 0, 100)
```

---

## 6) Power：RPV（含 Chiron 觸發規則）

### 6.1 規則（最重要）

- 若 `chiron_triggered = true`（A 的 Mars/Pluto 強硬相位踩到 B 的 Chiron）
    - B 的 `S_frame` 直接扣分（建議 -15 起跳，可配置）
    - `frame_break = true`

### 6.2 計算（簡化但可擴充）

```python
def calculate_power(f, context="neutral"):
    # Base frame stability
    frame_A = f.frame_A
    frame_B = f.frame_B

    # Chiron rule
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

---

## 7) 四軌輸出（Tracks）

> 四軌是「核心 Output Labels」。
> 

```python
def calculate_tracks(f, lust, soul, power):
    friend = 0.4*f.water_signal + 0.4*f.jupiter_signal + 0.2*(1 if f.bazi_harmony else 0)
    passion = 0.25*f.mars_signal + 0.25*f.venus_signal + 0.2*f.eros_signal + 0.3*(1 if f.bazi_clash else 0)
    partner = 0.35*f.moon_signal + 0.35*f.juno_signal + 0.3*(1 if f.bazi_generation else 0)
    deep_soul = 0.4*f.chiron_signal + 0.4*f.pluto_signal + 0.2*(1 if f.useful_god_complement else 0)

    # optional: if frame_break then soul track bonus
    if power["frame_break"]:
        deep_soul += 0.1

    return {
        "friend": clamp(friend*100, 0, 100),
        "passion": clamp(passion*100, 0, 100),
        "partner": clamp(partner*100, 0, 100),
        "soul": clamp(deep_soul*100, 0, 100)
    }
```

---

## 8) Mode selector（權重切換）

### Hunt Mode

- 放大：Eros / Mars / Pluto / BaziClash

### Nest Mode

- 放大：Juno / Moon / BaziGeneration / Saturn stability

### War Mode

- 放大：Mercury / Jupiter / skill_complement

> 建議實作：不改基礎分，只在「排序 score」上做 mode reweight。
> 

---

## 9) Quadrant（2D Matrix）

（沿用 MVP 的 deterministic 分類函數）

---

## 10) 最小測試集（建議你一定要做）

- 針對每個模組至少 5 組 fixture：
    - 權重/乘數是否正確
    - Chiron rule 是否確實觸發 frame break
    - 四軌 argmax 是否穩定
    - mode reweight 是否只影響排序，不污染基礎分

---

## Appendix: 保留敘事/商業/UI

- UI 卡片、腳本庫、定價方案、文案生成範例
- 心理學與世界觀敘事
- 長篇示例對話與 persona（Gia/Bonnie/Zhen/Aria）