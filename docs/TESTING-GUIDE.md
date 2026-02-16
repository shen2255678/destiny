# DESTINY — Testing Guide

**Last Updated:** 2026-02-16

---

## 三層測試策略

| Layer | 工具 | 用途 | 需要真實 Supabase? |
|-------|------|------|-------------------|
| **Layer 1: Unit Tests** | Vitest + mocks | 測試 API 邏輯、驗證、錯誤處理 | No (全 mock) |
| **Layer 2: Manual E2E** | 瀏覽器 + dev server | 完整流程測試 (註冊 → onboarding → daily) | **Yes** |
| **Layer 3: API Testing** | curl / Postman / Thunder Client | 直接打 API endpoint 驗證 response | **Yes** |

---

## Layer 1: Unit Tests (Mock — 不需真實 DB)

已有 35 個 unit tests，全部使用 mock Supabase client。

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
├── auth.test.ts                          # 10 tests — register/login/logout 邏輯
├── login-page.test.tsx                   # 4 tests  — Login 頁面互動
├── register-page.test.tsx                # 5 tests  — Register 頁面互動
└── api/
    ├── onboarding-birth-data.test.ts     # 5 tests  — data_tier 計算 + 驗證
    ├── onboarding-rpv-test.test.ts       # 3 tests  — RPV 儲存 + 驗證
    ├── onboarding-photos.test.ts         # 3 tests  — 照片上傳 + blur
    └── onboarding-soul-report.test.ts    # 3 tests  — 原型生成 + onboarding complete
```

### 測試了什麼？

| Test | 驗證項目 |
|------|---------|
| Happy path | 正確輸入 → 200 + 正確 DB 操作 |
| 401 Unauthorized | 未登入 → 拒絕 |
| 400 Bad Request | 缺少必要欄位 → 拒絕 |
| Data tier | unknown→3, morning→2, precise→1 |
| RPV mapping | option ID → DB value 對應正確 |

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

### 測試流程 Checklist

#### Step 0: 註冊帳號
- [ ] 開啟 http://localhost:3000/register
- [ ] 輸入 email + password (≥8 字元)
- [ ] 點擊 Register
- [ ] 預期: 自動導向 `/onboarding/birth-data`
- [ ] 驗證: Supabase Dashboard → Authentication → Users 應該看到新用戶

> **Tips:**
> - 可以用假 email 如 `test1@example.com`（Supabase 預設不驗證 email）
> - 如果 Supabase 有開啟 email confirmation，需到 Dashboard → Authentication → Settings → 關閉 "Enable email confirmations"

#### Step 1: Birth Data (硬體規格)
- [ ] 填寫出生日期 (任意過去日期)
- [ ] 選擇時間精確度 (建議先選「精確時間」測 Gold Tier)
- [ ] 如選精確時間，填入時間 (如 14:30)
- [ ] 填寫出生地點 (如「台北市」)
- [ ] 觀察 Data Tier 指示器是否正確顯示 Gold/Silver/Bronze
- [ ] 點擊 Continue
- [ ] 預期: 導向 `/onboarding/rpv-test`
- [ ] 驗證: Supabase Dashboard → Table Editor → users → 確認 birth_date, birth_time, data_tier 已寫入

#### Step 2: RPV Test (作業系統)
- [ ] 3 題都選擇一個選項
- [ ] 觀察 progress bar 填滿
- [ ] 點擊 Continue
- [ ] 預期: 導向 `/onboarding/photos`
- [ ] 驗證: users 表 → rpv_conflict, rpv_power, rpv_energy 已寫入，onboarding_step = 'photos'

#### Step 3: Photos (視覺門檻)
- [ ] 點擊 Photo 1 框 → 選擇一張圖片
- [ ] 點擊 Photo 2 框 → 選擇另一張圖片
- [ ] 兩張都選完後，點擊 Continue
- [ ] 預期: 導向 `/onboarding/soul-report`
- [ ] 驗證:
  - Supabase Dashboard → Storage → photos bucket → 應有 `{user_id}/` 資料夾
  - 裡面有: `original_1.jpg`, `original_2.jpg`, `blurred_1.jpg`, `blurred_2.jpg`
  - Table Editor → photos 表 → 應有 2 筆記錄

#### Step 4: Soul Report (靈魂原型)
- [ ] 頁面載入後應顯示動態原型 (非 hardcoded "The Wanderer")
- [ ] 觀察原型名稱、描述、tags、base stats 是否有內容
- [ ] Stats bars 應該有動畫填充
- [ ] 點擊 "Enter DESTINY"
- [ ] 預期: 導向 `/daily`
- [ ] 驗證: users 表 → archetype_name, archetype_desc 已寫入，onboarding_step = 'complete'

### 常見問題排除

| 問題 | 原因 | 解法 |
|------|------|------|
| Register 後沒有自動跳轉 | Email confirmation 開啟 | Dashboard → Auth Settings → 關閉 email confirm |
| Continue 按鈕沒反應 | 表單驗證未通過 | 檢查必填欄位是否都有填 |
| 401 錯誤 | Cookie 沒有正確設定 | 清除 cookies，重新登入 |
| Photos 上傳失敗 | Storage bucket 權限 | 確認 RLS policy 允許 authenticated users 上傳 |
| Soul Report 載入失敗 | users 表缺少資料 | 確認前 3 步都有正確寫入 |

---

## Layer 3: API Testing (curl / Postman)

直接測試 API endpoints，不經過前端頁面。

### 取得 Auth Token

首先需要登入取得 session cookie。有兩種方式：

#### 方式 A: 從瀏覽器取得 (最簡單)

1. 在瀏覽器登入 http://localhost:3000/login
2. 開 DevTools → Application → Cookies
3. 找到 `sb-masninqgihbazjirweiy-auth-token` 相關 cookies
4. 複製 cookie 值用於 curl

#### 方式 B: 用 Supabase API 直接登入

```bash
# 取得 access token
curl -X POST "https://masninqgihbazjirweiy.supabase.co/auth/v1/token?grant_type=password" \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test1@example.com","password":"yourpassword"}'

# Response 會包含 access_token
```

### 測試各 Endpoint

> **Note:** 以下 curl 範例直接打 localhost:3000。
> 由於 Next.js API routes 從 cookie 讀取 auth，
> 最簡單的方式是在瀏覽器登入後，用瀏覽器 console 的 `fetch()` 來測試。

#### 在瀏覽器 Console 測試 (推薦)

先登入 http://localhost:3000/login，然後在 DevTools Console 執行：

```javascript
// ---- Test: Birth Data ----
await fetch('/api/onboarding/birth-data', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    birth_date: '1995-06-15',
    birth_time: 'precise',
    birth_time_exact: '14:30',
    birth_city: '台北市',
  }),
}).then(r => r.json()).then(console.log)

// 預期: { data: { id: '...', birth_date: '1995-06-15', data_tier: 1, ... } }
```

```javascript
// ---- Test: RPV Test ----
await fetch('/api/onboarding/rpv-test', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    rpv_conflict: 'cold_war',
    rpv_power: 'control',
    rpv_energy: 'home',
  }),
}).then(r => r.json()).then(console.log)

// 預期: { data: { rpv_conflict: 'cold_war', onboarding_step: 'photos', ... } }
```

```javascript
// ---- Test: Soul Report ----
await fetch('/api/onboarding/soul-report')
  .then(r => r.json()).then(console.log)

// 預期: { data: { archetype_name: 'The Sentinel', tags: [...], stats: [...] } }
```

```javascript
// ---- Test: Photos (需要用 FormData) ----
const form = new FormData()
// 建立假圖片 blob
const fakeImg = new Blob(['fake'], { type: 'image/jpeg' })
form.append('photo1', fakeImg, 'photo1.jpg')
form.append('photo2', fakeImg, 'photo2.jpg')

await fetch('/api/onboarding/photos', {
  method: 'POST',
  body: form,
}).then(r => r.json()).then(console.log)

// 預期: { data: [{ user_id: '...', slot: 1, ... }, { ... slot: 2 }] }
// ⚠️ 注意: fake blob 可能讓 sharp 報錯，建議用真實圖片測試
```

#### 驗證 Error Cases

```javascript
// ---- 未登入 (先登出) ----
// 預期: { error: 'Not authenticated' }, status 401

// ---- 缺少欄位 ----
await fetch('/api/onboarding/birth-data', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ birth_date: '1995-06-15' }), // 缺少 birth_time, birth_city
}).then(r => console.log(r.status, await r.json()))

// 預期: 400 { error: 'Missing required fields: birth_date, birth_time, birth_city' }
```

---

## Supabase Dashboard 驗證

每步完成後，可在 Supabase Dashboard 直接確認資料：

1. 前往 https://supabase.com/dashboard/project/masninqgihbazjirweiy
2. **Authentication → Users** — 確認用戶已註冊
3. **Table Editor → users** — 確認各欄位已寫入
4. **Table Editor → photos** — 確認照片記錄
5. **Storage → photos** — 確認圖片檔案 (original + blurred)

---

## 重置測試資料

如果需要重新測試完整流程：

```sql
-- 在 Supabase SQL Editor 執行
-- 刪除特定測試用戶的資料 (替換 email)
DELETE FROM photos WHERE user_id = (SELECT id FROM auth.users WHERE email = 'test1@example.com');
DELETE FROM users WHERE email = 'test1@example.com';

-- 或重置 onboarding_step 讓用戶重走流程
UPDATE users SET onboarding_step = 'birth_data' WHERE email = 'test1@example.com';
```

也可以在 Supabase Dashboard → Authentication → Users → 刪除測試用戶，重新註冊。

---

## Astro Service 測試

### 啟動服務

```bash
cd astro-service
pip install -r requirements.txt    # 首次安裝
uvicorn main:app --port 8001       # 啟動
```

### Python Unit Tests (30 tests)

```bash
cd astro-service
pytest test_chart.py -v
```

測試涵蓋：

| 類別 | 測試項目 | 數量 |
|------|---------|------|
| 西洋占星 | Sun sign 12 星座、Tier 1/2/3 行為、邊界日期 | 12 |
| 八字四柱 | 日主、四柱結構、年柱/日柱驗證、Tier 行為 | 16 |
| 五行關係 | 相生/相剋/比和 全循環 | 7 |

### API 測試

```bash
# 健康檢查
curl http://localhost:8001/health

# 西洋占星 + 八字 (Tier 1: 精確時間)
curl -X POST http://localhost:8001/calculate-chart \
  -H "Content-Type: application/json" \
  -d '{"birth_date":"1997-03-07","birth_time":"precise","birth_time_exact":"10:59","lat":25.033,"lng":121.565,"data_tier":1}'

# 預期結果包含：
# sun_sign, moon_sign, venus_sign, mars_sign, saturn_sign, ascendant_sign
# bazi.four_pillars: 丁丑 癸卯 戊申 丁巳
# bazi.day_master: 戊 (earth)

# Tier 3: 僅日期
curl -X POST http://localhost:8001/calculate-chart \
  -H "Content-Type: application/json" \
  -d '{"birth_date":"1995-06-15","data_tier":3}'

# 五行關係分析
curl -X POST http://localhost:8001/analyze-relation \
  -H "Content-Type: application/json" \
  -d '{"element_a":"wood","element_b":"fire"}'
# 預期: relation=a_generates_b, harmony_score=0.85
```

### 八字驗證案例

| 鐘錶時間 | 出生地 | 真太陽時 | 四柱 | 日主 |
|----------|--------|---------|------|------|
| 1997-03-07 10:59 | 台北 | ~10:53 | 丁丑 癸卯 戊申 丁巳 | 戊土(陽) |

> **真太陽時計算：**
> `solar_time = clock_time + (經度 - 120°) × 4分鐘 + 均時差(EoT)`
> 台北 121.565°E → 經度修正 +6.26 分鐘，三月初 EoT ≈ -12 分鐘

### 八字 Data Tier 行為

| Tier | 時柱 | 說明 |
|------|------|------|
| Tier 1 (精確時間) | 完整四柱 | 有年月日時全部 |
| Tier 2 (模糊時間) | 近似時柱 | morning=9:00, afternoon=14:00, evening=20:00 |
| Tier 3 (僅日期) | 無時柱 | hour = null |

---

## Onboarding + 星盤整合測試

完成 birth-data 步驟後，API 會自動呼叫 astro-service 計算星盤和八字。

### 驗證流程

1. 確認 astro-service 在 `localhost:8001` 運行中
2. 走完 `/onboarding/birth-data` 步驟
3. 在 Supabase Dashboard → Table Editor → users 確認以下欄位已寫入：

| 欄位 | 說明 | 範例值 |
|------|------|--------|
| sun_sign | 太陽星座 | gemini |
| moon_sign | 月亮星座 (Tier 2+) | cancer |
| venus_sign | 金星星座 | taurus |
| mars_sign | 火星星座 | leo |
| saturn_sign | 土星星座 | pisces |
| ascendant_sign | 上升星座 (Tier 1 only) | virgo |
| element_primary | 主要元素 | air |
| bazi_day_master | 日主天干 | 戊 |
| bazi_element | 日主五行 | earth |
| bazi_four_pillars | 四柱完整資料 (JSONB) | {"day_master":"戊", ...} |

> **注意：** 如果 astro-service 未啟動，星盤欄位會保持 null，但 onboarding 流程不受影響（非阻塞式）。

---

## Summary

| 我想測什麼？ | 用哪層？ |
|-------------|---------|
| API 邏輯是否正確 (快速) | Layer 1: `npm test` |
| 星盤/八字計算正確性 | Astro Service: `pytest test_chart.py` |
| 完整用戶流程 (註冊到完成) | Layer 2: 瀏覽器 E2E |
| 單一 API response 格式 | Layer 3: 瀏覽器 Console fetch |
| DB 是否正確寫入 | Supabase Dashboard |
| Error handling (401/400) | Layer 1 (mock) 或 Layer 3 (real) |
| 五行配對分析 | `/analyze-relation` API |
