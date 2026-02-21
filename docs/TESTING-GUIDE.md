# DESTINY — Testing Guide

**Last Updated:** 2026-02-21 (Phase H ✅ — 91 JS + 132 Python tests)

---

## 測試策略概覽

DESTINY 採四層測試架構，建議依序執行：

| Layer | 工具 | 用途 | 需要服務？ |
|-------|------|------|-----------|
| **Layer 0: Sandbox 算法驗證** | `http://localhost:8001/sandbox` | 手動驗證排盤正確性 + 配對演算法 | astro-service |
| **Layer 1: Unit Tests** | Vitest + mocks | 驗證 API 邏輯、錯誤處理 | No (全 mock) |
| **Layer 2: Manual E2E** | 瀏覽器 + dev server | 完整流程測試 | **Supabase + astro-service** |
| **Layer 3: API Testing** | 瀏覽器 Console fetch | 直接打端點驗證 response | **Supabase** |

> **Note:** 上線新版算法或調整星盤參數前，**必須先通過 Layer 0 驗證**，
> 再執行 Layer 1–3。

---

## Layer 0: Sandbox 算法驗證（上線前必做）

Sandbox 是算法驗證的主要工具，無需 Next.js 或 Supabase，只需啟動
astro-service 即可使用。

### 啟動

```bash
cd astro-service
uvicorn main:app --port 8001
```

開啟 `http://localhost:8001/sandbox`。

### Phase 0-A：排盤準確性驗證（先做這個）

在跑配對演算法前，先確認三套排盤系統輸出正確。

#### 西洋占星 + 八字（`/calculate-chart`）

```bash
curl -s -X POST http://localhost:8001/calculate-chart \
  -H "Content-Type: application/json" \
  -d '{
    "birth_date": "1997-03-07",
    "birth_time": "precise",
    "birth_time_exact": "10:59",
    "lat": 25.033, "lng": 121.565,
    "data_tier": 1
  }' | python -m json.tool
```

**驗證重點：**

| 欄位 | 預期值 |
|---|---|
| `sun_sign` | `"pisces"` |
| `bazi.four_pillars` | `丁丑 癸卯 戊申 丁巳` |
| `bazi.day_master` | `"戊"` |
| `bazi_element` | `"earth"` |

#### 紫微斗數（`/compute-zwds-chart`）

```bash
curl -s -X POST http://localhost:8001/compute-zwds-chart \
  -H "Content-Type: application/json" \
  -d '{
    "birth_year": 1990,
    "birth_month": 6,
    "birth_day": 15,
    "birth_time": "11:30",
    "gender": "M"
  }' | python -m json.tool
```

**驗證重點：**

| 欄位 | 預期值 |
|---|---|
| `chart.five_element` | `"火六局"` |
| `chart.four_transforms.hua_lu` | `"太陰"` （庚年） |
| `chart.four_transforms.hua_ji` | `"天同"` （庚年） |
| `chart.palaces.ming.main_stars` | 非空陣列 |

#### 五行關係（`/analyze-relation`）

```bash
curl -s -X POST http://localhost:8001/analyze-relation \
  -H "Content-Type: application/json" \
  -d '{"element_a":"wood","element_b":"fire"}'
# 預期: { "relation": "a_generates_b", "harmony_score": 0.85 }
```

### Phase 0-B：配對演算法驗證（在排盤通過後）

使用 Sandbox Tab A 輸入已知關係的兩人資料，確認演算法的
MATCH / MISMATCH 判斷符合 ground truth。

詳細操作見 `docs/SANDBOX-GUIDE.md`。

---

## Layer 1: Unit Tests (Mock — 不需真實 DB)

現有 **91 JS unit tests**（14 個測試檔），全部使用 mock Supabase client。

### 執行方式

```bash
cd destiny-app

# 執行全部測試（一次性）
npm test

# Watch mode（修改檔案自動重跑）
npm run test:watch

# 只跑特定測試檔
npx vitest run src/__tests__/api/onboarding-birth-data.test.ts

# 跑特定 describe/it（用 -t flag）
npx vitest run -t "saves birth data"
```

### 現有測試清單

```
src/__tests__/
├── auth.test.ts                                   # 10 tests — register/login/logout 邏輯
├── login-page.test.tsx                            # 4 tests  — Login 頁面互動
├── register-page.test.tsx                         # 5 tests  — Register 頁面互動
└── api/
    ├── onboarding-birth-data.test.ts              # 14 tests — data_tier + ZWDS write-back
    ├── onboarding-rpv-test.test.ts                # 3 tests  — RPV 儲存 + 驗證
    ├── onboarding-photos.test.ts                  # 5 tests  — 照片上傳 + blur + 驗證
    ├── onboarding-soul-report.test.ts             # 3 tests  — 原型生成 + onboarding complete
    ├── matches-daily.test.ts                      # 5 tests  — 今日配對卡 + interest_tags
    ├── matches-action.test.ts                     # 7 tests  — Accept/Pass + mutual accept → connection
    ├── connections.test.ts                        # 5 tests  — connections 列表 + other_user + tags
    ├── connections-messages.test.ts               # 8 tests  — GET/POST messages + is_self + 403
    ├── rectification-next-question.test.ts        # 6 tests  — 選題邏輯 + 204 locked + boundary 優先
    └── rectification-answer.test.ts               # 9 tests  — Via Negativa + confidence + lock + event
```

### 各模組測試覆蓋範圍

| 模組 | Tests | 驗證項目 |
|------|-------|---------|
| Auth | 10 | register/login/logout/getCurrentUser + email/password 驗證 |
| Onboarding birth-data | 14 | data_tier 1/2/3、accuracy_type、ZWDS write-back（成功 + 失敗不阻塞） |
| Onboarding RPV | 3 | 儲存 conflict/power/energy、401、400 |
| Onboarding photos | 5 | 上傳+blur、401、400 missing/type/size |
| Onboarding soul-report | 3 | archetype gen、onboarding_step=complete、401 |
| Daily matches | 5 | 200 with cards、401、empty state、interest_tags shape |
| Match action | 7 | accept、pass、mutual accept → connection、401、400、404、no duplicate |
| Connections list | 5 | 200 with list、401、empty state、other_user、tags from match |
| Messages GET/POST | 8 | detail+msgs、is_self flag、403 non-member、201 insert、401/400 |
| Rectification next-question | 6 | 401、204 locked、204 PRECISE、response shape、2 options、boundary priority |
| Rectification answer | 9 | 401、400 (3 種)、200 state、confidence > old、event log、users update、tier_upgraded |

---

## Layer 2: Manual E2E Testing (真實 Supabase)

### 前置準備

```bash
cd destiny-app

# 確認 .env.local 存在且正確
cat .env.local
# 應該看到:
# NEXT_PUBLIC_SUPABASE_URL=https://masninqgihbazjirweiy.supabase.co
# NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...

# 啟動 dev server
npm run dev
```

### 完整測試流程 Checklist

#### Step 0: 註冊帳號
- [ ] 開啟 http://localhost:3000/register
- [ ] 輸入 email + password (≥8 字元)
- [ ] 點擊 Register
- [ ] 預期: 自動導向 `/onboarding/birth-data`
- [ ] 驗證: Supabase Dashboard → Authentication → Users 應該看到新用戶

> **Tips:** 可以用假 email 如 `test1@example.com`（Supabase 預設不驗證 email）

---

#### Step 1: Birth Data — 4-card 精度流程 (Phase B.5)
- [ ] 選擇精確度卡片：
  - **卡片 A「我有精確時間」** → 出現 time picker (HH:mm)，填入精確時間（如 14:30）
  - **卡片 B「我知道大概時段」** → 出現 12 格 2hr grid，點選一格
  - **卡片 C「我只知道大概」** → 出現 早上/下午/晚上 3 個選項
  - **卡片 D「我完全不知道」** → 直接可點 Continue
- [ ] 填寫出生日期 + 出生城市
- [ ] 點擊 Continue → 預期導向 `/onboarding/rpv-test`
- [ ] 驗證 Supabase `users` 表：
  - `birth_date`, `birth_city` 已寫入
  - `accuracy_type` = `PRECISE` / `TWO_HOUR_SLOT` / `FUZZY_DAY`
  - `current_confidence` = 0.90 / 0.30 / 0.15 / 0.05
  - `rectification_status` = `collecting_signals`
  - `window_start`, `window_end`, `window_size_minutes` 有值
- [ ] 驗證 `rectification_events` 表：有一筆 `event_type = range_initialized` 記錄
- [ ] **（Tier 1 only）** 驗證 `users` 表 ZWDS 欄位已寫入：
  - `zwds_five_element` 非 null（如 `"火六局"`）
  - `zwds_life_palace_stars` 非空陣列
  - `zwds_four_transforms` 為 JSONB 物件

---

#### Step 2: RPV Test
- [ ] 3 題都選擇一個選項
- [ ] 點擊 Continue → 預期導向 `/onboarding/photos`
- [ ] 驗證: users 表 → `rpv_conflict`, `rpv_power`, `rpv_energy` 已寫入

---

#### Step 3: Photos
- [ ] 上傳兩張圖片
- [ ] 驗證: Supabase Storage → photos bucket → `{user_id}/original_1.jpg`, `blurred_1.jpg`

---

#### Step 4: Soul Report
- [ ] 頁面載入後應顯示動態原型
- [ ] 點擊「Enter DESTINY」→ 預期導向 `/daily`
- [ ] 驗證: users 表 → `archetype_name`, `onboarding_step = complete`

---

#### Step 5: Daily Feed
- [ ] 顯示 3 張配對卡（或 empty state）
- [ ] Accept → 按鈕變綠色；Pass → 卡片消失
- [ ] 若兩個用戶互 Accept → 自動建立 connection

---

#### Step 6: Connections + Chat
- [ ] 開啟 http://localhost:3000/connections → 顯示所有 active connections
- [ ] 點擊卡片 → 進入聊天室
- [ ] 輸入訊息 → 樂觀更新，對方瀏覽器即時顯示

---

### 常見問題排除

| 問題 | 原因 | 解法 |
|------|------|------|
| Register 後沒有自動跳轉 | Email confirmation 開啟 | Dashboard → Auth Settings → 關閉 email confirm |
| 401 錯誤 | Cookie 沒有正確設定 | 清除 cookies，重新登入 |
| Photos 上傳失敗 | Storage bucket 權限 | 確認 RLS policy 允許 authenticated users 上傳 |
| Daily 空白 | 無配對資料 | 執行 `POST /api/matches/run` seed 資料（需 CRON_SECRET） |
| ZWDS 欄位為 null | astro-service 未啟動 | 確認 `http://localhost:8001/health` 回傳 ok |
| rectification_events 沒有資料 | Migration 未套用 | 確認已執行 `supabase db push`（008 最新） |

---

## Layer 3: API Testing (瀏覽器 Console)

先登入 http://localhost:3000/login，然後在 DevTools Console 執行：

### Onboarding

```javascript
// ---- Birth Data: 精確時間 (Tier 1) ----
await fetch('/api/onboarding/birth-data', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    birth_date: '1995-06-15',
    accuracy_type: 'PRECISE',
    birth_time_exact: '14:30',
    birth_city: '台北市',
  }),
}).then(r => r.json()).then(console.log)
// 預期: { data: { accuracy_type: 'PRECISE', current_confidence: 0.9, ... } }

// ---- Birth Data: 模糊時段 (Tier 2) ----
await fetch('/api/onboarding/birth-data', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    birth_date: '1995-06-15',
    accuracy_type: 'TWO_HOUR_SLOT',
    window_start: '13:00',
    window_end: '15:00',
    birth_city: '台北市',
  }),
}).then(r => r.json()).then(console.log)

// ---- RPV Test ----
await fetch('/api/onboarding/rpv-test', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ rpv_conflict: 'cold_war', rpv_power: 'control', rpv_energy: 'home' }),
}).then(r => r.json()).then(console.log)
```

### Rectification

```javascript
// ---- 取得下一道校正題 ----
await fetch('/api/rectification/next-question').then(r => r.json()).then(console.log)
// 預期 200: { question_id, phase, question_text, options: [{id, label, eliminates}], context }
// 預期 204: 若 accuracy_type = PRECISE 或 status = locked

// ---- 提交答案 ----
await fetch('/api/rectification/answer', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question_id: 'moon_exclusion_aries_taurus',
    selected_option: 'A',
    source: 'daily_quiz',
  }),
}).then(r => r.json()).then(console.log)
```

---

## Astro Service 測試

### 啟動服務

```bash
cd astro-service
pip install -r requirements.txt    # 首次安裝（含 lunardate）
uvicorn main:app --port 8001       # 啟動
```

### Python Unit Tests (132 tests)

```bash
cd astro-service

# 紫微斗數排盤引擎 (31 tests)
pytest test_zwds.py -v

# 星盤 + 八字 + 五行關係 (30 tests)
pytest test_chart.py -v

# 配對演算法 + ZWDS 整合 (71 tests)
pytest test_matching.py -v

# 全部一起跑
pytest -v
```

**test_zwds.py 測試分類（31 tests）：**

| 類別 | 測試項目 | 數量 |
|------|---------|------|
| 時辰地支 | get_hour_branch 12 種分段 | 5 |
| 四化星 | get_four_transforms 年干對應 | 2 |
| 命盤計算 | compute_zwds_chart 輸出結構 | 8 |
| 宮位能量 | get_palace_energy 空宮借星 | 2 |
| 煞星防禦 | detect_stress_defense 三種觸發 | 4 |
| 主星人設 | get_star_archetype_mods | 2 |
| 合盤引擎 | compute_zwds_synastry 端對端 | 8 |

**test_chart.py 測試分類（30 tests）：**

| 類別 | 測試項目 | 數量 |
|------|---------|------|
| 西洋占星 | Sun sign 12 星座、Tier 1/2/3 行為、邊界日期 | 12 |
| 八字四柱 | 日主、四柱結構、年柱/日柱驗證、Tier 行為 | 11 |
| 五行關係 | 相生/相剋/比和 全循環 | 7 |

**test_matching.py 測試分類（71 tests）：**

| 類別 | 測試項目 | 數量 |
|------|---------|------|
| 星座相位 (sign_aspect) | 合/刑/沖/拱/六合 + edge cases | 9 |
| lust_score / soul_score | 各行星權重 + BaZi 修正 | 12 |
| Power dynamic | Chiron 觸發、RPV 組合 | 8 |
| compute_tracks | 四軌分數 + BaZi 軌道 | 10 |
| classify_quadrant | 四象限分類 | 4 |
| compute_match_v2 | 端對端整合（含 ZWDS）| 12 |
| ZWDS 整合 | Tier 1 ZWDS 輸出鍵 + Tier 3 跳過 + 異常安全 | 8 |
| 舊版 compute_match_score | 向後相容 | 8 |

### API 測試（curl）

```bash
# 健康檢查
curl http://localhost:8001/health

# 西洋占星 + 八字（Tier 1: 精確時間）
curl -X POST http://localhost:8001/calculate-chart \
  -H "Content-Type: application/json" \
  -d '{"birth_date":"1997-03-07","birth_time":"precise","birth_time_exact":"10:59","lat":25.033,"lng":121.565,"data_tier":1}'
# 預期: sun_sign="pisces", bazi.four_pillars=丁丑 癸卯 戊申 丁巳

# 紫微斗數命盤（Tier 1）
curl -X POST http://localhost:8001/compute-zwds-chart \
  -H "Content-Type: application/json" \
  -d '{"birth_year":1990,"birth_month":6,"birth_day":15,"birth_time":"11:30","gender":"M"}'
# 預期: chart.five_element="火六局", chart.palaces.ming.main_stars 非空

# 五行關係分析
curl -X POST http://localhost:8001/analyze-relation \
  -H "Content-Type: application/json" \
  -d '{"element_a":"wood","element_b":"fire"}'
# 預期: { "relation": "a_generates_b", "harmony_score": 0.85 }

# 配對分數計算（Tier 1 雙人，含 ZWDS）
curl -X POST http://localhost:8001/compute-match \
  -H "Content-Type: application/json" \
  -d '{
    "user_a": {
      "sun_sign":"aries","mars_sign":"scorpio","bazi_element":"fire",
      "birth_year":1990,"birth_month":6,"birth_day":15,
      "birth_time":"11:30","data_tier":1,"gender":"M"
    },
    "user_b": {
      "sun_sign":"leo","mars_sign":"cancer","bazi_element":"water",
      "birth_year":1992,"birth_month":9,"birth_day":22,
      "birth_time":"08:00","data_tier":1,"gender":"F"
    }
  }'
# 預期: lust_score, soul_score, zwds.spiciness_level, layered_analysis 均有值
```

---

### API Sample Bodies（可複製修改的請求範例）

以下為實際測試驗證過的請求體，可直接複製並修改日期進行測試。

> **使用流程：** 先用 `/calculate-chart` 和 `/compute-zwds-chart` 確認排盤正確，
> 再組裝 `/compute-match` 的請求體。

#### `/calculate-chart` 請求體

```json
// 範例 A — 1995-03-26 14:30 台北（Tier 1）
// 驗證結果：sun=aries, asc=leo, 日主丙火, 四柱=乙亥己卯丙辰乙未
{
  "birth_date": "1995-03-26",
  "birth_time": "precise",
  "birth_time_exact": "14:30",
  "lat": 25.033,
  "lng": 121.565,
  "data_tier": 1
}

// 範例 B — 1997-03-07 10:59 台北（Tier 1，Ground Truth）
// 驗證結果：sun=pisces, asc=gemini, 日主戊土, 四柱=丁丑癸卯戊申丁巳
{
  "birth_date": "1997-03-07",
  "birth_time": "precise",
  "birth_time_exact": "10:59",
  "lat": 25.033,
  "lng": 121.565,
  "data_tier": 1
}

// 範例 C — 1996-11-07 19:05 台北（Tier 1）
// 驗證結果：sun=scorpio, asc=gemini, 日主戊土, 四柱=丙子己亥戊申壬戌
{
  "birth_date": "1996-11-07",
  "birth_time": "precise",
  "birth_time_exact": "19:05",
  "lat": 25.033,
  "lng": 121.565,
  "data_tier": 1
}

// 範例 D — 1997-06-07 06:00 台北（Tier 1）
// 驗證結果：sun=gemini, asc=gemini, 日主庚金, 四柱=丁丑丙午庚辰己卯
{
  "birth_date": "1997-06-07",
  "birth_time": "precise",
  "birth_time_exact": "06:00",
  "lat": 25.033,
  "lng": 121.565,
  "data_tier": 1
}

// 範例 E — 1997-03-08 20:00 台北（Tier 1）
// 驗證結果：sun=pisces, asc=libra, 日主己土, 四柱=丁丑癸卯己酉甲戌
{
  "birth_date": "1997-03-08",
  "birth_time": "precise",
  "birth_time_exact": "20:00",
  "lat": 25.033,
  "lng": 121.565,
  "data_tier": 1
}

// 範例 F — 1997-05-01 12:00 台北（Tier 1）
// 驗證結果：sun=taurus, asc=leo, 日主癸水, 四柱=丁丑甲辰癸卯戊午
{
  "birth_date": "1997-05-01",
  "birth_time": "precise",
  "birth_time_exact": "12:00",
  "lat": 25.033,
  "lng": 121.565,
  "data_tier": 1
}

// Tier 2 範本（模糊時段）
{
  "birth_date": "YYYY-MM-DD",
  "birth_time": "fuzzy_period",
  "window_start": "08:00",
  "window_end": "10:00",
  "lat": 25.033,
  "lng": 121.565,
  "data_tier": 2
}

// Tier 3 範本（僅出生日期）
{
  "birth_date": "YYYY-MM-DD",
  "birth_time": "unknown",
  "lat": 25.033,
  "lng": 121.565,
  "data_tier": 3
}
```

#### `/compute-zwds-chart` 請求體

```json
// 範例 A — 1995-03-26 14:30 男
// 驗證結果：水二局, 命宮七殺（殺破狼人設）
{
  "birth_year": 1995, "birth_month": 3, "birth_day": 26,
  "birth_time": "14:30", "gender": "M"
}

// 範例 B — 1997-03-07 10:59 男
// 驗證結果：土五局, 命宮空宮借星（is_chameleon=true, RPV -10）
{
  "birth_year": 1997, "birth_month": 3, "birth_day": 7,
  "birth_time": "10:59", "gender": "M"
}

// 範例 C — 1996-11-07 19:05 男
// 驗證結果：土五局, 命宮武曲+天府（紫府武相人設）
{
  "birth_year": 1996, "birth_month": 11, "birth_day": 7,
  "birth_time": "19:05", "gender": "M"
}

// 範例 D — 1997-06-07 06:00 女
// 驗證結果：金四局, 命宮天府（紫府武相人設）, 夫妻宮陀羅→ silent_rumination
{
  "birth_year": 1997, "birth_month": 6, "birth_day": 7,
  "birth_time": "06:00", "gender": "F"
}

// 範例 E — 1997-03-08 20:00 男
// 驗證結果：火六局, 命宮七殺（殺破狼人設）, 夫妻宮武曲+天相
{
  "birth_year": 1997, "birth_month": 3, "birth_day": 8,
  "birth_time": "20:00", "gender": "M"
}

// 範例 F — 1997-05-01 12:00 女
// 驗證結果：金四局, 命宮空宮借星（變色龍人設）, 夫妻宮空宮+右弼
{
  "birth_year": 1997, "birth_month": 5, "birth_day": 1,
  "birth_time": "12:00", "gender": "F"
}
```

#### `/compute-match` 請求體

**配對組 1：1995-03-26 ✗ 1997-03-07**
**驗證結果：lust=71.6, soul=95.4, soulmate 象限, spiciness=HIGH_VOLTAGE, one_way_hua_ji**

```json
{
  "user_a": {
    "data_tier": 1,
    "birth_year": 1995, "birth_month": 3, "birth_day": 26,
    "birth_time": "14:30", "gender": "M",
    "sun_sign": "aries",    "moon_sign": "aquarius",
    "mercury_sign": "aries", "venus_sign": "aries",
    "mars_sign": "leo",     "jupiter_sign": "sagittarius",
    "saturn_sign": "pisces", "pluto_sign": "scorpio",
    "chiron_sign": null,    "juno_sign": null,
    "ascendant_sign": "leo",
    "house4_sign": "scorpio", "house8_sign": "pisces",
    "bazi_element": "fire",
    "attachment_style": "secure",
    "rpv_conflict": "argue", "rpv_power": "control", "rpv_energy": "out"
  },
  "user_b": {
    "data_tier": 1,
    "birth_year": 1997, "birth_month": 3, "birth_day": 7,
    "birth_time": "10:59", "gender": "M",
    "sun_sign": "pisces",    "moon_sign": "aquarius",
    "mercury_sign": "aquarius", "venus_sign": "aries",
    "mars_sign": "capricorn", "jupiter_sign": "aquarius",
    "saturn_sign": "aries",  "pluto_sign": "sagittarius",
    "chiron_sign": null,     "juno_sign": null,
    "ascendant_sign": "gemini",
    "house4_sign": "virgo",  "house8_sign": "capricorn",
    "bazi_element": "earth",
    "attachment_style": "secure",
    "rpv_conflict": "cold_war", "rpv_power": "follow", "rpv_energy": "out"
  }
}
```

---

**配對組 2：1996-11-07 ✗ 1997-06-07（完整驗證版）**
**驗證結果：lust=94.5, soul=99.0, soulmate 象限, spiciness=MEDIUM, B defense=silent_rumination**

```json
{
  "user_a": {
    "data_tier": 1,
    "birth_year": 1996, "birth_month": 11, "birth_day": 7,
    "birth_time": "19:05", "gender": "M",
    "sun_sign": "scorpio",   "moon_sign": "libra",
    "mercury_sign": "scorpio", "venus_sign": "libra",
    "mars_sign": "virgo",    "jupiter_sign": "capricorn",
    "saturn_sign": "aries",  "pluto_sign": "sagittarius",
    "chiron_sign": null,     "juno_sign": null,
    "ascendant_sign": "gemini",
    "house4_sign": "virgo",  "house8_sign": "capricorn",
    "bazi_element": "earth",
    "attachment_style": "secure",
    "rpv_conflict": "cold_war", "rpv_power": "control", "rpv_energy": "out"
  },
  "user_b": {
    "data_tier": 1,
    "birth_year": 1997, "birth_month": 6, "birth_day": 7,
    "birth_time": "06:00", "gender": "F",
    "sun_sign": "gemini",    "moon_sign": "cancer",
    "mercury_sign": "taurus", "venus_sign": "cancer",
    "mars_sign": "virgo",    "jupiter_sign": "aquarius",
    "saturn_sign": "aries",  "pluto_sign": "sagittarius",
    "chiron_sign": null,     "juno_sign": null,
    "ascendant_sign": "gemini",
    "house4_sign": "virgo",  "house8_sign": "capricorn",
    "bazi_element": "metal",
    "attachment_style": "anxious",
    "rpv_conflict": "cold_war", "rpv_power": "follow", "rpv_energy": "out"
  }
}
```

---

**配對組 3：1997-03-08 ✗ 1997-05-01**
**驗證結果：lust=85.7, soul=75.8, soulmate 象限, spiciness=STABLE, 八字土剋水（A制B）**

```json
{
  "user_a": {
    "data_tier": 1,
    "birth_year": 1997, "birth_month": 3, "birth_day": 8,
    "birth_time": "20:00", "gender": "M",
    "sun_sign": "pisces",   "moon_sign": "pisces",
    "mercury_sign": "pisces", "venus_sign": "pisces",
    "mars_sign": "libra",   "jupiter_sign": "aquarius",
    "saturn_sign": "aries", "pluto_sign": "sagittarius",
    "chiron_sign": null,    "juno_sign": null,
    "ascendant_sign": "libra",
    "house4_sign": "capricorn", "house8_sign": "taurus",
    "bazi_element": "earth",
    "attachment_style": "anxious",
    "rpv_conflict": "cold_war", "rpv_power": "follow", "rpv_energy": "out"
  },
  "user_b": {
    "data_tier": 1,
    "birth_year": 1997, "birth_month": 5, "birth_day": 1,
    "birth_time": "12:00", "gender": "F",
    "sun_sign": "taurus",   "moon_sign": "aquarius",
    "mercury_sign": "taurus", "venus_sign": "taurus",
    "mars_sign": "virgo",   "jupiter_sign": "aquarius",
    "saturn_sign": "aries", "pluto_sign": "sagittarius",
    "chiron_sign": null,    "juno_sign": null,
    "ascendant_sign": "leo",
    "house4_sign": "scorpio", "house8_sign": "pisces",
    "bazi_element": "water",
    "attachment_style": "secure",
    "rpv_conflict": "cold_war", "rpv_power": "control", "rpv_energy": "out"
  }
}
```

> **欄位說明：**
> - `data_tier`: 1=精確時間, 2=模糊時段, 3=僅日期（Tier 3 跳過 ZWDS）
> - `gender`: `"M"` / `"F"`（用於 ZWDS 命盤計算）
> - `birth_time`: Tier 1 填 `"HH:mm"`；Tier 2 填 `"fuzzy_period"`；Tier 3 填 `"unknown"`
> - `attachment_style`: `"secure"` / `"anxious"` / `"avoidant"`
> - `rpv_conflict`: `"argue"` / `"cold_war"`
> - `rpv_power`: `"control"` / `"follow"`
> - `rpv_energy`: `"out"` / `"home"`
> - `chiron_sign` / `juno_sign`: 目前 Swiss Ephemeris 回傳 null，填 null 即可

---

### 八字驗證案例

| 鐘錶時間 | 出生地 | 真太陽時 | 四柱 | 日主 |
|----------|--------|---------|------|------|
| 1997-03-07 10:59 | 台北 | ~10:53 | 丁丑 癸卯 戊申 丁巳 | 戊土(陽) |

> **真太陽時計算：**
> `solar_time = clock_time + (經度 - 120°) × 4分鐘 + 均時差(EoT)`
> 台北 121.565°E → 經度修正 +6.26 分鐘，三月初 EoT ≈ -12 分鐘

### 八字 Data Tier 行為

| Tier | accuracy_type | 時柱 | 說明 |
|------|--------------|------|------|
| Tier 1 | `PRECISE` | 完整四柱 | 有年月日時全部 |
| Tier 2 | `TWO_HOUR_SLOT` / `FUZZY_DAY` (period) | 近似時柱 | morning=9:00, afternoon=14:00, evening=20:00 |
| Tier 3 | `FUZZY_DAY` (unknown) | 無時柱 | hour = null |

---

## 重置測試資料

```sql
-- 在 Supabase SQL Editor 執行
-- 刪除特定測試用戶的資料（替換 email）
DELETE FROM rectification_events WHERE user_id = (SELECT id FROM auth.users WHERE email = 'test1@example.com');
DELETE FROM messages WHERE connection_id IN (
  SELECT id FROM connections WHERE user_a_id = (SELECT id FROM auth.users WHERE email = 'test1@example.com')
     OR user_b_id = (SELECT id FROM auth.users WHERE email = 'test1@example.com')
);
DELETE FROM connections WHERE user_a_id = (SELECT id FROM auth.users WHERE email = 'test1@example.com')
  OR user_b_id = (SELECT id FROM auth.users WHERE email = 'test1@example.com');
DELETE FROM daily_matches WHERE user_id = (SELECT id FROM auth.users WHERE email = 'test1@example.com');
DELETE FROM photos WHERE user_id = (SELECT id FROM auth.users WHERE email = 'test1@example.com');
DELETE FROM users WHERE email = 'test1@example.com';

-- 或只重置 onboarding_step
UPDATE users SET onboarding_step = 'birth_data' WHERE email = 'test1@example.com';
```

---

## Supabase Dashboard 驗證

1. 前往 https://supabase.com/dashboard/project/masninqgihbazjirweiy
2. **Authentication → Users** — 確認用戶已註冊
3. **Table Editor → users** — 確認各欄位已寫入（含 ZWDS 欄位，Migration 008）
4. **Table Editor → rectification_events** — 確認 range_initialized 事件記錄
5. **Table Editor → daily_matches** — 確認配對記錄
6. **Table Editor → connections** — 確認 mutual accept 後自動建立
7. **Table Editor → messages** — 確認聊天訊息
8. **Storage → photos** — 確認圖片檔案（original + blurred）

---

## Summary

| 我想測什麼？ | 用哪層？ |
|-------------|---------|
| 排盤正確性（西洋/八字/紫微）| Layer 0: `curl` + Sandbox Phase 0-A |
| 配對演算法 MATCH/MISMATCH | Layer 0: Sandbox Tab A |
| API 邏輯是否正確（快速） | Layer 1: `npm test` (91 tests) |
| 紫微斗數引擎正確性 | Astro Service: `pytest test_zwds.py` (31 tests) |
| 星盤/八字計算正確性 | Astro Service: `pytest test_chart.py` (30 tests) |
| 配對演算法正確性 | Astro Service: `pytest test_matching.py` (71 tests) |
| 完整用戶流程（註冊到聊天）| Layer 2: 瀏覽器 E2E |
| 單一 API response 格式 | Layer 3: 瀏覽器 Console fetch |
| DB 是否正確寫入（含 ZWDS）| Supabase Dashboard |
| Error handling (401/400/403) | Layer 1 (mock) 或 Layer 3 (real) |
| 出生時間校正流程 | Layer 3: rectification endpoints |
| Realtime 即時訊息 | Layer 2: 兩個瀏覽器視窗互傳 |
