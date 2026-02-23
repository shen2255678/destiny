# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DESTINY** is a precision matchmaking dating platform that combines Vedic Astrology (占星學), Attachment Psychology (依戀心理學), and BDSM Power Dynamics (權力動力學) for deep compatibility matching. The tagline: "We don't match faces, we match Source Codes."

**Status:** Active development — Phase A ✅, Phase B ✅, Phase C ✅, Phase D ✅, Phase B.5 ✅, Phase E (AI Archetypes) **NEXT**.

**Algorithm:** v1.9 — orb-based kernel/glitch scoring; ASC cross-aspects in lust; Lunar Node karmic triggers (3° orb, soul_mod ±20); 7th House Descendant overlay (partner_mod +20, soul_mod +10); personal Karmic Axis in psychology.py; planet_degrees wired end-to-end.

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
│   ├── chart.py                  # Western astrology: planetary positions → zodiac signs (Tier 1: +Vertex/Lilith)
│   ├── bazi.py                   # BaZi (八字四柱): Four Pillars + Five Elements + true solar time
│   ├── matching.py               # Compatibility scoring v1.9: lust/soul 雙軸 + 四軌 + shadow modifiers + Lunar Nodes + Descendant partner_mod
│   ├── shadow_engine.py          # Chiron wound triggers + Vertex/Lilith synastry + 12th-house + attachment trap + 7th House Overlay
│   ├── psychology.py             # Weighted element profile + retrograde karma tags + SM dynamics + Karmic Axis
│   ├── prompt_manager.py         # Chinese tag translations for shadow/psych/synastry tags
│   ├── zwds.py                   # ZWDS bridge (ziwei-service HTTP client, Tier 1 only)
│   ├── test_chart.py             # pytest (109 tests)
│   ├── test_matching.py          # pytest (173 tests)
│   ├── test_shadow_engine.py     # pytest (56 tests)
│   ├── test_psychology.py        # pytest (33 tests)
│   ├── test_zwds.py              # pytest (31 tests)
│   ├── test_sandbox.py           # pytest (5 tests)
│   └── requirements.txt
├── docs/
│   ├── MVP-PROGRESS.md           # Progress tracker (source of truth)
│   ├── TESTING-GUIDE.md          # Three-layer testing strategy + astro-service
│   ├── ASTRO-SERVICE.md          # Astro microservice API guide
│   ├── HOW-IT-WORKS.md           # User-facing algorithm explanation (繁體中文)
│   ├── WEIGHTS-TUNING-GUIDE.md   # Algorithm weight tuning reference (v1.6)
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
- `docs/HOW-IT-WORKS.md` — User-facing explanation of matching algorithm (繁體中文)
- `docs/WEIGHTS-TUNING-GUIDE.md` — How to adjust algorithm weights; all WEIGHTS keys documented
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
pytest test_chart.py -v           # Run chart tests (102 tests)
pytest test_matching.py -v        # Run matching tests (173 tests)
pytest -v                         # Run all Python tests (387 tests, 6 files)
```

## Architecture

### Three-Layer System

1. **Data Ingestion Layer** — Birth chart data, RPV test (3 questions), 2 Gaussian-blurred photos
2. **Match Engine ("Black Box")** — Pushes 3 daily candidates; blind matching with labels, not photos
3. **Interaction Layer** — Progressive unlock: Lv.1 (text) → Lv.2 (50% photo) → Lv.3 (full HD); 24hr auto-disconnect

### Core Matching Algorithm (v1.9)

All weights are centralized in the `WEIGHTS` dict at the top of `matching.py`. See `docs/WEIGHTS-TUNING-GUIDE.md` for the full reference.

**v1 formula (compute_match_score):**
```
Match_Score = (Kernel_Compatibility × 0.5) + (Power_Dynamic_Fit × 0.3) + (Glitch_Tolerance × 0.2)
```

**v2 formula (compute_match_v2)** — 雙軸 + 四軌：
```
compute_match_v2()
├── compute_lust_score()      → X 軸（生理吸引力）
│   ├── mars_a × venus_b      → cross-person primary (WEIGHTS["lust_cross_mars_venus"] = 0.30)
│   ├── mars_b × venus_a      → cross-person primary (WEIGHTS["lust_cross_venus_mars"] = 0.30)
│   ├── venus × venus / mars × mars  → same-planet secondary
│   ├── house8, karmic triggers, power score
│   ├── Jupiter Friend Track: (jup_a×sun_b + jup_b×sun_a)/2 (fix: no same-year cohort inflation)
│   └── BaZi restriction multiplier (× 1.25 if 相剋)
├── compute_soul_score()      → Y 軸（靈魂深度）
│   ├── Moon, Mercury, Saturn, House4, Attachment
│   ├── Juno cross-aspect: (juno_a×moon_b + juno_b×moon_a)/2 (fix: no same-sign inflation)
│   └── BaZi generation multiplier (× 1.20 if 相生)
├── compute_tracks()          → 四軌（friend / passion / partner / soul）
└── compute_power_v2()        → RPV 動力（conflict / power / energy）
```

**Aspect scoring (linear orb decay):**
```
strength_ratio = 1.0 - (diff / orb)
final_score = 0.2 + (max_score - 0.2) × strength_ratio
```
0° conjunction → 1.0; 7° conjunction → ~0.30. Defined in `ASPECT_RULES` module constant.

Implemented in `astro-service/matching.py`:
- `POST /score-compatibility` — Returns Match_Score + breakdown (western, bazi, power_dynamic, glitch)
- `POST /analyze-relation` — 五行關係分析（相生/相剋/比和）

### Astro Service (`astro-service/`)

Python FastAPI 微服務，提供：
- `POST /calculate-chart` — 西洋占星 + 八字計算 + Tier 1 新增 Vertex/Lilith 提取（自動呼叫於 birth-data API）
- `POST /score-compatibility` — 完整相容性評分 → Match_Score
- `POST /analyze-relation` — 五行關係分析（相生/相剋/比和）
- `POST /compute-match` — v2 雙軸四軌匹配 + shadow modifiers + ZWDS bridge
- `POST /compute-zwds-chart` — ZWDS 12-palace chart (Tier 1)
- `GET /health` — Health check
- **真太陽時 (True Solar Time):** BaZi 時柱使用經度修正 + 均時差 (Equation of Time)
- **非阻塞式整合:** astro-service 不可用時，onboarding 不受影響，星盤欄位保持 null
- **Shadow Modifiers (shadow_engine.py):** Chiron wound triggers (5° orb) + Vertex soul triggers (3°) + Lilith lust triggers (3°) + 12th-house overlay + attachment trap matrix
- **Tier 1 bodies:** Vertex (`ascmc[3]`), Lilith (`swe.MEAN_APOG`) — absent in Tier 2/3

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
- **Migrations:** 001–012 (all pushed to remote)
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
