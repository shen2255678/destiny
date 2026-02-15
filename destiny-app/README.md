# DESTINY — destiny-app

Precision matchmaking platform built with Next.js 16, Supabase, and Tailwind CSS v4.

## Tech Stack

- **Framework:** Next.js 16 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS v4
- **Backend:** Supabase (Auth + PostgreSQL + Storage + Realtime)
- **Image Processing:** sharp (Gaussian blur)
- **Testing:** Vitest + Testing Library

## Getting Started

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Fill in NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server |
| `npm run build` | Production build |
| `npm test` | Run tests (watch mode) |
| `npx vitest run` | Run tests once |

## Project Structure

```
src/
├── app/
│   ├── api/onboarding/          # API routes (birth-data, rpv-test, photos, soul-report)
│   ├── login/                   # Login page
│   ├── register/                # Registration page
│   ├── onboarding/              # 4-step onboarding flow
│   │   ├── birth-data/          # Step 1: Birth data + data tier
│   │   ├── rpv-test/            # Step 2: RPV personality test
│   │   ├── photos/              # Step 3: Photo upload + blur
│   │   └── soul-report/         # Step 4: Archetype reveal
│   ├── daily/                   # Daily match feed (3 cards)
│   ├── connections/             # Active connections + chat
│   └── profile/                 # Self-view profile
├── lib/
│   ├── supabase/                # Supabase clients + types
│   │   ├── client.ts            # Browser client
│   │   ├── server.ts            # Server client (cookies)
│   │   ├── middleware.ts         # Session refresh
│   │   └── types.ts             # Database TypeScript types
│   ├── auth.ts                  # Auth functions (register/login/logout)
│   └── ai/
│       └── archetype.ts         # Soul archetype generator
├── middleware.ts                 # Auth guard
└── __tests__/                   # 33 tests across 7 files
    ├── auth.test.ts
    ├── login-page.test.tsx
    ├── register-page.test.tsx
    └── api/
        ├── onboarding-birth-data.test.ts
        ├── onboarding-rpv-test.test.ts
        ├── onboarding-photos.test.ts
        └── onboarding-soul-report.test.ts
```

## Database

Supabase PostgreSQL with 5 tables:

- **users** — Profile, birth data, RPV values, archetype, onboarding step
- **photos** — Original + blurred photo paths (Supabase Storage)
- **daily_matches** — 3 daily match cards per user
- **connections** — Matched pairs with sync level
- **messages** — Chat messages with auto-incrementing counters

All tables have Row Level Security (RLS) enabled.

## Onboarding Flow

1. **Birth Data** — Date, time precision, city → computes data tier (Gold/Silver/Bronze)
2. **RPV Test** — 3 binary questions mapping to conflict/power/energy preferences
3. **Photos** — Upload 2 photos → sharp Gaussian blur → Supabase Storage
4. **Soul Report** — Generates archetype from RPV values with base stats

## Environment Variables

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```
