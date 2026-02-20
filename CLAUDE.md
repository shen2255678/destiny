# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DESTINY** is a precision matchmaking dating platform that combines Vedic Astrology (占星學), Attachment Psychology (依戀心理學), and BDSM Power Dynamics (權力動力學) for deep compatibility matching. The tagline: "We don't match faces, we match Source Codes."

**Status:** Active development — Phase A ✅, Phase B ✅, Phase C ✅, Phase D ✅, Phase B.5 ✅, Phase E (AI Archetypes) **NEXT**.

## Repository Structure

```
destiny/
├── destiny-app/          # Next.js 16 App Router (main application)
│   ├── src/
│   │   ├── app/          # Pages + API routes
│   │   │   ├── api/onboarding/   # birth-data, rpv-test, photos, soul-report
│   │   │   ├── api/matches/      # action (like/pass), daily (feed)
│   │   │   ├── api/connections/  # list, [id]/messages
│   │   │   ├── api/rectification/  # next-question, answer
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   ├── onboarding/       # 4-step onboarding UI (birth-data has 4-card precision flow)
│   │   │   ├── daily/
│   │   │   ├── connections/
│   │   │   └── profile/
│   │   ├── lib/
│   │   │   ├── supabase/         # client.ts, server.ts, middleware.ts, types.ts
│   │   │   ├── auth.ts           # register/login/logout/getCurrentUser
│   │   │   └── ai/archetype.ts   # Deterministic archetype generator
│   │   ├── middleware.ts          # Auth guard (redirects to /login)
│   │   └── __tests__/            # Vitest tests (82 tests, 13 files)
│   ├── supabase/migrations/      # 001-006 migrations (pushed to remote)
│   └── .env.local                # SUPABASE_URL + ANON_KEY
├── astro-service/                # Python microservice (FastAPI + Swiss Ephemeris)
│   ├── main.py                   # FastAPI server (port 8001)
│   ├── chart.py                  # Western astrology: planetary positions → zodiac signs
│   ├── bazi.py                   # BaZi (八字四柱): Four Pillars + Five Elements + true solar time
│   ├── matching.py               # Compatibility scoring: WesternScore + BaZiScore → Match_Score
│   ├── test_chart.py             # pytest (30 tests)
│   ├── test_matching.py          # pytest (41 tests)
│   └── requirements.txt
├── docs/
│   ├── MVP-PROGRESS.md           # Progress tracker (source of truth)
│   ├── TESTING-GUIDE.md          # Three-layer testing strategy + astro-service
│   ├── ASTRO-SERVICE.md          # Astro microservice API guide
│   ├── DEPLOYMENT.md             # Vercel + Railway + AI API strategy
│   ├── Dynamic_BirthTimeRectification_Spec.md  # Phase B.5 完整 spec
│   ├── TECH-STACK.md
│   ├── superbase.md              # Supabase project details
│   └── plans/
│       ├── 2026-02-14-destiny-mvp-design.md
│       └── 2026-02-18-rectification-data-layer-design.md  # Phase B.5 設計文件
└── CLAUDE.md                     # This file
```

## Key Documentation

- `docs/MVP-PROGRESS.md` — Progress tracker with all endpoints, test coverage, known issues (**read this first**)
- `docs/TESTING-GUIDE.md` — Three-layer testing strategy (unit/E2E/API) + astro-service
- `docs/ASTRO-SERVICE.md` — Python astro microservice API guide
- `docs/TECH-STACK.md` — Architecture details and DB schema
- `docs/superbase.md` — Supabase project config (ref: `masninqgihbazjirweiy`)
- `docs/DEPLOYMENT.md` — Hosting guide: Vercel (Next.js) + Railway (Python) + AI API timeout strategy
- `docs/Dynamic_BirthTimeRectification_Spec.md` — Full spec for Dynamic Birth Time Rectification (Phase B.5)
- `docs/plans/2026-02-18-rectification-data-layer-design.md` — DB schema + API contract + UX flow for Phase B.5
- `MVP_PHASE1.pdf` — Detailed MVP specification
- `產品企劃書.pdf` — Complete product plan
- `Soul_Codes.pdf` — Zodiac personality/compatibility models

## Technology Stack

- **Frontend:** Next.js 16 App Router, TypeScript, Tailwind CSS v4
- **Backend:** Next.js API Routes (server-side), Supabase (Auth + PostgreSQL + Storage + Realtime)
- **Database:** Supabase PostgreSQL — 6 tables with RLS, triggers, indexes
- **Image Processing:** sharp (Gaussian blur for progressive photo reveal)
- **Testing:** Vitest + @testing-library/react + user-event (TDD workflow); pytest for Python
- **Astro Service:** Python FastAPI + pyswisseph (Western astrology) + BaZi (八字四柱, true solar time) + matching.py (compatibility scoring)
- **Planned:** Claude API (AI archetypes/tags)

## Development Commands

```bash
# Next.js App
cd destiny-app
npm run dev          # Start dev server (localhost:3000)
npm test             # Run Vitest tests (82 tests, 13 files)
npx vitest run       # Run tests once (CI mode)
npm run build        # Production build

# Astro Service (Python)
cd astro-service
pip install -r requirements.txt   # Install dependencies (first time)
uvicorn main:app --port 8001      # Start service
pytest test_chart.py -v           # Run chart tests (30 tests)
pytest test_matching.py -v        # Run matching tests (41 tests)
pytest -v                         # Run all Python tests (71 tests)
```

## Architecture

### Three-Layer System

1. **Data Ingestion Layer** — Birth chart data, RPV test (3 questions), 2 Gaussian-blurred photos
2. **Match Engine ("Black Box")** — Pushes 3 daily candidates; blind matching with labels, not photos
3. **Interaction Layer** — Progressive unlock: Lv.1 (text) → Lv.2 (50% photo) → Lv.3 (full HD); 24hr auto-disconnect

### Core Matching Algorithm

```
Match_Score = (Kernel_Compatibility × 0.5) + (Power_Dynamic_Fit × 0.3) + (Glitch_Tolerance × 0.2)
```

Kernel_Compatibility 由兩套系統組成：
- **西洋占星 (Western Astrology)** — 6 行星 + 上升星座 → 吸引的成因
- **八字四柱 (BaZi)** — 日主五行 + 相生相剋 → 相處的姿態

Implemented in `astro-service/matching.py`:
- `POST /score-compatibility` — Returns Match_Score + breakdown (western, bazi, power_dynamic, glitch)
- `POST /analyze-relation` — 五行關係分析（相生/相剋/比和）

### Astro Service (`astro-service/`)

Python FastAPI 微服務，提供：
- `POST /calculate-chart` — 西洋占星 + 八字計算（自動呼叫於 birth-data API）
- `POST /score-compatibility` — 完整相容性評分 → Match_Score
- `POST /analyze-relation` — 五行關係分析（相生/相剋/比和）
- `GET /health` — Health check
- **真太陽時 (True Solar Time):** BaZi 時柱使用經度修正 + 均時差 (Equation of Time)
- **非阻塞式整合:** astro-service 不可用時，onboarding 不受影響，星盤欄位保持 null

### Data Integrity Tiers

- **Tier 1 (Gold):** Precise birth time → full chart + 完整四柱（年月日時）
- **Tier 2 (Silver):** Fuzzy birth time → medium accuracy + 近似時柱
- **Tier 3 (Bronze):** Birth date only → Sun sign only + 三柱（無時柱）

### Dynamic Birth Time Rectification (Phase B.5)

Via Negativa quiz system — users eliminate what they are NOT to narrow birth time window.

**AccuracyType → Initial Confidence:**

| AccuracyType | Confidence | Window |
|---|---|---|
| `PRECISE` | 0.90 | 0 min |
| `TWO_HOUR_SLOT` | 0.30 | 120 min |
| `FUZZY_DAY` (morning/afternoon/evening) | 0.15 | 360 min |
| `FUZZY_DAY` (unknown) | 0.05 | 1440 min |

**RectificationStatus flow:** `unrectified → collecting_signals → narrowed_to_2hr → locked`

- `GET /api/rectification/next-question` — Returns next Via Negativa question (204 if PRECISE/locked)
- `POST /api/rectification/answer` — Applies +0.10 confidence per answer; locks at ≥ 0.80

### Onboarding Flow (4 steps, all wired)

1. `/onboarding/birth-data` → `POST /api/onboarding/birth-data` (4-card precision UI: PRECISE/TWO_HOUR_SLOT/FUZZY_DAY/UNKNOWN; computes data_tier + accuracy_type + auto-calls astro-service)
2. `/onboarding/rpv-test` → `POST /api/onboarding/rpv-test` (maps option IDs to DB values)
3. `/onboarding/photos` → `POST /api/onboarding/photos` (sharp blur + Supabase Storage)
4. `/onboarding/soul-report` → `GET /api/onboarding/soul-report` (archetype generation)

### Daily Matches Flow (Phase C)

- `GET /api/matches/daily` — Returns 3 daily candidates with archetype labels (no photos)
- `POST /api/matches/action` — Records like/pass; triggers connection creation on mutual like

### Connections Flow (Phase D)

- `GET /api/connections` — Lists active connections with unlock level
- `GET /api/connections/[id]/messages` — Returns message history
- `POST /api/connections/[id]/messages` — Sends message; Supabase Realtime broadcasts

### RPV Option Mapping

| Option ID | Field | DB Value |
|-----------|-------|----------|
| 1A | rpv_conflict | cold_war |
| 1B | rpv_conflict | argue |
| 2A | rpv_power | control |
| 2B | rpv_power | follow |
| 3A | rpv_energy | home |
| 3B | rpv_energy | out |

## Supabase

- **Project ref:** `masninqgihbazjirweiy`
- **Tables:** users, photos, daily_matches, connections, messages, rectification_events
- **Migrations:** 001–006 (all pushed to remote)
- **RLS:** Enabled on all tables
- **Storage:** `photos` bucket (original + blurred versions)
- **Auth:** Email/Password
- **Realtime:** Enabled on `messages` table

## Conventions

- Code and identifiers in English; UI copy in Traditional Chinese (繁體中文)
- TDD: Write failing test → implement → verify green
- API routes use Supabase server client (`src/lib/supabase/server.ts`)
- All API routes check auth via `supabase.auth.getUser()`
- Onboarding steps tracked via `users.onboarding_step` field

## Language Notes

Product documentation and UI copy are primarily in Traditional Chinese (繁體中文). Code and technical identifiers should use English.
