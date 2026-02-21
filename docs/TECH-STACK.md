# DESTINY — Tech Stack & Architecture Reference

**Last Updated:** 2026-02-21 (Phase H ✅ — Three-System Algorithm)

---

## Architecture Overview

```
+--------------------------------------------------+
|  Next.js 16 (Vercel)                             |
|  +-- React Pages (App Router)                    |
|  +-- API Routes (Server-side)                    |
|       +-- AI API calls (Claude / Gemini)         |
|       +-- Archetype / profile card generation    |
|       +-- Image processing (sharp)               |
+--------------------------------------------------+
           |                    |
           v                    v
+--------------------+  +------------------------------+
|  Supabase          |  |  Python Astro Service        |
|  +-- Auth          |  |  (FastAPI, port 8001)        |
|  +-- PostgreSQL    |  |  +-- Swiss Ephemeris (swisseph)
|  +-- Storage       |  |  +-- BaZi 八字四柱 (bazi.py) |
|  +-- Realtime      |  |  +-- ZWDS 紫微斗數 (zwds.py) |
+--------------------+  |  +-- Synastry (zwds_synastry)|
           ^             |  +-- Match v2 (matching.py) |
           |             +------------------------------+
           |                         |
           +-------------------------+
             (ZWDS fields written back on Tier 1 onboarding)
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 16 (App Router) | React SSR + Static pages |
| Language | TypeScript | Type safety |
| Styling | Tailwind CSS v4 | Utility-first CSS |
| UI Components | shadcn/ui | Card, Button, Input, Dialog, etc. |
| Icons | Material Symbols Outlined | Google icon font |
| Auth | Supabase Auth | Email/password |
| Database | Supabase PostgreSQL | 6 tables + ZWDS fields |
| Storage | Supabase Storage | Photo blobs |
| Realtime | Supabase Realtime | Chat WebSocket |
| Western Astrology | Python + FastAPI + swisseph | Swiss Ephemeris 星盤計算 |
| BaZi 八字 | Python (`bazi.py`) | Four Pillars + true solar time |
| ZWDS 紫微斗數 | Python (`zwds.py`, `zwds_synastry.py`) | 12-palace chart + synastry |
| Calendar | lunardate (Python) | Solar → lunar calendar conversion |
| AI/LLM | Claude API / Google Gemini | Archetype / profile card / match report |
| Image Processing | sharp (Node.js) | Gaussian blur pipeline |
| Python Hosting | Railway / Fly.io | FastAPI microservice |
| Frontend Hosting | Vercel | Next.js deployment |

---

## Database Schema

| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `users` | birth_date, rpv_*, sun_sign, moon_sign, attachment_style, archetype_name, **zwds_life_palace_stars, zwds_spouse_palace_stars, zwds_karma_palace_stars, zwds_four_transforms, zwds_five_element, zwds_body_palace_name, zwds_defense_triggers** | User profile + chart data |
| `photos` | storage_path, blurred_path, half_blurred_path | Original + blurred photo paths |
| `daily_matches` | user_id, matched_user_id, total_score, tags (JSONB), radar_* | Daily 3 match cards |
| `connections` | user_a_id, user_b_id, sync_level, message_count, status | Active pairings |
| `messages` | connection_id, sender_id, content | Chat messages |
| `rectification_events` | user_id, event_type, question_id, window_* | Via Negativa 校時事件 |

**Migrations applied:** 001–008 (all pushed to remote Supabase)

### ZWDS columns on `users` (Migration 008)

| Column | Type | Description |
|---|---|---|
| `zwds_life_palace_stars` | `TEXT[]` | 命宮主星 |
| `zwds_spouse_palace_stars` | `TEXT[]` | 夫妻宮主星 |
| `zwds_karma_palace_stars` | `TEXT[]` | 福德宮主星 |
| `zwds_four_transforms` | `JSONB` | 四化：化祿/化権/化科/化忌 |
| `zwds_five_element` | `TEXT` | 五行局（如「火六局」） |
| `zwds_body_palace_name` | `TEXT` | 身宮名稱 |
| `zwds_defense_triggers` | `TEXT[]` | 煞星防禦機制 |

---

## Three-System Match Algorithm

The compatibility engine in `astro-service/matching.py` integrates three
independent astrology systems:

```
System 1: Western Astrology  — sign-level aspects (6 planets + ASC)
System 2: BaZi Five Elements — day master generation / restriction
System 3: ZWDS               — life palace archetypes + flying stars
                               (Tier 1 only, multiplicative modifier)
```

**Track modifier formula (ZWDS integration):**

```python
track_final = track_raw × (0.70 × zwds_mod + 0.30)
```

ZWDS contributes at most 70% of the modifier weight. Western + BaZi
retain a guaranteed 30% baseline.

**Legacy formula (still used for `daily_matches` seed scores):**

```
Match_Score = (Kernel_Compatibility × 0.5) + (Power_Dynamic_Fit × 0.3)
            + (Glitch_Tolerance × 0.2)
```

---

## Data Integrity Tiers

| Tier | User Provides | Algorithm Access | ZWDS |
|------|--------------|-----------------|------|
| 1 (Gold) | Precise birth time | Full chart + all houses | ✅ Full 3-system |
| 2 (Silver) | Fuzzy time (period) | No ASC / House signs | ❌ Skipped |
| 3 (Bronze) | Birth date only | Sun + slow planets only | ❌ Skipped |

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

| Feature | Endpoint | Model | Output |
|---------|----------|-------|--------|
| Archetype report | `/generate-archetype` | Claude Haiku / Gemini | 3 tags + 150-char report |
| Profile card | `/generate-profile-card` | Claude Haiku / Gemini | headline, tags, bio |
| Match report | `/generate-match-report` | Claude Haiku / Gemini | title, sparks, advice |

All three endpoints support both `provider: "anthropic"` and
`provider: "gemini"` with a `gemini_model` override field.

---

## Python Astro Service Structure

```
astro-service/
├── main.py               # FastAPI server (port 8001) + sandbox endpoints
├── chart.py              # Western astrology: planets → zodiac signs
├── bazi.py               # BaZi 八字: Four Pillars + true solar time + season
├── zwds.py               # ZWDS 紫微斗數: 12-palace chart engine
├── zwds_synastry.py      # ZWDS synastry: flying stars + archetypes + defense
├── matching.py           # compute_match_v2: three-system integration
├── sandbox.html          # Algorithm Validation Sandbox UI
├── test_chart.py         # pytest (30 tests)
├── test_matching.py      # pytest (101 tests)
├── test_zwds.py          # pytest (31 tests)
└── requirements.txt      # fastapi, uvicorn, pyswisseph, lunardate, anthropic, google-genai
```

---

## Next.js App Structure

```
destiny-app/
├── src/app/
│   ├── login/, register/
│   ├── onboarding/         # 4-step onboarding (birth-data → rpv → photos → soul-report)
│   ├── daily/              # Daily match feed
│   ├── connections/        # Connection list + chat rooms
│   ├── profile/
│   └── api/
│       ├── onboarding/     # birth-data, rpv-test, photos, soul-report
│       ├── matches/        # daily, action
│       ├── connections/    # list, [id]/messages
│       └── rectification/  # next-question, answer
├── src/lib/
│   ├── supabase/           # client.ts, server.ts, middleware.ts, types.ts
│   └── auth.ts
├── src/__tests__/          # 91 Vitest tests (14 files)
└── supabase/migrations/    # 001–008 migrations
```
