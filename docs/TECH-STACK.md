# DESTINY — Tech Stack & Architecture Reference

**Last Updated:** 2026-02-15

---

## Architecture Overview

```
+--------------------------------------------------+
|  Next.js 14+ (Vercel)                            |
|  +-- React Pages (App Router)                    |
|  +-- API Routes (Server-side)                    |
|       +-- AI API calls (Claude / OpenAI)         |
|       +-- Chameleon tag generation               |
|       +-- Ice-breaker question generation        |
|       +-- Archetype generation                   |
|       +-- Image processing (sharp)               |
+--------------------------------------------------+
           |                    |
           v                    v
+--------------------+  +--------------------+
|  Supabase          |  |  Python Service     |
|  +-- Auth          |  |  (FastAPI)          |
|  +-- PostgreSQL    |  |  +-- Swiss Ephemeris|
|  +-- Storage       |  |  +-- Match Algorithm|
|  +-- Realtime      |  |  +-- Daily Cron Job |
+--------------------+  +--------------------+
                              |
                              v
                        Supabase DB
                        (writes match results)
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 16 (App Router) | React SSR + Static pages |
| Language | TypeScript | Type safety |
| Styling | Tailwind CSS v4 | Utility-first CSS |
| UI Components | shadcn/ui | Card, Button, Input, Dialog, etc. |
| Charts | Recharts / Nivo | Radar chart (激情/穩定/溝通) |
| Animation | Framer Motion | Micro-interactions |
| Icons | Material Symbols Outlined | Google icon font |
| Auth | Supabase Auth | Email/password + OAuth |
| Database | Supabase PostgreSQL | 5 tables |
| Storage | Supabase Storage | Photo blobs |
| Realtime | Supabase Realtime | Chat WebSocket |
| Astrology | Python + FastAPI + swisseph | Swiss Ephemeris 星盤計算 |
| AI/LLM | Claude API / OpenAI API | Tag/archetype generation |
| Image Processing | sharp (Node.js) | Gaussian blur pipeline |
| Python Hosting | Railway / Fly.io | FastAPI microservice |
| Frontend Hosting | Vercel | Next.js deployment |

---

## Database Schema (5 Tables)

| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `users` | birth_date, rpv_*, sun_sign, moon_sign, attachment_style, power_dynamic, archetype_name | User profile + chart data |
| `photos` | storage_path, blurred_path, half_blurred_path | Original + blurred photo paths |
| `daily_matches` | user_id, matched_user_id, total_score, tags (JSONB), radar_*, user_action | Daily 3 match cards |
| `connections` | user_a_id, user_b_id, sync_level, message_count, status | Active pairings |
| `messages` | connection_id, sender_id, content | Chat messages |

Full SQL definitions: see `docs/plans/2026-02-14-destiny-mvp-design.md` Section 3.

---

## Match Algorithm

```
Match_Score = (Kernel_Compatibility × 0.5) + (Power_Dynamic_Fit × 0.3) + (Glitch_Tolerance × 0.2)
```

| Match Type | Logic | Use Case |
|-----------|-------|----------|
| Complementary (互補型) | Earth+Water / Fire+Air | Long-term |
| Similar (相似型) | Same element pairing | Partnership |
| Tension (張力型) | Fixed+Fixed signs | High chemistry |

---

## Data Integrity Tiers

| Tier | User Provides | Algorithm Access |
|------|--------------|-----------------|
| 3 (Bronze) | Birth date only | Sun, Mercury, Venus, Mars |
| 2 (Silver) | Fuzzy time (morning/afternoon) | + fuzzy Moon, approximate houses |
| 1 (Gold) | Precise birth time | Full D1+D9 charts, deep matching |

---

## Progressive Unlock System

| Level | Trigger | Unlocks |
|-------|---------|---------|
| Lv.1 | 0-10 messages | Text only, blurred photos |
| Lv.2 | 10-50 messages | 50% clear photos, voice call |
| Lv.3 | 50+ messages OR 3min call | Full HD photos, exchange contacts |

24hr inactivity → auto-disconnect.

---

## AI Integration Points

| Feature | Trigger | Input | Output |
|---------|---------|-------|--------|
| Archetype Generation | Onboarding complete | Chart + RPV | Archetype name + description |
| Chameleon Tags | Daily match generation | Both users' attributes | 3 relative tags + card color |
| Ice-breaker Question | Connection created | Both users' data | 1 scenario question |
| Ice-breaker Result Tags | Both users answer | Question + answers | Updated tags |

---

## Project Structure

```
destiny-app/
├── src/app/
│   ├── page.tsx                          # Landing page
│   ├── layout.tsx                        # Root layout (Inter font, Material Icons)
│   ├── globals.css                       # Tailwind v4 theme + DESTINY tokens
│   ├── login/page.tsx                    # Login
│   ├── register/page.tsx                 # Register
│   ├── onboarding/
│   │   ├── layout.tsx                    # Onboarding shell + progress bar
│   │   ├── StepIndicator.tsx             # Step progress component
│   │   ├── page.tsx                      # Redirect → birth-data
│   │   ├── birth-data/page.tsx           # Step 1
│   │   ├── rpv-test/page.tsx             # Step 2
│   │   ├── photos/page.tsx               # Step 3
│   │   └── soul-report/page.tsx          # Step 4
│   ├── daily/page.tsx                    # Daily Feed (3 match cards)
│   ├── connections/
│   │   ├── page.tsx                      # Connections list
│   │   └── [id]/page.tsx                 # Chat room
│   ├── profile/page.tsx                  # Self-view profile
│   └── api/                             # (待建立) API Routes
├── src/components/ui/                    # shadcn/ui components
│   ├── card.tsx, button.tsx, badge.tsx
│   ├── progress.tsx, avatar.tsx
│   ├── scroll-area.tsx, dialog.tsx, input.tsx
│   └── ...
└── docs/
    ├── plans/2026-02-14-destiny-mvp-design.md  # MVP design doc
    ├── MVP-PROGRESS.md                          # Progress tracker
    └── TECH-STACK.md                            # This file
```
