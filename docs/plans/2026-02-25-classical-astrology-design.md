# Classical Astrology Layer — 定位星鏈 & 互溶 Design Doc

**Date:** 2026-02-25
**Feature:** Algorithm V3 — 廟旺落陷 (Essential Dignities) + 定位星鏈 (Dispositor Chain) + 互溶 (Mutual Reception)
**Spec source:** `docs/plans/2026-02-24-algorithm-v3-bonus-plan.md`
**Approach:** Approach A — psychology.py 純資料層 + ideal_avatar.py 獨立 Rule + matching.py 跨盤互溶

---

## Architecture

```
psychology.py          ← Tasks 1 & 2: 常數 + 純函式
  ESSENTIAL_DIGNITIES
  MODERN_RULERSHIPS
  evaluate_planet_dignity(planet, sign) → str
  find_dispositor_chain(western_chart, start_planet) → dict

ideal_avatar.py        ← Task 3: 獨立 Rule 1.5
  _extract_classical_astrology_layer(western_chart, psych_needs) → Optional[str]
  (called from extract_ideal_partner_profile after Rule 1)

matching.py            ← Task 4: 跨盤互溶 + soul boost + badge
  check_synastry_mutual_reception(chart_a, chart_b) → List[str]
  (called from compute_match_v2 after existing modifiers)
```

---

## Task 1: ESSENTIAL_DIGNITIES + evaluate_planet_dignity (`psychology.py`)

### 常數

```python
ESSENTIAL_DIGNITIES = {
    "Sun":   {"Dignity": ["leo"],               "Exaltation": ["aries"],
              "Detriment": ["aquarius"],         "Fall": ["libra"]},
    "Moon":  {"Dignity": ["cancer"],            "Exaltation": ["taurus"],
              "Detriment": ["capricorn"],        "Fall": ["scorpio"]},
    "Venus": {"Dignity": ["taurus", "libra"],   "Exaltation": ["pisces"],
              "Detriment": ["scorpio", "aries"], "Fall": ["virgo"]},
    "Mars":  {"Dignity": ["aries", "scorpio"],  "Exaltation": ["capricorn"],
              "Detriment": ["libra", "taurus"],  "Fall": ["cancer"]},
}
```

僅個人行星（日月金火）。外行星世代影響過大，不列入個人心理狀態計算。

### 函式

```python
def evaluate_planet_dignity(planet_name: str, sign_name: str) -> str:
    """
    回傳: "Dignity" | "Exaltation" | "Detriment" | "Fall" | "Peregrine"
    未知行星/星座 → 靜默回傳 "Peregrine"，不 crash。
    sign_name 接受小寫（"scorpio"）或 title case（"Scorpio"）。
    """
```

---

## Task 2: MODERN_RULERSHIPS + find_dispositor_chain (`psychology.py`)

### 常數

```python
MODERN_RULERSHIPS = {
    "aries": "Mars",  "taurus": "Venus",    "gemini": "Mercury",
    "cancer": "Moon", "leo": "Sun",         "virgo": "Mercury",
    "libra": "Venus", "scorpio": "Pluto",   "sagittarius": "Jupiter",
    "capricorn": "Saturn", "aquarius": "Uranus", "pisces": "Neptune",
}
```

### 函式

```python
def find_dispositor_chain(western_chart: dict, start_planet: str) -> dict:
    """
    從 start_planet 出發，追溯守護星鏈直到終止條件。

    回傳:
      {
        "chain": ["Venus", "Mars", "Pluto"],   # 順序鏈條
        "final_dispositor": "Pluto",           # 最終定位星（或 None）
        "mutual_reception": ["Venus", "Mars"], # 互溶對（或 []）
        "status": "final_dispositor" | "mutual_reception" | "mixed_loop" | "incomplete"
      }
    """
```

### 內部演算法

行星名 → chart key 映射：`"Sun" → "sun_sign"`, `"Venus" → "venus_sign"`, etc.（全小寫 + `_sign`）

```
while True:
    current_sign = western_chart.get(f"{current_planet.lower()}_sign")
    if current_sign is None:
        status = "incomplete"; break          # Tier 3 月亮缺失 → 提早回傳

    next_planet = MODERN_RULERSHIPS.get(current_sign.lower())
    if not next_planet:
        status = "incomplete"; break

    # 終止條件 1 — Final Dispositor (自守)
    owned_signs = [s for s,r in MODERN_RULERSHIPS.items() if r == current_planet]
    if current_sign.lower() in owned_signs:
        final_dispositor = current_planet; break

    # 終止條件 2 — Mutual Reception
    next_sign = western_chart.get(f"{next_planet.lower()}_sign", "")
    next_owned = [s for s,r in MODERN_RULERSHIPS.items() if r == current_planet]
    if next_sign.lower() in next_owned:
        mutual_reception = [current_planet, next_planet]; break

    # 終止條件 3 — Endless Loop (visited > 3 unique planets)
    if next_planet in visited or len(visited) >= 3:
        status = "mixed_loop"; break

    visited.add(current_planet)
    current_planet = next_planet
```

---

## Task 3: `_extract_classical_astrology_layer` (`ideal_avatar.py`)

```python
def _extract_classical_astrology_layer(
    western_chart: dict,
    psych_needs: List[str],
) -> Optional[str]:
    """Rule 1.5: Classical astrology — dignity, dispositor chain, natal mutual reception.

    Returns relationship_dynamic hint: "high_voltage" | "stable" | None
    """
```

### 步驟 1 — 廟旺落陷 (Venus + Moon)

```
venus_sign = western_chart.get("venus_sign")
moon_sign  = western_chart.get("moon_sign")   # None at Tier 3 → skip

for (planet, sign) in [(Venus, venus_sign), (Moon, moon_sign)]:
    if sign is None: continue
    state = evaluate_planet_dignity(planet, sign)
    if state in ("Detriment", "Fall"):
        inject "感情中容易缺乏安全感，帶有較強的執念、防禦機制與測試心理"
        dynamic_hint = "high_voltage"
    elif state in ("Dignity", "Exaltation"):
        inject "感情需求直接且純粹，有能力給予並享受穩定的愛"
        if dynamic_hint is None: dynamic_hint = "stable"
```

### 步驟 2 — Final Dispositor 潛意識大 Boss

```
對 Sun/Moon/Venus/Mars 各跑 find_dispositor_chain()
Moon chain → 若 status=="incomplete" 直接跳過
統計 final_dispositor 出現次數，取最多者

Boss 映射：
  Pluto | Saturn   → "潛意識底層受到強烈的業力驅動..."
  Venus | Jupiter  → "生命底層渴望和諧與豐盛..."
  Uranus | Mercury → "極度需要心智上的刺激與靈魂自由..."
  其他 (Moon/Sun/Mars) → 不注入
```

### 步驟 3 — 單人盤互溶 (Natal Mutual Reception)

呼叫 `find_dispositor_chain` 偵測到 `status == "mutual_reception"` 時，根據互溶組合注入標籤：

| 組合 | 標籤 | dynamic |
|------|------|---------|
| Venus ↔ Mars | 情慾與愛情的表達充滿張力與宿命感... | `high_voltage` |
| Sun ↔ Moon | 內在意志與情緒極度自洽... | — |
| Venus ↔ Jupiter / Venus ↔ Moon | 感情中擁有強大的滋養能力... | — |

### 整合進 `extract_ideal_partner_profile`

```python
# Rule 1.5 (after Rule 1, before Rule 2)
classical_dynamic = _extract_classical_astrology_layer(western_chart, psych_needs)
if classical_dynamic == "high_voltage":
    relationship_dynamic = "high_voltage"
elif classical_dynamic == "stable" and relationship_dynamic != "high_voltage":
    relationship_dynamic = "stable"
```

---

## Task 4: `check_synastry_mutual_reception` (`matching.py`)

```python
def check_synastry_mutual_reception(chart_a: dict, chart_b: dict) -> List[str]:
    """
    檢查三組跨盤互溶（雙向各查一次）。
    chart_a / chart_b 為 western_chart dict（含 {planet}_sign 欄位）。
    Missing sign → 靜默跳過，不 crash。
    """
```

### 三組規則

使用 `MODERN_RULERSHIPS` 做通用判斷（不 hardcode 星座名稱）：

```python
def _is_mutual_reception(sign_a: str, sign_b: str, planet_a: str, planet_b: str) -> bool:
    return (MODERN_RULERSHIPS.get(sign_a.lower()) == planet_b and
            MODERN_RULERSHIPS.get(sign_b.lower()) == planet_a)
```

| 組合 | 條件 | 徽章 |
|------|------|------|
| 日月互溶 | `_is_mutual_reception(a_sun, b_moon, "Sun", "Moon")` (或反向) | `古典業力：日月互溶 (靈魂深處的陰陽完美契合)` |
| 金火互溶 | `_is_mutual_reception(a_venus, b_mars, "Venus", "Mars")` (或反向) | `古典業力：金火互溶 (無法抗拒的致命吸引力與肉體契合)` |
| 金月互溶 | `_is_mutual_reception(a_venus, b_moon, "Venus", "Moon")` (或反向) | `古典業力：金月互溶 (無條件的溫柔接納與情緒滋養)` |

### Wiring 進 `compute_match_v2`（Apply modifiers 之後，resonance_badges 計算之前）

```python
# ── Synastry Mutual Reception (classical astrology) ───────────────────────
_western_a = chart_a.get("western_chart", chart_a)   # 容錯：直接傳 chart 或含 western_chart 的 wrapper
_western_b = chart_b.get("western_chart", chart_b)
synastry_mr_badges = check_synastry_mutual_reception(_western_a, _western_b)
for _ in synastry_mr_badges:
    soul = soul + (1.0 - soul) * 0.22   # 邊際遞減，每個 badge +22% 剩餘空間
resonance_badges.extend(synastry_mr_badges)
```

---

## Tier 降級防呆

| 情況 | 處理 |
|------|------|
| Tier 3（無月亮） | `moon_sign = None` → dignity check 跳過；chain 回傳 `incomplete` → boss 統計排除 |
| 任何 sign 為 None | `.get()` 回 None → 所有條件不成立，靜默跳過 |
| `extract_ideal_partner_profile({}, {}, {})` | 全空輸入 → 三個步驟全部無輸出，不 crash |

---

## Test Plan（目標 +23 tests → 581 total）

### `test_psychology.py` +10

| # | 測試 |
|---|------|
| 1 | Venus in scorpio → Detriment |
| 2 | Mars in capricorn → Exaltation |
| 3 | Moon in taurus → Exaltation |
| 4 | Sun in aquarius → Detriment |
| 5 | Unknown planet → Peregrine |
| 6 | `find_dispositor_chain` — Venus in Taurus → Final Dispositor = Venus (self-rules Taurus) |
| 7 | `find_dispositor_chain` — Venus in Aries, Mars in Libra → mutual_reception = [Venus, Mars] |
| 8 | `find_dispositor_chain` — mixed loop (3+ planets, no resolution) → mixed_loop |
| 9 | `find_dispositor_chain` — start planet sign is None (Tier 3 Moon) → incomplete |
| 10 | `find_dispositor_chain` — multi-hop chain reaching Final Dispositor (e.g., Moon→Cancer→Moon self-rules) |

### `test_ideal_avatar.py` +8

| # | 測試 |
|---|------|
| 1 | Venus Detriment → psychological_needs includes "執念"，dynamic = high_voltage |
| 2 | Moon Exaltation → psychological_needs includes "穩定的愛"，dynamic = stable |
| 3 | Pluto as dominant boss → "業力驅動" in needs |
| 4 | Venus/Jupiter as dominant boss → "豐盛" in needs |
| 5 | Venus-Mars natal mutual reception → "執念、佔有慾" in needs + high_voltage |
| 6 | Tier 3 chart (moon_sign=None) → no crash，dignities still run for Venus |
| 7 | Empty western_chart {} → no crash，returns None dynamic |
| 8 | Sun-Moon mutual reception → "自洽" tag injected |

### `test_matching.py` +5

| # | 測試 |
|---|------|
| 1 | Venus-Mars synastry MR → badge 金火互溶 + soul boost |
| 2 | Sun-Moon synastry MR → badge 日月互溶 |
| 3 | Venus-Moon synastry MR → badge 金月互溶 |
| 4 | No MR → no badge, soul unchanged |
| 5 | Missing sign (None) in one chart → no crash |

---

## Files Modified

| File | Change |
|------|--------|
| `astro-service/psychology.py` | Add `ESSENTIAL_DIGNITIES`, `MODERN_RULERSHIPS`, `evaluate_planet_dignity()`, `find_dispositor_chain()` |
| `astro-service/ideal_avatar.py` | Add `_extract_classical_astrology_layer()` + wire into `extract_ideal_partner_profile()` |
| `astro-service/matching.py` | Add `check_synastry_mutual_reception()` + wire into `compute_match_v2()` |
| `astro-service/test_psychology.py` | +10 tests |
| `astro-service/test_ideal_avatar.py` | +8 tests |
| `astro-service/test_matching.py` | +5 tests |

**No DB migration needed** — all new functions use runtime chart data passed in request body.
