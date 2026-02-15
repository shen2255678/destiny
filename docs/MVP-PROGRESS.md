# DESTINY MVP — Progress Tracker

**Last Updated:** 2026-02-16

---

## Frontend Pages

| Route | Page | UI Status | DB 串接 | 備註 |
|-------|------|-----------|---------|------|
| `/` | Landing Page | Done | N/A | 靜態行銷頁，無需 DB |
| `/login` | Login | Done | **Done** | 已串接 Supabase Auth + error handling + loading state |
| `/register` | Register | Done | **Done** | 已串接 Supabase Auth + error handling + loading state |
| `/onboarding` | Redirect | Done | N/A | 自動導向 /onboarding/birth-data |
| `/onboarding/birth-data` | Step 1: 硬體規格 | Done | **Done** | 已串接 `POST /api/onboarding/birth-data` + data_tier 計算 |
| `/onboarding/rpv-test` | Step 2: 作業系統 | Done | **Done** | 已串接 `POST /api/onboarding/rpv-test`，option ID → DB value 映射 |
| `/onboarding/photos` | Step 3: 視覺門檻 | Done | **Done** | 已串接 `POST /api/onboarding/photos`，真實檔案上傳 + sharp 高斯模糊 |
| `/onboarding/soul-report` | Step 4: 靈魂原型 | Done | **Done** | 已串接 `GET /api/onboarding/soul-report`，deterministic 原型生成 (待升級 AI) |
| `/daily` | Daily Feed (3 Cards) | Done | Pending | 需串接 `GET /api/matches/daily`，目前為 mock data |
| `/connections` | Connections List | Done | Pending | 需串接 `GET /api/connections` |
| `/connections/[id]` | Chat Room | Done | Pending | 需串接 Supabase Realtime + `GET/POST /api/connections/:id/messages` |
| `/profile` | Self-View Profile + Edit | Done | **Done** | 已串接 `GET/PATCH /api/profile/me` + 編輯模式 + 照片 signed URL + bio + 興趣標籤 |

---

## Backend / API

| Module | Status | Description |
|--------|--------|-------------|
| Supabase 專案建立 | **Done** | 專案已建立 (`masninqgihbazjirweiy`)，Auth provider 已設定 (Email/Password) |
| Database Schema | **Done** | 5 張表已建立 + RLS + triggers + indexes + storage bucket (`001` → `003` migrations) |
| Migration 002 | **Done** | `social_energy` 欄位 (high/medium/low) |
| Migration 003 | **Done** | `bio` (TEXT, 500 字上限) + `interest_tags` (JSONB) 欄位 |
| Supabase Client | **Done** | `client.ts` (browser) + `server.ts` (SSR) + `middleware.ts` (session) |
| Auth Middleware | **Done** | `src/middleware.ts` — 自動 redirect 未登入用戶到 /login |
| Auth Functions | **Done** | `src/lib/auth.ts` — register/login/logout/getCurrentUser + email/password 驗證 |
| TypeScript Types | **Done** | `src/lib/supabase/types.ts` — 完整 Database 型別定義 + Relationships（Supabase JS v2.95 相容） |
| Onboarding API (4 endpoints) | **Done** | birth-data, rpv-test, photos, soul-report — 全部已實作 + TDD |
| Image Processing | **Done** | sharp 高斯模糊 + 基本驗證 (MIME type + size limit 10MB) — 詳見 `docs/PHOTO-PIPELINE.md` |
| Archetype Generator | **Done** | `src/lib/ai/archetype.ts` — 8 組 deterministic 原型 (待升級 Claude API) |
| API Routes (其餘) | Not Started | Daily matching, connections, chat, profile endpoints |
| Python Microservice | Not Started | FastAPI + Swiss Ephemeris，星盤計算引擎 |
| AI/LLM Integration | Not Started | Claude API 串接 (動態原型、變色龍標籤、破冰題) |

---

## Backend API Endpoints

### Auth & Onboarding
- [x] `POST /api/auth/register` — Supabase Auth 註冊 (透過 `src/lib/auth.ts`)
- [x] `POST /api/onboarding/birth-data` — 儲存出生資料 + 計算 data_tier (1/2/3)
- [x] `POST /api/onboarding/rpv-test` — 儲存 RPV 三題測試結果 (conflict/power/energy)
- [x] `POST /api/onboarding/photos` — 上傳 2 張照片 + sharp 高斯模糊 + Supabase Storage
- [x] `GET /api/onboarding/soul-report` — 生成靈魂原型 + base stats + 更新 onboarding_step=complete

### Daily Destiny
- [ ] `GET /api/matches/daily` — 取得今日 3 張配對卡
- [ ] `POST /api/matches/:id/action` — 提交 Accept / Pass

### Connections
- [ ] `GET /api/connections` — 列出所有活躍連結
- [ ] `GET /api/connections/:id` — 連結詳情 + sync level
- [ ] `POST /api/connections/:id/icebreaker-answer` — 提交破冰答案

### Chat
- [ ] `GET /api/connections/:id/messages` — 取得訊息 (分頁)
- [ ] `POST /api/connections/:id/messages` — 發送訊息

### Profile
- [x] `GET /api/profile/me` — 自我檢視：所有個人資料 + 照片 signed URL + bio + interest_tags
- [x] `PATCH /api/profile/me` — 更新個人資料（display_name, 出生資料, RPV, bio, interest_tags, 自動重算 data_tier）
- [x] `POST /api/profile/me/photos` — 重新上傳照片
- [x] `GET /api/profile/energy` — 取得社交能量狀態
- [x] `PATCH /api/profile/energy` — 更新社交能量狀態 (high/medium/low)

---

## Python Microservice (待實作)

- [ ] `POST /calculate-chart` — 計算星盤 (Swiss Ephemeris)
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
| Daily Match Cards | UI Done, Data Pending | 需 Python matching + API |
| Dual Blind Selection (Accept/Pass) | UI Done, Logic Pending | 需 API |
| Chameleon Tags | UI Mock Only | 需 AI API 動態生成 |
| Radar Chart (激情/穩定/溝通) | UI Done (bars), Data Pending | 考慮升級為 Recharts radar |
| Progressive Unlock (Lv.1→2→3) | UI Shown, Logic Pending | 需 DB trigger |
| Chat (Text) | UI Done, Realtime Pending | 需 Supabase Realtime |
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
| `src/__tests__/api/onboarding-birth-data.test.ts` | 5 | Birth data API (tier 3/2/1, 401 unauth, 400 missing) |
| `src/__tests__/api/onboarding-rpv-test.test.ts` | 3 | RPV test API (saves results, 401, 400) |
| `src/__tests__/api/onboarding-photos.test.ts` | 5 | Photos API (upload+blur, 401, 400 missing, 400 type, 400 size) |
| `src/__tests__/api/onboarding-soul-report.test.ts` | 3 | Soul report API (archetype gen, onboarding complete, 401) |
| **Total** | **35** | All passing |

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

---

## Known Issues / TODO

1. ~~**照片上傳** — `/onboarding/photos` 目前點擊僅切換 UI 狀態，無真實檔案上傳功能~~ → ✅ Done
2. ~~**所有表單** — 目前均為 `preventDefault()`，未串接任何 API~~ → ✅ Onboarding 4 步 + Login/Register 全部已串接
3. **Mock Data** — Daily Feed、Connections、Chat 均使用寫死的 mock data（Profile 已串接真實資料）
4. ~~**Responsive** — 部分頁面在手機尺寸可能需要調整~~ → ✅ Done（全站響應式已完成）
5. **Radar Chart** — 目前用進度條代替，後續可升級為 Recharts/Nivo radar chart
6. **Archetype AI** — 目前為 deterministic 映射 (8 組)，待串接 Claude API 動態生成
7. **Python 星盤** — birth-data API 目前僅存資料，尚未觸發星盤計算

---

## Next Steps (建議優先順序)

1. ~~**建立 Supabase 專案**~~ — ✅ Done
2. ~~**實作 Auth flow**~~ — ✅ Done (Login/Register + middleware + 19 tests)
3. ~~**實作 Onboarding API**~~ — ✅ Done (birth-data, rpv-test, photos, soul-report + 14 tests)
4. **建立 Python Microservice** — FastAPI + swisseph 星盤計算 ← **NEXT**
5. **實作 Daily Matching** — Python cron + match algorithm
6. **串接 AI/LLM** — 動態原型生成、變色龍標籤
7. **實作 Chat** — Supabase Realtime WebSocket
8. **Progressive Unlock Logic** — DB trigger + frontend unlock

---

## Implementation Plan

完整實作計劃見：`C:\Users\haowei\.claude\plans\declarative-jingling-dongarra.md`

| Phase | Tasks | Status |
|-------|-------|--------|
| Phase A: Onboarding API | Tasks 1-4 (birth-data, rpv-test, photos, soul-report) | **Done** ✅ |
| Phase B: Python Microservice | Tasks 5-6 (chart calculation, wire to API) | Pending |
| Phase C: Daily Matching | Tasks 7-10 (matching, daily feed, actions, AI tags) | Pending |
| Phase D: Connections + Chat | Tasks 11-13 (connections, icebreaker, realtime chat) | Pending |
| Phase E: Profile + Finishing | Tasks 14-15 (profile API, 24hr auto-disconnect) | **Partial** ✅ Profile done, 24hr pending |
