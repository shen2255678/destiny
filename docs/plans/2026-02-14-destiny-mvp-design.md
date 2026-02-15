# Project DESTINY - MVP Phase 1 Design Document

**Date:** 2026-02-14
**Status:** Approved
**Author:** Haowei + Claude

---

## 1. Overview

DESTINY is a precision matchmaking platform combining Vedic Astrology, Attachment Psychology, and Power Dynamics for deep compatibility matching.

**Slogan:** "We don't match faces, we match Source Codes."

**MVP Goal:** Validate the core loop: Data Ingestion -> Algorithm Matching -> Interaction Verification

### MVP Scope (IN)

- User registration & onboarding ("Soul Checkup")
- Birth data collection + astrology chart calculation
- Simplified RPV test (3 questions)
- Photo upload with Gaussian blur
- Daily Destiny: 3 daily match cards with dynamic tags + radar chart
- Dual blind selection (Accept / Pass)
- Simplified ice-breaker (1 scenario question, results update tags only)
- Progressive unlock chat (Lv.1 text -> Lv.2 50% photo -> Lv.3 full unlock)
- 24-hour inactivity auto-disconnect
- Chameleon Tagging System (AI-generated relative tags)
- Self-view profile (positive Base Stats + Archetype only)

### MVP Scope (OUT)

- Bounty Mode (Phase 2)
- Voice recording / voice print (Phase 2)
- Social credit system (Phase 2)
- Oracle Mode paid features (Phase 2)
- Dasha filtering (Phase 2)
- AI Wingman / relationship predictor in chat (Phase 2)
- Native mobile apps (Phase 3)

---

## 2. Architecture

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

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14+ (App Router), React, TypeScript |
| Styling | Tailwind CSS |
| UI Components | shadcn/ui |
| Charts | Recharts or Nivo (radar chart) |
| Animation | Framer Motion |
| Auth | Supabase Auth |
| Database | Supabase PostgreSQL |
| Storage | Supabase Storage (photos) |
| Realtime | Supabase Realtime (chat) |
| Astrology Engine | Python + FastAPI + swisseph |
| AI/LLM | Claude API or OpenAI API |
| Image Processing | sharp (Node.js, Gaussian blur) |
| Python Hosting | Railway or Fly.io |
| Frontend Hosting | Vercel |
| Design Tool | Google Stitch |

---

## 3. Database Schema

### users

```sql
CREATE TABLE users (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email           TEXT UNIQUE NOT NULL,
  gender          TEXT NOT NULL,
  birth_date      DATE NOT NULL,
  birth_time      TEXT,                    -- 'precise' | 'morning' | 'afternoon' | 'unknown'
  birth_time_exact TIME,
  birth_city      TEXT NOT NULL,
  birth_lat       DECIMAL(9,6),
  birth_lng       DECIMAL(9,6),
  data_tier       INT DEFAULT 3,           -- 3=Bronze 2=Silver 1=Gold

  -- RPV test results
  rpv_conflict    TEXT,                    -- 'cold_war' | 'argue'
  rpv_power       TEXT,                    -- 'control' | 'follow'
  rpv_energy      TEXT,                    -- 'home' | 'out'

  -- Chart parameters (calculated by Python)
  sun_sign        TEXT,
  moon_sign       TEXT,
  venus_sign      TEXT,
  mars_sign       TEXT,
  saturn_sign     TEXT,
  ascendant_sign  TEXT,

  -- Derived psychological parameters
  attachment_style TEXT,                   -- 'anxious' | 'avoidant' | 'secure' | 'disorganized'
  power_dynamic   TEXT,                    -- 'dominant' | 'submissive' | 'switch'
  energy_level    INT,
  element_primary TEXT,                    -- 'fire' | 'earth' | 'air' | 'water'

  -- Profile
  archetype_name  TEXT,
  archetype_desc  TEXT,

  -- Onboarding status
  onboarding_step TEXT DEFAULT 'birth_data', -- 'birth_data' | 'rpv_test' | 'photos' | 'complete'

  created_at      TIMESTAMPTZ DEFAULT NOW(),
  updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### photos

```sql
CREATE TABLE photos (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
  storage_path    TEXT NOT NULL,
  blurred_path    TEXT NOT NULL,
  half_blurred_path TEXT,
  upload_order    INT NOT NULL,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### daily_matches

```sql
CREATE TABLE daily_matches (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID REFERENCES users(id),
  matched_user_id UUID REFERENCES users(id),
  match_date      DATE NOT NULL,

  -- Score breakdown
  kernel_score    DECIMAL(4,2),
  power_score     DECIMAL(4,2),
  glitch_score    DECIMAL(4,2),
  total_score     DECIMAL(4,2),
  match_type      TEXT,                    -- 'complementary' | 'similar' | 'tension'

  -- Chameleon tags (AI-generated, relative to viewer)
  tags            JSONB,
  radar_passion   INT,
  radar_stability INT,
  radar_communication INT,

  -- Card visual
  card_color      TEXT,                    -- 'coral' | 'blue' | 'purple'

  -- User actions
  user_action     TEXT DEFAULT 'pending',  -- 'pending' | 'accept' | 'pass'

  created_at      TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(user_id, matched_user_id, match_date)
);
```

### connections

```sql
CREATE TABLE connections (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_a_id       UUID REFERENCES users(id),
  user_b_id       UUID REFERENCES users(id),
  match_id        UUID REFERENCES daily_matches(id),

  -- Ice-breaker
  icebreaker_question TEXT,
  user_a_answer   TEXT,
  user_b_answer   TEXT,
  icebreaker_tags JSONB,

  -- Sync rate
  sync_level      INT DEFAULT 1,
  message_count   INT DEFAULT 0,
  call_duration   INT DEFAULT 0,

  -- Status
  status          TEXT DEFAULT 'icebreaker', -- 'icebreaker' | 'active' | 'expired'
  last_activity   TIMESTAMPTZ DEFAULT NOW(),

  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

### messages

```sql
CREATE TABLE messages (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  connection_id   UUID REFERENCES connections(id) ON DELETE CASCADE,
  sender_id       UUID REFERENCES users(id),
  content         TEXT NOT NULL,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. API Design

### Auth & Onboarding

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register via Supabase Auth |
| POST | /api/onboarding/birth-data | Save birth data, trigger Python chart calculation |
| POST | /api/onboarding/rpv-test | Save RPV 3-question results |
| POST | /api/onboarding/photos | Upload 2 photos, auto Gaussian blur via sharp |
| GET | /api/onboarding/soul-report | Return AI-generated Archetype + Base Stats |

### Daily Destiny

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/matches/daily | Get today's 3 match cards |
| POST | /api/matches/:id/action | Submit Accept or Pass |

### Connections

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/connections | List all active connections |
| GET | /api/connections/:id | Connection detail with sync level |
| POST | /api/connections/:id/icebreaker-answer | Submit ice-breaker answer |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/connections/:id/messages | Get messages (paginated) |
| POST | /api/connections/:id/messages | Send a message |

### Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/profile/me | Self-view: Base Stats + Archetype |

---

## 5. Core Algorithms

### Match Score Formula

```
Match_Score = (Kernel_Compatibility * 0.5) + (Power_Dynamic_Fit * 0.3) + (Glitch_Tolerance * 0.2)
```

### Match Types

| Type | Logic | Recommended For |
|------|-------|----------------|
| Complementary | Earth+Water / Fire+Air | Long-term relationships |
| Similar | Same element pairing | Partnerships |
| Tension | Fixed+Fixed signs | Short-term / high chemistry |

### Chameleon Tagging System

Tags are **relative, not absolute**. Generated at runtime via `Function(User_A, User_B)`.

**Generation flow:**
1. Python calculates raw compatibility scores
2. Next.js API Route sends both users' attributes to AI
3. AI generates 3 positive/neutral tags from A's perspective of B
4. Tags stored in `daily_matches.tags` as JSONB

**Rules:**
- Only positive or neutral labels shown
- Never show: negative labels, raw S/M data, relative weakness
- Same user shows different tags to different viewers

### Self-View (Filtered)

Users see only:
- Base Stats: Passion / Stability / Intellect (Lv.1-10)
- Archetype name + description (positive framing)
- Never: relative tags, S/M raw scores, negative labels

### Data Integrity Tiers

| Tier | Data Provided | Algorithm Access |
|------|--------------|-----------------|
| 3 (Bronze) | Birth date only | Sun, Mercury, Venus, Mars only |
| 2 (Silver) | Fuzzy time (morning/afternoon) | + fuzzy Moon, approximate houses |
| 1 (Gold) | Precise birth time | Full D1+D9 charts, S/M deep matching |

---

## 6. Progressive Unlock System

| Level | Trigger | Unlocked Features |
|-------|---------|------------------|
| Lv.1 | 0-10 message rounds | Text chat only, blurred photos |
| Lv.2 | 10-50 message rounds | 50% clear photos, voice call |
| Lv.3 | 50+ rounds OR 3+ min call | Full HD photos, exchange contacts |

**Auto-disconnect:** 24 hours of inactivity -> connection status = 'expired'

Implemented via PostgreSQL trigger on `messages` table insert:
- Increment `connections.message_count`
- Update `connections.last_activity`
- Check and update `connections.sync_level`

---

## 7. AI Integration Points

| Feature | When Called | Prompt Input | Output |
|---------|-----------|-------------|--------|
| Archetype Generation | Onboarding complete | User's chart + RPV results | Archetype name + description |
| Chameleon Tags | Daily match generation | Both users' attributes | 3 relative tags + card color |
| Ice-breaker Question | Connection created | Both users' chart + power dynamic | 1 scenario question with options |
| Ice-breaker Result Tags | Both users answer | Question + both answers | Updated relationship tags |

---

## 8. Frontend Structure

### Page Routes (Next.js App Router)

```
app/
├── (auth)/
│   ├── login/page.tsx
│   └── register/page.tsx
├── (onboarding)/
│   ├── birth-data/page.tsx        # Soul Checkup Step 1
│   ├── rpv-test/page.tsx          # Soul Checkup Step 2
│   ├── photos/page.tsx            # Soul Checkup Step 3
│   └── soul-report/page.tsx       # Archetype reveal
├── (main)/
│   ├── daily/page.tsx             # Daily Destiny cards
│   ├── connections/page.tsx       # Connection list
│   └── connections/[id]/page.tsx  # Chat room with sync meter
├── profile/page.tsx               # Self-view profile
└── api/                           # API Routes (server-side)
```

### UI Style: Dark Mystic Tarot (Healing)

```
Colors:
  Background:     #13111C (deep purple-black)
  Surface:        #1E1B2E (card background)
  Primary:        #8B7EC8 (lavender purple)
  Gold Accent:    #C4A882 (warm gold sand)
  Secondary:      #6B5B95 (deep purple)
  Moonlight:      #E8D5B7 (moon cream)
  Text Primary:   #E8E0D8 (warm off-white)
  Text Secondary: #9590A8 (muted purple-gray)

  Card Borders (by match type):
    Passion:   #C97B7B (dark coral)
    Stability: #7BA3C9 (calm blue)
    Tension:   #9B7BC9 (purple)

Typography:
  Chinese: Noto Serif TC (classical feel)
  English: Cormorant Garamond (tarot card aesthetic)

Visual Elements:
  - Zodiac symbols, moon phase icons
  - Tarot-card-style card frames (rounded + fine line decorations)
  - Soft gradient radar charts
  - Micro-animations: star twinkle, card flip (Framer Motion)

Component Library: shadcn/ui
  - Card, Button, Input, Dialog, ScrollArea
  - Avatar, Progress, Badge
  - All themed with Tailwind to match dark mystic palette
```

### Design Workflow

1. Haowei designs in Google Stitch (layout, colors, elements)
2. Development implements designs using Tailwind + shadcn/ui
3. Framer Motion for transitions and micro-interactions

---

## 9. Python Microservice

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /calculate-chart | Calculate natal chart from birth data |
| POST | /run-daily-matching | Cron job: generate daily matches for all users |

### Tech

- **Framework:** FastAPI
- **Astrology:** swisseph (Swiss Ephemeris Python binding)
- **Hosting:** Railway or Fly.io
- **Schedule:** Cron job at 21:00 daily

### Chart Calculation Output

```json
{
  "sun_sign": "capricorn",
  "moon_sign": "cancer",
  "venus_sign": "aquarius",
  "mars_sign": "aries",
  "saturn_sign": "pisces",
  "ascendant_sign": "virgo",
  "element_primary": "earth",
  "data_tier": 1
}
```

### Daily Matching Flow

1. Fetch all active users from Supabase
2. For each user, compute `Match_Score` against eligible candidates
3. Exclude: already matched pairs, previously passed
4. Select top 3 matches
5. Write to `daily_matches` table
6. Trigger Next.js API (webhook) to generate AI tags for each pair

---

## 10. Success Metrics

| Metric | What It Validates |
|--------|------------------|
| Blind Match Rate | % of users who Accept without seeing photos |
| Conversation Retention | % of pairs reaching Lv.2 (photo unlock) |
| User NPS | Post-unlock satisfaction: "surprise" vs "disappointment" |

---

## 11. MVP Execution Notes

1. **No payments** — MVP is free, collect data to calibrate algorithm
2. **No complex animations** — Dark mystic feel, functional UI, minimal but atmospheric
3. **Seed users** — Recruit from spiritual communities, investor groups, engineer forums
4. **Design-first** — UI designed in Google Stitch before development
