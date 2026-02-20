# DESTINY Algorithm Implementation Spec (MVP)

<aside>
🎯

**目的**：這份文件是給 AI / 開發者直接落地用的 *最小可行演算法規格*。

只保留「可實作、可測試、可輸出」的核心。

</aside>

## 0) 輸入與依賴（Inputs）

### 必要輸入（MVP）

- `user.birth_date`（YYYY-MM-DD）
- `user.birth_place`（lat/lng + timezone）
- `user.birth_time`（可選，允許未知或模糊區間）
- `user.profile_answers`（MVP 問卷）
    - `attachment_hint`（由 Q1 推導）
    - `power_hint`（由 Q2 推導）
    - `energy_hint`（由 Q3 推導）

### 需要的天文資料/計算

- 行星：Sun / Moon / Mercury / Venus / Mars / Saturn / Pluto
- 宮位：4th / 8th（若出生時間不足，允許降級：略過宮位或使用區間估計）
- 相位：合相 / 衝 / 刑 / 拱 / 六合（角度容許誤差 `orb` 可配置）

---

## 1) 核心輸出（Outputs / Schema）

> 建議所有服務都回同一個 JSON schema。
> 

```json
{
  "lust_score": 0,
  "soul_score": 0,
  "rpv": 0,
  "roles": {
    "viewer_role": "Dom|Sub|Switch|Equal",
    "target_role": "Dom|Sub|Switch|Equal"
  },
  "quadrant": "friend|lover|partner|colleague",
  "labels": ["#..."],
  "reasons": [
    {"code": "VENUS_MARS_TRINE", "weight": 0.20, "note": "..."}
  ]
}
```

---

## 2) 權重表（Single Source of Truth）

> 所有程式碼只讀這張表，避免規格分裂。
> 

### X 軸：Lust（生理吸引）

- Venus: 0.15
- Mars: 0.20
- House 8 overlay: 0.15
- Pluto intensity: 0.20
- Power Dynamic Fit（S/M）: 0.30

### Y 軸：Soul（心理契合）

- Moon: 0.25
- Mercury: 0.20
- House 4 overlay: 0.15
- Saturn stability: 0.20
- Attachment compatibility: 0.20

---

## 3) 主要流程（Deterministic Flow）

```python
features = extract_features(user_A, user_B)

lust = score_lust(features)
soul = score_soul(features)

power = score_power_dynamics(features, context="neutral")

quadrant = classify_quadrant(lust, soul)
labels = build_labels(lust, soul, power, quadrant)

return build_output(lust, soul, power, quadrant, labels)
```

---

## 4) Feature Extraction（最低限度）

### 4.1 Synastry Aspects（相位）

- `venus_mars_aspect_strength`
- `moon_moon_aspect_strength`
- `mercury_mercury_aspect_strength`
- `saturn_personal_aspect_strength`
- `pluto_personal_aspect_strength`

### 4.2 House Overlays（落宮，允許降級）

- `house8_connection_strength`（如果出生時間不可靠，回傳 `null`）
- `house4_connection_strength`（同上）

### 4.3 MVP 心理/權力訊號（問卷）

- `attachment_type`（Anxious / Avoidant / Secure / Disorganized）
- `power_preference`（Dom / Sub / Switch / Equal 的傾向）

---

## 5) Scoring（只保留最終版函數）

### 5.1 Lust Score

```python
def score_lust(f):
    score = 0
    score += f.venus_mars_aspect_strength * 0.15
    score += f.mars_aspect_strength * 0.20
    score += (f.house8_connection_strength or 0) * 0.15
    score += f.pluto_personal_aspect_strength * 0.20
    score += f.power_dynamic_fit * 0.30
    return clamp(score * 100, 0, 100)
```

### 5.2 Soul Score

```python
def score_soul(f):
    score = 0
    score += f.moon_moon_aspect_strength * 0.25
    score += f.mercury_mercury_aspect_strength * 0.20
    score += (f.house4_connection_strength or 0) * 0.15
    score += f.saturn_personal_aspect_strength * 0.20
    score += f.attachment_fit * 0.20
    return clamp(score * 100, 0, 100)
```

---

## 6) Power Dynamics（MVP 版：簡化 RPV）

> MVP 不做「多情境曲線」，先做 deterministic 版本。
> 

```python
def score_power_dynamics(f, context="neutral"):
    # power_dynamic_fit 本身已被算入 Lust
    # 這裡只輸出 rpv 與角色判定，供標籤與 UI 用
    rpv = f.frame_stability_A - f.frame_stability_B

    if rpv > 15:
        roles = ("Dom", "Sub")
    elif rpv < -15:
        roles = ("Sub", "Dom")
    else:
        roles = ("Equal", "Equal")

    return {"rpv": rpv, "roles": roles}
```

---

## 7) Quadrant 分類（2D Matrix）

```python
def classify_quadrant(lust, soul):
    if lust >= 70 and soul >= 70:
        return "partner"
    if lust >= 70 and soul < 50:
        return "lover"
    if lust < 50 and soul >= 70:
        return "friend"
    return "colleague"
```

---

## 8) 最小測試案例（必備）

- Case 1：Lust 高、Soul 低 → lover
- Case 2：Lust 低、Soul 高 → friend
- Case 3：雙高 → partner
- Case 4：雙低 → colleague

---

## Appendix（留白：之後接 Full Spec）

- Eros / Juno / Chiron
- 八字相生/相剋
- 四軌輸出與 mode selector（Hunt/Nest/War）
- 更完整的 RPV（S_Frame / C_Need / 情境係數）