# DESTINY — Astro Service 星盤計算微服務

Python FastAPI 微服務，使用 Swiss Ephemeris 計算出生星盤（natal chart）。

---

## Quick Start

```bash
cd astro-service

# 安裝依賴
pip install -r requirements.txt

# 執行測試
pytest test_chart.py -v

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
  "sun_sign": "gemini",
  "moon_sign": "capricorn",
  "venus_sign": "gemini",
  "mars_sign": "virgo",
  "saturn_sign": "pisces",
  "ascendant_sign": "libra",
  "element_primary": "air"
}
```

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

---

## Data Tier 行為

| Tier | 使用者提供 | 計算結果 |
|------|-----------|---------|
| **1 (Gold)** | 精確出生時間 + 經緯度 | 全部 6 星座 + Ascendant |
| **2 (Silver)** | 模糊時段（morning/afternoon/evening） | Sun, Moon（近似）, Venus, Mars, Saturn。**Ascendant = null** |
| **3 (Bronze)** | 僅出生日期 | Sun, Venus, Mars, Saturn。**Moon = null, Ascendant = null** |

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
| 0 | 0°–30° | Aries ♈ 牡羊 | Fire |
| 1 | 30°–60° | Taurus ♉ 金牛 | Earth |
| 2 | 60°–90° | Gemini ♊ 雙子 | Air |
| 3 | 90°–120° | Cancer ♋ 巨蟹 | Water |
| 4 | 120°–150° | Leo ♌ 獅子 | Fire |
| 5 | 150°–180° | Virgo ♍ 處女 | Earth |
| 6 | 180°–210° | Libra ♎ 天秤 | Air |
| 7 | 210°–240° | Scorpio ♏ 天蠍 | Water |
| 8 | 240°–270° | Sagittarius ♐ 射手 | Fire |
| 9 | 270°–300° | Capricorn ♑ 摩羯 | Earth |
| 10 | 300°–330° | Aquarius ♒ 水瓶 | Air |
| 11 | 330°–360° | Pisces ♓ 雙魚 | Water |

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
├── requirements.txt   # Python 依賴
├── chart.py           # 核心計算模組（calculate_chart, longitude_to_sign）
├── main.py            # FastAPI 應用（/calculate-chart, /health）
└── test_chart.py      # pytest 測試（12 tests）
```

---

## 測試

```bash
cd astro-service
pytest test_chart.py -v
```

測試涵蓋：
- `longitude_to_sign` 單元測試（含邊界值）
- Tier 3：Sun sign 正確性（Gemini, Capricorn, Aries）
- Tier 1：所有 6 個 sign + ascendant 皆有值
- Tier 2：Moon 有值但 Ascendant 為 null
- 星座交界日期（Pisces/Aries, Leo/Virgo）
- 全 12 星座可達性驗證

---

## 待辦 (Next Steps)

1. **串接 Next.js API** — `POST /api/onboarding/birth-data` 完成後自動呼叫 `astro-service/calculate-chart`，將結果回寫 `users` 表
2. **加入 Supabase 回寫** — astro-service 直接用 `supabase-py` 寫入 DB（或由 Next.js API 轉寫）
3. **Daily Matching** — `POST /run-daily-matching` 端點，Cron Job 每日 21:00 執行
4. **部署** — Railway / Fly.io 部署 FastAPI 服務
