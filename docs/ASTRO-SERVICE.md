# DESTINY — Astro Service 星盤計算微服務

Python FastAPI 微服務，使用 Swiss Ephemeris 計算出生星盤（natal chart）。

---

## Quick Start

```bash
cd astro-service

# 安裝依賴
pip install -r requirements.txt

# 執行測試
pytest -v

# 啟動開發伺服器
uvicorn main:app --port 8001 --reload
```

服務啟動後可透過 http://localhost:8001/docs 查看 Swagger UI。

---

## API Endpoints

### `GET /health`

Health check。

```bash
curl http://localhost:8001/health
```

```json
{ "status": "ok" }
```

### `GET /sandbox`

Serves `sandbox.html` — 瀏覽器端演算法驗證工具。

```
http://localhost:8001/sandbox
```

### `POST /calculate-chart`

根據出生資料計算星盤，回傳各行星所在星座。

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `birth_date` | string | Yes | ISO 日期，例如 `"1995-06-15"` |
| `birth_time` | string | No | `"precise"` / `"morning"` / `"afternoon"` / `"evening"` / `"unknown"` |
| `birth_time_exact` | string | No | `"HH:MM"` 格式，僅在 `birth_time = "precise"` 時使用 |
| `lat` | float | No | 出生地緯度（預設 25.033，台北） |
| `lng` | float | No | 出生地經度（預設 121.565，台北） |
| `data_tier` | int | No | 1 (Gold) / 2 (Silver) / 3 (Bronze)，預設 3 |

**範例 — Tier 1（精確時間）:**

```bash
curl -X POST http://localhost:8001/calculate-chart \
  -H "Content-Type: application/json" \
  -d '{
    "birth_date": "1995-06-15",
    "birth_time": "precise",
    "birth_time_exact": "14:30",
    "lat": 25.033,
    "lng": 121.565,
    "data_tier": 1
  }'
```

```json
{
  "data_tier": 1,
  "sun_sign": "gemini",       "sun_degree": 84.21,
  "moon_sign": "capricorn",   "moon_degree": 295.44,
  "mercury_sign": "gemini",   "mercury_degree": 75.12,  "mercury_rx": false,
  "venus_sign": "gemini",     "venus_degree": 70.33,    "venus_rx": false,
  "mars_sign": "virgo",       "mars_degree": 167.88,    "mars_rx": false,
  "jupiter_sign": "sagittarius", "jupiter_degree": 248.91,
  "saturn_sign": "pisces",    "saturn_degree": 332.05,
  "uranus_sign": "capricorn", "uranus_degree": 272.10,
  "neptune_sign": "capricorn","neptune_degree": 295.60,
  "pluto_sign": "scorpio",    "pluto_degree": 231.44,
  "chiron_sign": null,        "chiron_degree": null,
  "juno_sign": null,          "juno_degree": null,
  "ascendant_sign": "libra",  "ascendant_degree": 195.30,
  "house4_sign": "capricorn", "house4_degree": 275.10,
  "house7_sign": "aries",     "house7_degree": 15.30,
  "house8_sign": "taurus",    "house8_degree": 55.30,
  "house12_sign": "virgo",    "house12_degree": 155.70,
  "vertex_sign": "aries",     "vertex_degree": 15.44,
  "lilith_sign": "aquarius",  "lilith_degree": 315.22,
  "element_primary": "air",
  "bazi": { "year_pillar": "乙亥", "month_pillar": "壬午", "day_pillar": "庚申", "hour_pillar": "甲未", "day_master": "庚", "day_master_element": "metal" },
  "emotional_capacity": 65,
  "sm_tags": ["Dom_Dom", "Power_Dom"],
  "karmic_tags": ["Axis_Sign_Gemini_Sag", "North_Node_Sign_Gemini", "Axis_House_1_7", "North_Node_House_1"],
  "element_profile": { "dominant_element": "air", "missing_element": "water" },
  "north_node_sign": "gemini",  "north_node_degree": 71.44,
  "south_node_sign": "sagittarius", "south_node_degree": 251.44,
  "element_profile": { "dominant_element": "air", "missing_element": "water" },
  "natal_aspects": [
    { "a": "sun", "b": "moon", "aspect": "square", "orb": 3.21, "strength": 0.598 }
  ]
}
```

> **Note:** `chiron_sign` 和 `juno_sign` 在小行星星曆檔（`seas_18.se1`）未找到時會回傳 `null`。

**範例 — Tier 3（僅日期）:**

```bash
curl -X POST http://localhost:8001/calculate-chart \
  -H "Content-Type: application/json" \
  -d '{"birth_date": "1995-06-15", "data_tier": 3}'
```

```json
{
  "data_tier": 3,
  "sun_sign": "gemini",
  "moon_sign": null,
  "venus_sign": "gemini",
  "mars_sign": "virgo",
  "saturn_sign": "pisces",
  "ascendant_sign": null,
  "element_primary": "air"
}
```

### `POST /score-compatibility`

相容性評分 — 回傳 Match_Score + 各維度分數。

```bash
curl -X POST http://localhost:8001/score-compatibility \
  -H "Content-Type: application/json" \
  -d '{
    "user_a": { "sun_sign": "aries", "moon_sign": "scorpio", "venus_sign": "pisces", "mars_sign": "leo", "saturn_sign": "capricorn", "bazi_element": "fire" },
    "user_b": { "sun_sign": "leo", "moon_sign": "cancer", "venus_sign": "leo", "mars_sign": "cancer", "saturn_sign": "capricorn", "bazi_element": "water" }
  }'
```

### `POST /analyze-relation`

五行關係分析（相生/相剋/比和）。

```bash
curl -X POST http://localhost:8001/analyze-relation \
  -H "Content-Type: application/json" \
  -d '{"element_a": "fire", "element_b": "water"}'
```

### `POST /compute-match`

雙人合盤配對計算（v2）— 回傳 lust/soul/tracks/power/quadrant 完整分析。

```bash
curl -X POST http://localhost:8001/compute-match \
  -H "Content-Type: application/json" \
  -d '{
    "user_a": {
      "sun_sign": "aries", "moon_sign": "scorpio", "venus_sign": "pisces",
      "mars_sign": "leo", "jupiter_sign": "sagittarius", "saturn_sign": "capricorn",
      "mercury_sign": "aries", "pluto_sign": "scorpio", "chiron_sign": null,
      "juno_sign": null, "ascendant_sign": "libra",
      "house4_sign": "capricorn", "house8_sign": "taurus",
      "bazi_element": "fire", "bazi_month_branch": "午",
      "rpv_conflict": "argue", "rpv_power": "control", "rpv_energy": "out",
      "attachment_style": "secure",
      "emotional_capacity": 70,
      "data_tier": 1,
      "birth_year": 1990, "birth_month": 3, "birth_day": 25,
      "birth_time": "11:30", "gender": "M"
    },
    "user_b": {
      "sun_sign": "leo", "moon_sign": "cancer", "venus_sign": "leo",
      "mars_sign": "cancer", "jupiter_sign": "gemini", "saturn_sign": "capricorn",
      "mercury_sign": "leo", "pluto_sign": "scorpio",
      "bazi_element": "water",
      "rpv_conflict": "cold_war", "rpv_power": "follow", "rpv_energy": "home",
      "attachment_style": "anxious",
      "data_tier": 1,
      "birth_year": 1992, "birth_month": 8, "birth_day": 10,
      "birth_time": "08:00", "gender": "F"
    }
  }'
```

### `POST /compute-zwds-chart`

紫微斗數 12 宮命盤（Tier 1 only）。

```bash
curl -X POST http://localhost:8001/compute-zwds-chart \
  -H "Content-Type: application/json" \
  -d '{"birth_year": 1990, "birth_month": 6, "birth_day": 15, "birth_time": "11:30", "gender": "M"}'
```

### `POST /generate-archetype`

產生 DESTINY 原型報告（5 節：archetype_tags, resonance, shadow, reality_check, evolution）。需要 LLM API key。

```bash
curl -X POST http://localhost:8001/generate-archetype \
  -H "Content-Type: application/json" \
  -d '{
    "match_data": {"lust_score": 80, "soul_score": 65, "primary_track": "passion", "tracks": {"friend": 50, "passion": 80, "partner": 60, "soul": 65}},
    "person_a_name": "A", "person_b_name": "B",
    "mode": "auto",
    "provider": "anthropic",
    "api_key": "sk-ant-..."
  }'
```

### `POST /generate-profile-card`

產生個人靈魂 Profile Card。需要 LLM API key。

```bash
curl -X POST http://localhost:8001/generate-profile-card \
  -H "Content-Type: application/json" \
  -d '{
    "chart_data": {"sun_sign": "aries", "moon_sign": "scorpio", "venus_sign": "pisces", "mars_sign": "leo"},
    "rpv_data": {"rpv_conflict": "argue", "rpv_power": "control", "rpv_energy": "out"},
    "attachment_style": "secure",
    "person_name": "測試用戶",
    "provider": "anthropic",
    "api_key": "sk-ant-..."
  }'
```

回傳：`{headline, shadow_trait, avoid_types, evolution, core}`

### `POST /generate-match-report`

產生雙人關係報告。需要 LLM API key。

回傳：`{title, one_liner, sparks, landmines, advice, core}`

### `POST /generate-ideal-match`

產生理想伴侶輪廓（根據單人星盤）。需要 LLM API key。

```bash
curl -X POST http://localhost:8001/generate-ideal-match \
  -H "Content-Type: application/json" \
  -d '{
    "chart_data": {"sun_sign": "aries", "moon_sign": "scorpio", "venus_sign": "pisces", "mars_sign": "leo"},
    "provider": "anthropic",
    "api_key": "sk-ant-..."
  }'
```

回傳：`{antidote, reality_anchors: [3 items], core_need}`

### `POST /api/users/onboard` 🆕

Onboarding 一站式 API — 計算星盤 + 快取到 Supabase + 回傳安全 DTO。

```bash
curl -X POST http://localhost:8001/api/users/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid-here",
    "birth_date": "1997-03-07",
    "birth_time": "precise",
    "birth_time_exact": "10:59",
    "lat": 25.033, "lng": 121.565,
    "data_tier": 1,
    "gender": "M",
    "generate_report": false
  }'
```

回傳（DTO 脫敏後）：
```json
{
  "status": "success",
  "data": {
    "relationship_dynamic": "high_voltage",
    "psychological_needs": ["渴望被完全理解"],
    "favorable_elements": ["水", "木"],
    "attachment_style": "anxious",
    "ai_natal_report": ""
  }
}
```

> **Note:** Raw chart data 寫入 `user_natal_data` 表，永不回傳前端。

### `POST /api/matches/compute` 🆕

雙人配對 API — 快取查詢 → 計算 → LLM 報告 → DTO 脫敏。

```bash
curl -X POST http://localhost:8001/api/matches/compute \
  -H "Content-Type: application/json" \
  -d '{
    "user_a_id": "uuid-a",
    "user_b_id": "uuid-b",
    "force_recompute": false,
    "generate_report": true,
    "provider": "anthropic",
    "api_key": "sk-ant-..."
  }'
```

回傳（DTO 脫敏後）：
```json
{
  "status": "success",
  "cached": false,
  "data": {
    "harmony_score": 86,
    "tension_level": 3,
    "badges": ["命理雙重認證"],
    "tracks": {"friend": 62, "passion": 79, "partner": 55, "soul": 89},
    "primary_track": "soul",
    "quadrant": "soulmate",
    "ai_insight_report": "你們之間的連結..."
  }
}
```

> **Note:** 第二次呼叫相同 pair 會從 `matches` 表快取直接回傳（`cached: true`）。

---

## Data Tier 行為

| Tier | 使用者提供 | 計算結果 |
|------|-----------|---------|
| **1 (Gold)** | 精確時間 + 座標 | 全行星 + Ascendant + House 4/7/8/12 + Vertex + Lilith + Lunar Nodes + natal_aspects + emotional_capacity |
| **2 (Silver)** | 模糊時段（morning/afternoon/evening） | Sun, Moon（近似）, Venus, Mars, Saturn + Lunar Nodes。**Ascendant = null, House = null** |
| **3 (Bronze)** | 僅出生日期 | Sun, Venus, Mars, Saturn + Lunar Nodes。**Moon = null, Ascendant = null** |

### 模糊時段對應

| `birth_time` | 計算用時間（台北當地時間） |
|---|---|
| `morning` | 09:00 |
| `afternoon` | 14:00 |
| `evening` | 20:00 |
| `unknown` / 未提供 | 12:00（noon） |

---

## 星座對應

黃經每 30° 為一個星座：

| Index | 黃經範圍 | 星座 | Element |
|-------|---------|------|---------|
| 0 | 0°-30° | Aries 牡羊 | Fire |
| 1 | 30°-60° | Taurus 金牛 | Earth |
| 2 | 60°-90° | Gemini 雙子 | Air |
| 3 | 90°-120° | Cancer 巨蟹 | Water |
| 4 | 120°-150° | Leo 獅子 | Fire |
| 5 | 150°-180° | Virgo 處女 | Earth |
| 6 | 180°-210° | Libra 天秤 | Air |
| 7 | 210°-240° | Scorpio 天蠍 | Water |
| 8 | 240°-270° | Sagittarius 射手 | Fire |
| 9 | 270°-300° | Capricorn 摩羯 | Earth |
| 10 | 300°-330° | Aquarius 水瓶 | Air |
| 11 | 330°-360° | Pisces 雙魚 | Water |

`element_primary` 由 Sun sign 推導。

---

## DB 欄位對應

計算結果對應 `users` 表的欄位：

| API Response | DB Column | Type |
|---|---|---|
| `sun_sign` | `users.sun_sign` | TEXT |
| `moon_sign` | `users.moon_sign` | TEXT |
| `venus_sign` | `users.venus_sign` | TEXT |
| `mars_sign` | `users.mars_sign` | TEXT |
| `saturn_sign` | `users.saturn_sign` | TEXT |
| `ascendant_sign` | `users.ascendant_sign` | TEXT |
| `element_primary` | `users.element_primary` | TEXT (fire/earth/air/water) |

---

## 檔案結構

```
astro-service/
├── requirements.txt
├── main.py            # FastAPI server (port 8001) — 15 endpoints (含 2 新 production API)
├── chart.py           # Western astrology: planetary positions + natal aspects + Lilith/Vertex
├── bazi.py            # BaZi 八字四柱: Four Pillars + Five Elements + true solar time
├── matching.py        # Compatibility scoring: lust/soul/tracks/power/quadrant (v2)
├── shadow_engine.py   # Synastry modifiers: Chiron/Vertex/Lilith triggers + 12th house overlay + Lunar Nodes + DSC Overlay (v1.9)
├── psychology.py      # Psychology layer: SM dynamics + retrograde karma + element profile + Karmic Axis (v1.9)
├── zwds.py            # ZiWei DouShu bridge
├── prompt_manager.py  # LLM prompt templates (profile/match/archetype/ideal-match/synastry)
├── api_presenter.py   # 🆕 DTO 脫敏層 (format_safe_match_response / format_safe_onboard_response)
├── db_client.py       # 🆕 Supabase Python client (natal data + psychology + match cache)
├── test_chart.py      # pytest (109 tests)
├── test_matching.py   # pytest (173 tests)
├── test_shadow_engine.py # pytest (56 tests)
├── test_zwds.py       # pytest (31 tests)
├── test_psychology.py # pytest (33 tests)
├── test_sandbox.py    # pytest (5 tests)
├── test_api_presenter.py # 🆕 pytest (34 tests — DTO 安全性稽核)
├── sandbox.html       # Algorithm validation sandbox (browser-based dev tool)
└── ephe/              # Swiss Ephemeris data files
```

---

## 測試

```bash
cd astro-service
pytest -v                       # 全部 446 個測試（Python）
pytest test_chart.py -v         # 109 tests — 西洋占星 + 本命相位 + Lilith/Vertex + Lunar Nodes + House 7
pytest test_matching.py -v      # 173 tests — 配對演算法
pytest test_shadow_engine.py -v # 56 tests — 暗黑修正器 + Descendant Overlay
pytest test_zwds.py -v          # 31 tests — 紫微斗數
pytest test_psychology.py -v    # 33 tests — 心理標籤 + Karmic Axis
pytest test_sandbox.py -v       # 5 tests — Sandbox endpoints
pytest test_api_presenter.py -v # 34 tests — DTO 安全性稽核 🆕
pytest test_prompt_manager.py -v # 15 tests — LLM Prompt 結構
```

測試涵蓋：
- `longitude_to_sign` 單元測試（含邊界值）
- Tier 3：Sun sign 正確性（Gemini, Capricorn, Aries）
- Tier 1：所有行星 sign + ascendant + House 4/7/8/12 + Vertex + Lilith + Lunar Nodes + natal_aspects 皆有值
- Tier 2：Moon 有值但 Ascendant 為 null；Lunar Nodes 有值
- 星座交界日期（Pisces/Aries, Leo/Virgo）
- 全 12 星座可達性驗證
- 配對演算法：lust/soul/tracks/power/quadrant 完整覆蓋
- 暗黑修正器：Chiron/Vertex/Lilith/Lunar Nodes/Descendant synastry triggers
- 紫微斗數：12 宮命盤計算
- 心理標籤：SM dynamics + retrograde karma + element profile + Karmic Axis（Sign+House）
