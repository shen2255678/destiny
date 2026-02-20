# DESTINY MVP — Progress Tracker

**Last Updated:** 2026-02-20 (Phase C ✅ Phase D ✅ Phase B.5 ✅ Phase G ✅)

---

## Frontend Pages

| Route | Page | UI Status | DB 串接 | 備註 |
|-------|------|-----------|---------|------|
| `/` | Landing Page | Done | N/A | 靜態行銷頁，無需 DB |
| `/login` | Login | Done | **Done** | 已串接 Supabase Auth + error handling + loading state |
| `/register` | Register | Done | **Done** | 已串接 Supabase Auth + error handling + loading state |
| `/onboarding` | Redirect | Done | N/A | 自動導向 /onboarding/birth-data |
| `/onboarding/birth-data` | Step 1: 硬體規格 | Done | **Done** | 4-card 精度選擇 UX + 12 格 TWO_HOUR_SLOT grid + FUZZY_DAY 3 選項；已串接 `POST /api/onboarding/birth-data` + accuracy_type + rectification 初始化 |
| `/onboarding/rpv-test` | Step 2: 作業系統 | Done | **Done** | 已串接 `POST /api/onboarding/rpv-test`，option ID → DB value 映射 |
| `/onboarding/photos` | Step 3: 視覺門檻 | Done | **Done** | 已串接 `POST /api/onboarding/photos`，真實檔案上傳 + sharp 高斯模糊 |
| `/onboarding/soul-report` | Step 4: 靈魂原型 | Done | **Done** | 已串接 `GET /api/onboarding/soul-report`，deterministic 原型生成 (待升級 AI) |
| `/daily` | Daily Feed (3 Cards) | Done | **Done** | 已串接 `GET /api/matches/daily` + Accept/Pass 動作，含 loading/empty state |
| `/connections` | Connections List | Done | **Done** | 已串接 `GET /api/connections`，真實資料 + loading/empty state + 模糊照片 |
| `/connections/[id]` | Chat Room | Done | **Done** | 已串接 `GET/POST /api/connections/:id/messages` + Supabase Realtime + 樂觀更新 |
| `/profile` | Self-View Profile + Edit | Done | **Done** | 已串接 `GET/PATCH /api/profile/me` + 編輯模式 + 照片 signed URL + bio + 興趣標籤 |

---

## Backend / API

| Module | Status | Description |
|--------|--------|-------------|
| Supabase 專案建立 | **Done** | 專案已建立 (`masninqgihbazjirweiy`)，Auth provider 已設定 (Email/Password) |
| Database Schema | **Done** | 5 張表已建立 + RLS + triggers + indexes + storage bucket (`001` → `003` migrations) |
| Migration 002 | **Done** | `social_energy` 欄位 (high/medium/low) |
| Migration 003 | **Done** | `bio` (TEXT, 500 字上限) + `interest_tags` (JSONB) 欄位 |
| Migration 006 | **Done** ✅ | Rectification 欄位（accuracy_type, window_start/end, window_size_minutes, rectification_status, current_confidence, active_range, calibrated_time, active_d9_slot, is_boundary_case, dealbreakers, priorities）+ `rectification_events` 新表 + RLS |
| Supabase Client | **Done** | `client.ts` (browser) + `server.ts` (SSR) + `middleware.ts` (session) |
| Auth Middleware | **Done** | `src/middleware.ts` — 自動 redirect 未登入用戶到 /login |
| Auth Functions | **Done** | `src/lib/auth.ts` — register/login/logout/getCurrentUser + email/password 驗證 |
| TypeScript Types | **Done** | `src/lib/supabase/types.ts` — 完整 Database 型別定義 + Relationships（Supabase JS v2.95 相容） |
| Onboarding API (4 endpoints) | **Done** | birth-data, rpv-test, photos, soul-report — 全部已實作 + TDD |
| Image Processing | **Done** | sharp 高斯模糊 + 基本驗證 (MIME type + size limit 10MB) — 詳見 `docs/PHOTO-PIPELINE.md` |
| Archetype Generator | **Done** | `src/lib/ai/archetype.ts` — 8 組 deterministic 原型 (待升級 Claude API) |
| Matches API (Phase C) | **Done** | run + daily + action 端點，含 mutual accept → 建立 connection |
| Python Microservice | **Done** | `astro-service/` — FastAPI + Swiss Ephemeris + BaZi 八字四柱 + 真太陽時，30 pytest 通過。已串接 birth-data API 自動回寫 DB。詳見 `docs/ASTRO-SERVICE.md` |
| Rectification Data Layer | **Done** ✅ | Phase B.5：Migration 006 + types.ts 更新 + birth-data API 接受 accuracy_type/window/fuzzy_period + 初始化 rectification state + log range_initialized event + 4-card 精度 UX + rectification quiz endpoints (next-question + answer) |
| AI/LLM Integration | Not Started | Claude API 串接 (動態原型、變色龍標籤、破冰題) |
| **Matching Algorithm v2 (Phase G)** | **Done ✅** | Lust/Soul 雙軸 + 四軌（friend/passion/partner/soul）+ Power D/s frame + Chiron rule + Attachment 問卷 + Mercury/Jupiter/Pluto/Chiron/Juno/House4/8。Migration 007 + `compute_match_v2` + `/api/onboarding/attachment`。設計文件：`docs/plans/2026-02-20-expanded-matching-algorithm-design.md`，實作計劃：`docs/plans/2026-02-20-phase-g-matching-v2-plan.md` |

---

## Backend API Endpoints

### Auth & Onboarding
- [x] `POST /api/auth/register` — Supabase Auth 註冊 (透過 `src/lib/auth.ts`)
- [x] `POST /api/onboarding/birth-data` — 儲存出生資料 + 計算 data_tier (1/2/3) + 回寫星盤（含 Phase G 新欄位）
- [x] `POST /api/onboarding/rpv-test` — 儲存 RPV 三題測試結果 (conflict/power/energy)
- [x] `POST /api/onboarding/photos` — 上傳 2 張照片 + sharp 高斯模糊 + Supabase Storage
- [x] `GET /api/onboarding/soul-report` — 生成靈魂原型 + base stats + 更新 onboarding_step=complete
- [x] `POST /api/onboarding/attachment` — **(Phase G)** 儲存依附風格（anxious/avoidant/secure）+ 角色（dom_secure/sub_secure/balanced）

### Rectification (Phase B.5 — Done ✅)
- [x] `GET /api/rectification/next-question` — 取得下一道校正問題（依邊界案例優先度排序：Asc/Dsc 換座優先；4 道題庫：月亮崩潰 coarse + 上升排除 fine + 八字社交 coarse + 八字時柱 fine）
- [x] `POST /api/rectification/answer` — 提交回答 → Via Negativa 過濾候選時段 → 更新 current_confidence → 信心值 ≥ 0.8 時自動鎖定 calibrated_time + tier_upgraded

### Daily Destiny
- [x] `GET /api/matches/daily` — 取得今日 3 張配對卡（含 archetype、tags、radar、blurred_photo、interest_tags）
- [x] `POST /api/matches/:id/action` — Accept/Pass 邏輯；雙方都 Accept → 自動建立 connections 記錄
- [x] `POST /api/matches/run` — 每日配對 orchestrator（service role；支援 CRON_SECRET 保護）

### Connections
- [x] `GET /api/connections` — 列出所有非過期 connections（含 sync_level, last_activity, tags, other_user, blurred_photo_url）
- [ ] `POST /api/connections/:id/icebreaker-answer` — 提交破冰答案（Phase D 後續）

### Chat
- [x] `GET /api/connections/:id/messages` — 取得 connection 詳情 + 最近 50 則訊息（含 is_self flag）
- [x] `POST /api/connections/:id/messages` — 發送文字訊息（DB trigger 自動更新 message_count + sync_level）
- [ ] `POST /api/connections/:id/messages/image` — 發送圖片訊息（後續 Phase D+ 實作）

### Profile
- [x] `GET /api/profile/me` — 自我檢視：所有個人資料 + 照片 signed URL + bio + interest_tags
- [x] `PATCH /api/profile/me` — 更新個人資料（display_name, 出生資料, RPV, bio, interest_tags, 自動重算 data_tier）
- [x] `POST /api/profile/me/photos` — 重新上傳照片
- [x] `GET /api/profile/energy` — 取得社交能量狀態
- [x] `PATCH /api/profile/energy` — 更新社交能量狀態 (high/medium/low)

---

## Python Microservice (`astro-service/`)

- [x] `POST /calculate-chart` — 計算星盤 (Swiss Ephemeris) + 八字四柱 (BaZi)，支援 Tier 1/2/3；**(Phase G)** 新增 Mercury/Jupiter/Pluto/Chiron/Juno + House 4/8（Placidus）
- [x] `POST /analyze-relation` — 五行關係分析（相生/相剋/比和 + harmony_score）
- [x] `POST /compute-match` — **(Phase G v2)** 輸出 `lust_score, soul_score, power{rpv/frame_break/viewer_role/target_role}, tracks{friend/passion/partner/soul}, primary_track, quadrant, labels`
- [x] `GET /health` — Health check
- [x] 串接 Next.js API — birth-data 完成後自動呼叫 calculate-chart 回寫 DB（非阻塞式）
- [x] 真太陽時 (True Solar Time) — 經度修正 + 均時差 (Equation of Time)
- [x] Migration 004 — `bazi_day_master`, `bazi_element`, `bazi_four_pillars` 欄位
- [x] Migration 007 — **(Phase G)** `mercury_sign, jupiter_sign, pluto_sign, chiron_sign, juno_sign, house4_sign, house8_sign, attachment_role`
- [x] Windows Unicode path fix — `_resolve_ephe_path()` 自動複製星曆檔到 ASCII temp 路徑（pyswisseph C 庫不支援 Unicode）
- [ ] `POST /run-daily-matching` — 每日 21:00 Cron Job，生成配對

---

## Core Features 實作進度

| Feature | Status | Notes |
|---------|--------|-------|
| User Registration | **Done** | Supabase Auth Email/Password + 前端驗證 |
| User Login | **Done** | Supabase Auth + error/loading UI |
| Auth Middleware | **Done** | 自動保護路由，未登入 → /login |
| Birth Data Collection | **Done** | API + 前端串接，data_tier 自動計算 |
| RPV Test (3 Questions) | **Done** | API + 前端串接，option ID → DB value 映射 |
| Photo Upload + Blur | **Done** | 真實檔案上傳 + sharp 高斯模糊 + Supabase Storage |
| Soul Report / Archetype | **Done** | Deterministic 原型生成 (8 組)，待升級 Claude API |
| Daily Match Cards | **Done** | GET /api/matches/daily 串接，真實 API 資料 + loading/empty state |
| Dual Blind Selection (Accept/Pass) | **Done** | POST /api/matches/[id]/action；雙方 Accept → 自動建立 connection |
| Chameleon Tags | UI Mock Only | 需 AI API 動態生成 |
| Radar Chart (激情/穩定/溝通) | UI Done (bars), Data Pending | 由 matching algorithm 計算 |
| Progressive Unlock (Lv.1→2→3) | UI Shown, Logic Pending | 需 DB trigger / API logic |
| Chat (Text) | **Done** | Supabase Realtime + 樂觀更新 + is_self flag |
| Chat (Image) | Not Started | 圖片上傳至 Storage + message_type 欄位 |
| 24hr Auto-Disconnect | Not Started | 需 DB cron/trigger |
| Ice-breaker (Simplified) | Not Started | UI + AI API |
| Self-View Profile + Edit | **Done** | GET/PATCH API + 編輯模式 + 照片重傳 + signed URL 顯示 |
| Profile Bio | **Done** | 自我介紹編輯，500 字上限，即時字數顯示 |
| Interest Tags | **Done** | 30 個預設標籤（6 類），多選上限 10 個，pill UI |
| Social Energy Bar | **Done** | 一鍵切換 High/Medium/Low，存入 DB |
| Responsive Layout | **Done** | 全站響應式：Profile / Connections / Daily / Onboarding |

---

## Test Coverage

| Test File | Tests | Description |
|-----------|-------|-------------|
| `src/__tests__/auth.test.ts` | 10 | Auth 邏輯層 (register/login/logout/getCurrentUser + validation) |
| `src/__tests__/login-page.test.tsx` | 4 | Login 頁面整合 (submit/redirect/error/loading) |
| `src/__tests__/register-page.test.tsx` | 5 | Register 頁面整合 (submit/redirect/error/mismatch/loading) |
| `src/__tests__/api/onboarding-birth-data.test.ts` | 12 | Birth data API (tier 3/2/1, evening, 401, 400, PRECISE/TWO_HOUR_SLOT/FUZZY_DAY accuracy_type, event logging) |
| `src/__tests__/api/onboarding-rpv-test.test.ts` | 3 | RPV test API (saves results, 401, 400) |
| `src/__tests__/api/onboarding-photos.test.ts` | 5 | Photos API (upload+blur, 401, 400 missing, 400 type, 400 size) |
| `src/__tests__/api/onboarding-soul-report.test.ts` | 3 | Soul report API (archetype gen, onboarding complete, 401) |
| `src/__tests__/api/matches-daily.test.ts` | 5 | Daily matches API (200 with cards, 401 unauth, empty state, interest_tags) |
| `src/__tests__/api/matches-action.test.ts` | 7 | Action API (accept, pass, mutual accept → connection, 401, 400, 404, no duplicate) |
| `src/__tests__/api/connections.test.ts` | 5 | Connections list API (200 with list, 401 unauth, empty state, other_user, tags) |
| `src/__tests__/api/connections-messages.test.ts` | 8 | Messages API: GET (401, 403, detail+msgs, is_self) + POST (401, 400, 403, insert) |
| `astro-service/test_chart.py` | 37 | 西洋占星 (12) + 八字四柱 (11) + 五行關係 (7) + Phase G 新星體/宮位 (6+1) |
| `src/__tests__/api/rectification-next-question.test.ts` | 6 | Rectification next-question API (401, 204 locked, 204 PRECISE, shape, options, boundary priority) |
| `src/__tests__/api/rectification-answer.test.ts` | 9 | Rectification answer API (401, 400 missing/invalid, 200 state, confidence increase, event log, update users, tier_upgraded) |
| `astro-service/test_matching.py` | 73 | 配對演算法 v1：sign_aspect(9) + kernel(6) + power(4) + glitch(3) + classify(6) + tags(5) + integration(8)；**Phase G v2：** lust(4) + soul(4) + power_v2(4) + chiron(4) + quadrant(5) + attachment(3) + match_v2(8) |
| `src/__tests__/api/onboarding/attachment.test.ts` | 7 | **(Phase G)** Attachment API (400 missing, 400 invalid style, 200 valid, 200 all styles, 401 unauth, role included, 400 invalid role) |
| **Total** | **199** | All passing (89 JS + 110 Python) — +52 Phase G tests |

---

## Infrastructure

| Component | Status | Details |
|-----------|--------|---------|
| Supabase Project | **Done** | URL: `masninqgihbazjirweiy.supabase.co` |
| Auth Provider | **Done** | Email/Password enabled |
| Database (5 tables) | **Done** | users, photos, daily_matches, connections, messages |
| RLS Policies | **Done** | 所有表啟用 Row Level Security |
| DB Triggers | **Done** | `updated_at` 自動更新 + 訊息 → message_count/sync_level |
| Indexes | **Done** | 常用查詢路徑已建立索引 |
| Storage Bucket | **Done** | `photos` bucket + upload/view/delete policies |
| `.env.local` | **Done** | SUPABASE_URL + ANON_KEY |
| Vitest | **Done** | vitest + @testing-library/react + user-event |
| Python Astro Service | **Done** | `astro-service/` — FastAPI + pyswisseph + BaZi + matching algo + pytest (71 tests) |

---

## Deployment

> 完整部署指南見 `docs/DEPLOYMENT.md`

| Service | Platform | Plan | Status | 備註 |
|---------|----------|------|--------|------|
| Next.js App | **Vercel** | Hobby (free) | Not deployed | `vercel` CLI 一鍵部署；git push 自動 CI/CD |
| Python astro-service | **Railway** | Hobby ($5/月) | Not deployed | 支援 pyswisseph C native lib；Procfile: `web: uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Database + Auth + Storage | **Supabase** | Free tier | **Live** | `masninqgihbazjirweiy.supabase.co` |
| AI API (Claude / Gemini / OpenAI) | Anthropic / Google / OpenAI | Pay-as-you-go | Not integrated | 從 Vercel API routes 呼叫；注意 Hobby 方案 10s timeout（長生成需用 Streaming） |

**部署環境變數（Vercel Dashboard 設定）：**
```bash
NEXT_PUBLIC_SUPABASE_URL=https://masninqgihbazjirweiy.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
ASTRO_SERVICE_URL=https://<your-service>.up.railway.app   # Railway 部署後填入
ANTHROPIC_API_KEY=<key>
CRON_SECRET=<secret>   # /api/matches/run 保護
```

**部署順序：**
1. Railway — 部署 astro-service，取得 Railway URL
2. Vercel — 部署 Next.js，設定環境變數（含 ASTRO_SERVICE_URL）
3. Supabase — 執行 Migration 005 + 006（evening fix + Rectification）
4. 端對端測試：註冊 → 星盤計算 → 配對

---

## Known Issues / TODO

1. ~~**照片上傳** — `/onboarding/photos` 目前點擊僅切換 UI 狀態，無真實檔案上傳功能~~ → ✅ Done
2. ~~**所有表單** — 目前均為 `preventDefault()`，未串接任何 API~~ → ✅ Onboarding 4 步 + Login/Register 全部已串接
3. ~~**Mock Data** — Daily Feed、Connections、Chat 均使用寫死的 mock data~~ → ✅ Done（全部已串接真實 API）
4. ~~**Responsive** — 部分頁面在手機尺寸可能需要調整~~ → ✅ Done（全站響應式已完成）
5. **Radar Chart** — 目前用進度條代替，後續可升級為 Recharts/Nivo radar chart
6. **Archetype AI** — 目前為 deterministic 映射 (8 組)，待串接 Claude API 動態生成
7. ~~**Python 星盤** — birth-data API 目前僅存資料，尚未觸發星盤計算~~ → ✅ Done（西洋占星 + 八字四柱 + 真太陽時，已串接 birth-data API 自動回寫 DB）

---

## Next Steps (已完成 → 下一步)

1. ~~**建立 Supabase 專案**~~ — ✅ Done
2. ~~**實作 Auth flow**~~ — ✅ Done (Login/Register + middleware + 19 tests)
3. ~~**實作 Onboarding API**~~ — ✅ Done (birth-data, rpv-test, photos, soul-report + 14 tests)
4. ~~**建立 Python Microservice**~~ — ✅ Done (西洋占星 + 八字四柱 + 真太陽時 + 30 tests)
5. ~~**串接星盤計算到 Next.js**~~ — ✅ Done (birth-data API → astro-service → 回寫 DB，非阻塞式)
6. ~~**Phase C: Daily Matching**~~ — ✅ Done (matching algo + /compute-match + /run + /daily + /action + 53 new tests)
7. ~~**Phase B.5: Rectification Data Layer**~~ — ✅ Done (Migration 006 + accuracy_type/window fields + 4-card UX + quiz endpoints + 15 new tests; total 82 JS tests)
8. ~~**Phase D: Connections + Chat**~~ — ✅ Done (GET /api/connections + GET/POST /api/connections/:id/messages + Realtime + 13 new tests)
9. ~~**Phase G: Matching Algorithm v2**~~ ← ✅ Done (Lust/Soul 雙軸 + 四軌 + Power D/s + Chiron rule + Attachment 問卷 + Mercury/Jupiter/Pluto/Chiron/Juno/House4/8；199 tests)
10. **Phase E: Progressive Unlock + Auto-Disconnect** ← **CURRENT**
11. **Phase F: AI/LLM Integration**

---

## Implementation Plan

### Phase C: Daily Matching (核心配對) ← NEXT

**目標：** 讓用戶每天收到 3 張真實配對卡，可以 Accept/Pass。

| Step | Task | 依賴 | 說明 |
|------|------|------|------|
| C1 | **Matching Algorithm** | astro-service | Python 配對演算法：西洋占星相位比對 + 八字五行相生相剋 + RPV 權力動力 → Match_Score |
| C2 | `POST /compute-match` | C1 | **Done** ✅ Python endpoint：計算兩人配對分數，回傳完整 match result |
| C3 | `GET /api/matches/daily` | C2 | Next.js API：取得今日 3 張卡（含 archetype、tags、radar scores、**interest_tags**） |
| C4 | `POST /api/matches/:id/action` | C3 | Accept/Pass 邏輯：雙方都 Accept → 自動建立 `connections` 記錄 |
| C5 | **Wire Daily UI** | C3, C4 | 串接 `/daily` 頁面，替換 mock data → 真實 API 資料 |

**配對卡資訊（含 interest_tags）：**
```
{
  archetype_name, match_type, total_score,
  tags: [...chameleon_tags],
  interest_tags: ["攝影", "咖啡", "登山"],   // ← 對方的興趣標籤，當話題
  radar: { passion, stability, communication },
  blurred_photo_url
}
```

**Match_Score 公式：**
```
Match_Score = Kernel_Compatibility × 0.5 + Power_Dynamic_Fit × 0.3 + Glitch_Tolerance × 0.2

Kernel_Compatibility:
  - 西洋占星: Sun/Moon/Venus 相位分析 (合/刑/沖/拱/六合)
  - 八字五行: 日主相生相剋 (harmony_score from analyze_element_relation)

Power_Dynamic_Fit:
  - RPV conflict × RPV power 交叉對比 (互補 vs 同類)

Glitch_Tolerance:
  - Mars/Saturn 相位張力 → 衝突容忍度
```

---

### Phase B.5: Rectification Data Layer (出生時間校正) — Specced

**目標：** 讓不知道精確出生時間的用戶也能完成註冊，並透過後續問答（Via Negativa 反問法）逐步校正出生時間，解鎖更高精度的配對功能。

**完整 Spec：** `docs/Dynamic_BirthTimeRectification_Spec.md`
**設計文件：** `docs/plans/2026-02-18-rectification-data-layer-design.md`

| Step | Task | 類型 | 說明 |
|------|------|------|------|
| B5-1 | `supabase/migrations/005_rectification.sql` | **New** | 新增欄位（accuracy_type, window_start/end, rectification_status, current_confidence, active_range, calibrated_time, is_boundary_case, dealbreakers）+ `rectification_events` 表 + 修正 evening constraint |
| B5-2 | `src/lib/supabase/types.ts` | Edit | 新增欄位型別 + rectification_events 表型別 |
| B5-3 | `src/__tests__/api/onboarding-birth-data.test.ts` | Edit | 新增測試：PRECISE/TWO_HOUR_SLOT/FUZZY_DAY + boundary flag + event log |
| B5-4 | `src/app/api/onboarding/birth-data/route.ts` | Edit | 接受新欄位、初始化 rectification state、boundary detection、log event |
| B5-5 | `src/app/onboarding/birth-data/page.tsx` | Rewrite | 4 張卡精度選擇 UX + 12 格 2hr slot grid + FUZZY_DAY 3 選項 |
| B5-6 | `src/app/api/rectification/next-question/route.ts` | **New** | 選題邏輯（Asc/Dsc 換座優先 > 月亮換座 > 八字時柱 > 資訊增益最大化） |
| B5-7 | `src/app/api/rectification/answer/route.ts` | **New** | applyNegativeFilter → 更新 confidence → lockIfReady → log event |

**Onboarding UX 精度卡片（card D → accuracy_type 對照）：**

| 卡片 | 精度類型 | 初始信心值 | 下一步 |
|------|---------|-----------|--------|
| A — 我有精確時間 | `PRECISE` | 0.90 | time picker (HH:mm) |
| B — 我知道大概時段 | `TWO_HOUR_SLOT` | 0.30 | 12 格 2hr slot grid |
| C — 我只知道大概 | `FUZZY_DAY` (period) | 0.15 | 早上/下午/晚上 3 選項 |
| D — 我完全不知道 | `FUZZY_DAY` (unknown) | 0.05 | 直接進入下一步 |

**注意：** 目前 `birth_time` CHECK constraint 有 bug，缺少 `evening` 值，Migration 005 同時修正此問題。

---

### Phase D: Connections + Chat (含圖片訊息)

**目標：** 雙向 Accept 後進入聊天室，支援文字 + 圖片訊息，Supabase Realtime 即時更新。

| Step | Task | 依賴 | 說明 |
|------|------|------|------|
| D1 | `GET /api/connections` | C4 | 列出所有活躍 connections（含 sync_level, last_message, status） |
| D2 | `GET /api/connections/:id` | D1 | 單一 connection 詳情 + 對方 profile（blurred photo, tags） |
| D3 | **Icebreaker** | D2 | 破冰題生成 + `POST /api/connections/:id/icebreaker-answer` |
| D4 | `GET /api/connections/:id/messages` | D2 | 分頁載入訊息 (cursor-based pagination) |
| D5 | `POST /api/connections/:id/messages` | D4 | 發送文字訊息，更新 message_count + sync_level |
| D6 | **圖片訊息** | D5 | `POST /api/connections/:id/messages/image`：上傳圖片至 Storage → 存 message record（type=image） |
| D7 | **Supabase Realtime** | D5 | 訂閱 `messages` 表 INSERT → 即時顯示新訊息（不需重新整理） |
| D8 | **Wire Chat UI** | D4-D7 | 串接 `/connections` + `/connections/[id]` 頁面 |

**DB 變更（messages 表增加圖片支援）：**
```sql
-- Migration 005: Chat image support
ALTER TABLE public.messages ADD COLUMN IF NOT EXISTS message_type TEXT DEFAULT 'text'
  CHECK (message_type IN ('text', 'image'));
ALTER TABLE public.messages ADD COLUMN IF NOT EXISTS image_path TEXT;  -- Storage path
```

---

### Phase E: Progressive Unlock + Auto-Disconnect

| Step | Task | 依賴 | 說明 |
|------|------|------|------|
| E1 | **Sync Level Logic** | D5 | message_count → 自動升級 sync_level (0-10: Lv.1, 10-50: Lv.2, 50+: Lv.3) |
| E2 | **Photo Unlock** | E1 | Lv.1: 全模糊, Lv.2: 50% 清晰 (half_blurred_path), Lv.3: 完整 HD |
| E3 | **24hr Auto-Disconnect** | D1 | DB cron/trigger：24hr 無活動 → status='expired'，前端顯示過期狀態 |

---

### Phase G: Matching Algorithm v2（擴充星體 + 雙軸 + 四軌）

**設計文件：** `docs/plans/2026-02-20-expanded-matching-algorithm-design.md`
**依賴：** Phase C 已完成（matching.py 基礎存在）

| Step | Task | 類型 | 說明 |
|------|------|------|------|
| G1 | **Migration 007** | New SQL | 新增 `mercury_sign, jupiter_sign, pluto_sign, chiron_sign, juno_sign, house4_sign, house8_sign, attachment_style, attachment_role` |
| G2 | **chart.py 擴充** | Edit | 加入 Mercury/Jupiter/Pluto/Chiron/Juno + House 4/8；`swe.set_ephe_path('./ephe')`；Tier 2/3 降級 null |
| G3 | **bazi.py** | Edit | 加入 `swe.set_ephe_path('./ephe')` |
| G4 | **matching.py 重寫** | Rewrite | 用新架構取代舊 `Match_Score`：`calculate_lust_score` + `calculate_soul_score` + `calculate_power` + `calculate_tracks` + `classify_quadrant` |
| G5 | **test_matching.py 更新** | Edit | 新增 ~37 個測試（見設計文件 §13）；舊測試遷移/移除 |
| G6 | **`/api/onboarding/attachment`** | New API | Next.js 新端點：接受 Q_A1/Q_A2 → 回寫 `attachment_style/role` |
| G7 | **birth-data API 更新** | Edit | 呼叫 astro-service 後，回寫新欄位（mercury_sign ... house8_sign） |
| G8 | **types.ts 更新** | Edit | 新增 Migration 007 欄位型別 |
| G9 | **daily feed 輸出更新** | Edit | `/api/matches/daily` 改用新 Schema 輸出 `primary_track` / `lust_score` / `soul_score` |

**Attachment 問卷（2 題，加入 Onboarding Step 2 或獨立 Step）：**

| 題號 | 問題 | 選項 |
|------|------|------|
| Q_A1 | 當你喜歡上一個人，你更像⋯⋯ | A.焦慮確認(anxious) / B.保持距離(avoidant) / C.自然流動(secure) |
| Q_A2 | 在親密關係裡，你更渴望⋯⋯ | A.成為依靠(dom_secure) / B.完全放下防備(sub_secure) / C.獨立又黏著(balanced) |

**星曆檔（已下載至 `astro-service/ephe/`）：**
- `seas_18.se1`（Chiron + Juno）
- `sepl_18.se1`（行星）
- `semo_18.se1`（月亮）

---

### Phase F: AI/LLM Integration (後續)

| Step | Task | 說明 |
|------|------|------|
| F1 | **Dynamic Archetype** | Claude API → 根據完整 profile 動態生成靈魂原型（取代 8 組 deterministic） |
| F2 | **Chameleon Tags** | Claude API → 根據配對雙方 profile 動態生成 3-5 個關係標籤 |
| F3 | **Icebreaker Questions** | Claude API → 根據雙方 profile + 配對類型生成個性化破冰題 |

---

### Phase Summary

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase A: Onboarding API | birth-data, rpv-test, photos, soul-report | **Done** ✅ |
| Phase B: Python Microservice | 西洋占星 + 八字四柱 + 真太陽時 + API 串接 | **Done** ✅ |
| Phase C: Daily Matching | matching algorithm + daily API + Accept/Pass | **Done** ✅ |
| Phase B.5: Rectification Data Layer | Migration 006 + accuracy_type + 4-card UX + quiz API (15 new tests) | **Done** ✅ |
| Phase D: Connections + Chat | connections API + text/image chat + Realtime | **Done** ✅ |
| Phase E: Progressive Unlock | sync level + photo unlock + 24hr disconnect | Pending |
| Phase F: AI/LLM | dynamic archetype + chameleon tags + icebreaker | Pending |
| **Phase G: Matching v2** | Lust/Soul 雙軸 + 四軌（friend/passion/partner/soul）+ Power D/s frame + Chiron rule + Attachment 問卷 + Mercury/Jupiter/Pluto/Chiron/Juno/House4/8；Migration 007；110 Python + 89 JS tests | **Done ✅** |
| ~~Phase E (old): Profile~~ | GET/PATCH API + photos + bio + tags + energy | **Done** ✅ |
