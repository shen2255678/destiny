# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DESTINY** is a precision matchmaking dating platform that combines Vedic Astrology (占星學), Attachment Psychology (依戀心理學), and BDSM Power Dynamics (權力動力學) for deep compatibility matching. The tagline: "We don't match faces, we match Source Codes."

**Status:** Active development — Phase A (Onboarding) complete, Phase B (Python Microservice) next.

## Repository Structure

```
destiny/
├── destiny-app/          # Next.js 16 App Router (main application)
│   ├── src/
│   │   ├── app/          # Pages + API routes
│   │   │   ├── api/onboarding/   # birth-data, rpv-test, photos, soul-report
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   ├── onboarding/       # 4-step onboarding UI
│   │   │   ├── daily/
│   │   │   ├── connections/
│   │   │   └── profile/
│   │   ├── lib/
│   │   │   ├── supabase/         # client.ts, server.ts, middleware.ts, types.ts
│   │   │   ├── auth.ts           # register/login/logout/getCurrentUser
│   │   │   └── ai/archetype.ts   # Deterministic archetype generator
│   │   ├── middleware.ts          # Auth guard (redirects to /login)
│   │   └── __tests__/            # Vitest tests (33 tests, 7 files)
│   ├── supabase/migrations/      # 001_initial_schema.sql (pushed to remote)
│   └── .env.local                # SUPABASE_URL + ANON_KEY
├── docs/
│   ├── MVP-PROGRESS.md           # Progress tracker (source of truth)
│   ├── TECH-STACK.md
│   └── superbase.md              # Supabase project details
└── CLAUDE.md                     # This file
```

## Key Documentation

- `docs/MVP-PROGRESS.md` — Progress tracker with all endpoints, test coverage, known issues
- `docs/TECH-STACK.md` — Architecture details and DB schema
- `docs/superbase.md` — Supabase project config (ref: `masninqgihbazjirweiy`)
- `MVP_PHASE1.pdf` — Detailed MVP specification
- `產品企劃書.pdf` — Complete product plan
- `Soul_Codes.pdf` — Zodiac personality/compatibility models

## Technology Stack

- **Frontend:** Next.js 16 App Router, TypeScript, Tailwind CSS v4
- **Backend:** Next.js API Routes (server-side), Supabase (Auth + PostgreSQL + Storage)
- **Database:** Supabase PostgreSQL — 5 tables with RLS, triggers, indexes
- **Image Processing:** sharp (Gaussian blur for progressive photo reveal)
- **Testing:** Vitest + @testing-library/react + user-event (TDD workflow)
- **Planned:** Python FastAPI + swisseph (astrology), Claude API (AI archetypes/tags)

## Development Commands

```bash
cd destiny-app
npm run dev          # Start dev server (localhost:3000)
npm test             # Run Vitest tests (33 tests)
npx vitest run       # Run tests once (CI mode)
npm run build        # Production build
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

### Data Integrity Tiers

- **Tier 1 (Gold):** Precise birth time → full D1 & D9 chart
- **Tier 2 (Silver):** Fuzzy birth time → medium accuracy with fuzzy logic
- **Tier 3 (Bronze):** Birth date only → limited astrology

### Onboarding Flow (4 steps, all wired)

1. `/onboarding/birth-data` → `POST /api/onboarding/birth-data` (computes data_tier)
2. `/onboarding/rpv-test` → `POST /api/onboarding/rpv-test` (maps option IDs to DB values)
3. `/onboarding/photos` → `POST /api/onboarding/photos` (sharp blur + Supabase Storage)
4. `/onboarding/soul-report` → `GET /api/onboarding/soul-report` (archetype generation)

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
- **Tables:** users, photos, daily_matches, connections, messages
- **RLS:** Enabled on all tables
- **Storage:** `photos` bucket (original + blurred versions)
- **Auth:** Email/Password

## Conventions

- Code and identifiers in English; UI copy in Traditional Chinese (繁體中文)
- TDD: Write failing test → implement → verify green
- API routes use Supabase server client (`src/lib/supabase/server.ts`)
- All API routes check auth via `supabase.auth.getUser()`
- Onboarding steps tracked via `users.onboarding_step` field

## Language Notes

Product documentation and UI copy are primarily in Traditional Chinese (繁體中文). Code and technical identifiers should use English.
