# DESTINY — Testing Guide

**Last Updated:** 2026-02-20 (Phase C ✅ Phase D ✅ Phase B.5 ✅ — 82 JS + 71 Python tests)

---

## 三層測試策略

| Layer | 工具 | 用途 | 需要真實 Supabase? |
|-------|------|------|-------------------|
| **Layer 1: Unit Tests** | Vitest + mocks | 測試 API 邏輯、驗證、錯誤處理 | No (全 mock) |
| **Layer 2: Manual E2E** | 瀏覽器 + dev server | 完整流程測試 (註冊 → onboarding → daily → chat) | **Yes** |
| **Layer 3: API Testing** | 瀏覽器 Console fetch | 直接打 API endpoint 驗證 response | **Yes** |

---

## Layer 1: Unit Tests (Mock — 不需真實 DB)

現有 **82 JS unit tests**（13 個測試檔），全部使用 mock Supabase client。

### 執行方式

```bash
cd destiny-app

# 執行全部測試 (一次性)
npm test

# Watch mode (修改檔案自動重跑)
npm run test:watch

# 只跑特定測試檔
npx vitest run src/__tests__/api/onboarding-birth-data.test.ts

# 跑特定 describe/it (用 -t flag)
npx vitest run -t "saves birth data"
```

### 現有測試清單

```
src/__tests__/
├── auth.test.ts                                   # 10 tests — register/login/logout 邏輯
├── login-page.test.tsx                            # 4 tests  — Login 頁面互動
├── register-page.test.tsx                         # 5 tests  — Register 頁面互動
└── api/
    ├── onboarding-birth-data.test.ts              # 12 tests — data_tier + accuracy_type + confidence + event log
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
| Onboarding birth-data | 12 | data_tier 1/2/3、evening、PRECISE/TWO_HOUR_SLOT/FUZZY_DAY accuracy_type、initial confidence、range_initialized event、401/400 |
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
  - **卡片 B「我知道大概時段」** → 出現 12 格 2hr grid，點選一格（如 13:00-15:00）
  - **卡片 C「我只知道大概」** → 出現 早上/下午/晚上 3 個選項
  - **卡片 D「我完全不知道」** → 直接可點 Continue
- [ ] 填寫出生日期 + 出生城市
- [ ] 點擊 Continue
- [ ] 預期: 導向 `/onboarding/rpv-test`
- [ ] 驗證 Supabase `users` 表：
  - `birth_date`, `birth_city` 已寫入
  - `accuracy_type` = `PRECISE` / `TWO_HOUR_SLOT` / `FUZZY_DAY`
  - `current_confidence` = 0.90 / 0.30 / 0.15 / 0.05
  - `rectification_status` = `collecting_signals`
  - `window_start`, `window_end`, `window_size_minutes` 有值
- [ ] 驗證 `rectification_events` 表：有一筆 `event_type = range_initialized` 記錄
- [ ] 驗證: 若 astro-service 運行中 → `sun_sign`, `bazi_day_master` 應有值

---

#### Step 2: RPV Test (作業系統)
- [ ] 3 題都選擇一個選項
- [ ] 觀察 progress bar 填滿
- [ ] 點擊 Continue → 預期導向 `/onboarding/photos`
- [ ] 驗證: users 表 → `rpv_conflict`, `rpv_power`, `rpv_energy` 已寫入，`onboarding_step = photos`

---

#### Step 3: Photos (視覺門檻)
- [ ] 點擊 Photo 1 框 → 選擇一張圖片
- [ ] 點擊 Photo 2 框 → 選擇另一張圖片
- [ ] 兩張都選完後，點擊 Continue → 預期導向 `/onboarding/soul-report`
- [ ] 驗證:
  - Supabase Storage → photos bucket → `{user_id}/original_1.jpg`, `blurred_1.jpg` 等
  - `photos` 表 → 2 筆記錄

---

#### Step 4: Soul Report (靈魂原型)
- [ ] 頁面載入後應顯示動態原型（非 hardcoded）
- [ ] 觀察原型名稱、描述、tags、base stats 有內容
- [ ] 點擊「Enter DESTINY」→ 預期導向 `/daily`
- [ ] 驗證: users 表 → `archetype_name`, `onboarding_step = complete`

---

#### Step 5: Daily Feed (配對卡)
- [ ] 開啟 http://localhost:3000/daily
- [ ] 預期顯示 3 張配對卡（或 empty state 若無 seed 資料）
- [ ] 各卡顯示：archetype、tags、radar bars、模糊頭像
- [ ] 點擊 Accept → 按鈕變綠色
- [ ] 點擊 Pass → 卡片消失
- [ ] 若兩個用戶互 Accept → 自動建立 connection

> **測試 mutual accept 的方式：** 用兩個不同帳號，跑 `POST /api/matches/run` 生成配對，再雙方都 Accept。

---

#### Step 6: Connections (連結列表)
- [ ] 開啟 http://localhost:3000/connections
- [ ] 預期顯示所有 active connections（有 mutual accept 的）
- [ ] 各卡顯示：tags、sync_level 進度條、last_activity 時間、模糊頭像
- [ ] 無 connection 時顯示 empty state
- [ ] 點擊卡片 → 進入聊天室

---

#### Step 7: Chat (聊天室)
- [ ] 進入 `/connections/[id]`
- [ ] 載入時顯示 connection 資訊 + 歷史訊息
- [ ] 輸入訊息 → Enter 或點送出按鈕
- [ ] **樂觀更新**：訊息立即出現（不需等 API）
- [ ] 對方在另一個瀏覽器傳訊息 → **Supabase Realtime** 應即時出現（不需重新整理）
- [ ] Lv.1 時顯示模糊照片 + 鎖定提示「Unlocks at Lv.2」
- [ ] 訊息數達 10 條 → sync_level 應升至 2

---

### 常見問題排除

| 問題 | 原因 | 解法 |
|------|------|------|
| Register 後沒有自動跳轉 | Email confirmation 開啟 | Dashboard → Auth Settings → 關閉 email confirm |
| Continue 按鈕沒反應 | 表單驗證未通過 | 檢查必填欄位是否都有填 |
| 401 錯誤 | Cookie 沒有正確設定 | 清除 cookies，重新登入 |
| Photos 上傳失敗 | Storage bucket 權限 | 確認 RLS policy 允許 authenticated users 上傳 |
| Daily 空白 | 無配對資料 | 執行 `POST /api/matches/run` seed 資料（需 CRON_SECRET） |
| Realtime 不更新 | Supabase Realtime 未啟用 | Dashboard → Database → Replication → 確認 messages table 已開啟 |
| rectification_events 沒有資料 | Migration 006 未套用 | 確認已執行 `supabase db push` |

---

## Layer 3: API Testing (瀏覽器 Console)

先登入 http://localhost:3000/login，然後在 DevTools Console 執行：

### Onboarding

```javascript
// ---- Birth Data: 新格式 (accuracy_type) ----
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
// 預期: { data: { accuracy_type: 'PRECISE', current_confidence: 0.9, rectification_status: 'collecting_signals', ... } }

// ---- Birth Data: TWO_HOUR_SLOT ----
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
// 預期: { data: { accuracy_type: 'TWO_HOUR_SLOT', current_confidence: 0.30, window_size_minutes: 120, ... } }

// ---- RPV Test ----
await fetch('/api/onboarding/rpv-test', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ rpv_conflict: 'cold_war', rpv_power: 'control', rpv_energy: 'home' }),
}).then(r => r.json()).then(console.log)
```

### Daily Matches

```javascript
// ---- 取得今日配對卡 ----
await fetch('/api/matches/daily').then(r => r.json()).then(console.log)
// 預期: { matches: [{ id, archetype_name, tags, interest_tags, radar_passion, ... }] }

// ---- Accept 一張配對卡 (替換 matchId) ----
await fetch('/api/matches/MATCH_ID_HERE', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ action: 'accept' }),
}).then(r => r.json()).then(console.log)
// 預期: { match: { user_action: 'accept' }, connection: null }  (或 { connection: { id: ... } } 若對方也 accept)
```

### Connections + Chat

```javascript
// ---- 列出所有 connections ----
await fetch('/api/connections').then(r => r.json()).then(console.log)
// 預期: { connections: [{ id, sync_level, message_count, last_activity, tags, other_user, blurred_photo_url }] }

// ---- 取得聊天室訊息 (替換 connId) ----
await fetch('/api/connections/CONN_ID_HERE/messages').then(r => r.json()).then(console.log)
// 預期: { connection: { sync_level, message_count, ... }, messages: [{ id, content, is_self, ... }] }

// ---- 發送訊息 ----
await fetch('/api/connections/CONN_ID_HERE/messages', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ content: 'Hello!' }),
}).then(r => r.json()).then(console.log)
// 預期: 201 { message: { id, sender_id, content, created_at } }
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
// 預期: { rectification_status, current_confidence, tier_upgraded, next_question_available }
```

### Error Cases

```javascript
// ---- 缺少欄位 (400) ----
await fetch('/api/onboarding/birth-data', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ birth_date: '1995-06-15' }), // 缺少 accuracy_type 和 birth_city
}).then(r => console.log(r.status, r.json()))
// 預期: 400 { error: 'Missing required fields: ...' }
```

---

## Astro Service 測試

### 啟動服務

```bash
cd astro-service
pip install -r requirements.txt    # 首次安裝
uvicorn main:app --port 8001       # 啟動
```

### Python Unit Tests (71 tests)

```bash
cd astro-service

# 星盤 + 八字 + 五行關係 (30 tests)
pytest test_chart.py -v

# 配對演算法 (41 tests)
pytest test_matching.py -v

# 全部一起跑
pytest -v
```

**test_chart.py 測試分類：**

| 類別 | 測試項目 | 數量 |
|------|---------|------|
| 西洋占星 | Sun sign 12 星座、Tier 1/2/3 行為、邊界日期 | 12 |
| 八字四柱 | 日主、四柱結構、年柱/日柱驗證、Tier 行為 | 11 |
| 五行關係 | 相生/相剋/比和 全循環 | 7 |

**test_matching.py 測試分類：**

| 類別 | 測試項目 | 數量 |
|------|---------|------|
| 星座相位 (sign_aspect) | 合/刑/沖/拱/六合 + edge cases | 9 |
| Kernel 相容性 | 日主相生相剋 + RPV 組合 | 6 |
| Power Dynamic Fit | 互補/同類 組合 | 4 |
| Glitch Tolerance | Mars/Saturn 張力 | 3 |
| Match 分類 | complementary/similar/tension | 6 |
| Chameleon Tags | 動態標籤生成 | 5 |
| Integration | compute_match end-to-end | 8 |

### API 測試

```bash
# 健康檢查
curl http://localhost:8001/health

# 西洋占星 + 八字 (Tier 1: 精確時間)
curl -X POST http://localhost:8001/calculate-chart \
  -H "Content-Type: application/json" \
  -d '{"birth_date":"1997-03-07","birth_time":"precise","birth_time_exact":"10:59","lat":25.033,"lng":121.565,"data_tier":1}'
# 預期: sun_sign, moon_sign, ascendant_sign + bazi.four_pillars: 丁丑 癸卯 戊申 丁巳

# 五行關係分析
curl -X POST http://localhost:8001/analyze-relation \
  -H "Content-Type: application/json" \
  -d '{"element_a":"wood","element_b":"fire"}'
# 預期: { relation: "a_generates_b", harmony_score: 0.85 }

# 配對分數計算 (替換為真實 user_id)
curl -X POST http://localhost:8001/compute-match \
  -H "Content-Type: application/json" \
  -d '{"user_a": {...}, "user_b": {...}}'
```

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
-- 刪除特定測試用戶的資料 (替換 email)
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
3. **Table Editor → users** — 確認各欄位已寫入（含新 accuracy_type / current_confidence 欄位）
4. **Table Editor → rectification_events** — 確認 range_initialized 事件記錄
5. **Table Editor → daily_matches** — 確認配對記錄
6. **Table Editor → connections** — 確認 mutual accept 後自動建立
7. **Table Editor → messages** — 確認聊天訊息
8. **Storage → photos** — 確認圖片檔案 (original + blurred)

---

## Summary

| 我想測什麼？ | 用哪層？ |
|-------------|---------|
| API 邏輯是否正確 (快速) | Layer 1: `npm test` (82 tests) |
| 星盤/八字計算正確性 | Astro Service: `pytest test_chart.py` (30 tests) |
| 配對演算法正確性 | Astro Service: `pytest test_matching.py` (41 tests) |
| 完整用戶流程 (註冊到聊天) | Layer 2: 瀏覽器 E2E |
| 單一 API response 格式 | Layer 3: 瀏覽器 Console fetch |
| DB 是否正確寫入 | Supabase Dashboard |
| Error handling (401/400/403) | Layer 1 (mock) 或 Layer 3 (real) |
| 出生時間校正流程 | Layer 3: rectification endpoints |
| Realtime 即時訊息 | Layer 2: 兩個瀏覽器視窗互傳 |
