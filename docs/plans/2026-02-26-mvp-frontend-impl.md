# DESTINY MVP Frontend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create `destiny-mvp/` — a standalone Next.js 16 app that transforms `astro-service/sandbox.html` into a user-facing platform with 3D tarot card UI, Google OAuth, and astro-service integration.

**Architecture:** New Next.js 16 App Router app at `destiny-mvp/` (repo root level). Shares the same Supabase project (`masninqgihbazjirweiy`) and astro-service (`http://localhost:8001`) as destiny-app. Uses dark mystic visual theme (purple/violet on deep black), matching sandbox.html's aesthetic rather than destiny-app's healing pink. MVP scope: Login → Run Synastry → View 3D Tarot Report.

**Tech Stack:** Next.js 16 App Router, TypeScript, Tailwind CSS v4, framer-motion (3D cards), @supabase/ssr, lucide-react

**Sandbox.html tabs → MVP pages mapping:**
- Tab A (伴侶驗證) + Tab D (合盤報告) → `/lounge` + `/report/[id]`
- Tab C (個人名片) → future `/profile` page (deferred)
- Tab B (校時模擬) → deferred

---

## Task 1: Scaffold `destiny-mvp/` Next.js App

**Files:**
- Create: `destiny-mvp/` (new Next.js app)

**Step 1: Scaffold from repo root**

```bash
cd "E:/下班自學用/destiny"
npx create-next-app@latest destiny-mvp --typescript --tailwind --app --no-src-dir --import-alias "@/*" --yes
```

**Step 2: Install additional dependencies**

```bash
cd "E:/下班自學用/destiny/destiny-mvp"
npm install @supabase/ssr @supabase/supabase-js framer-motion lucide-react clsx tailwind-merge class-variance-authority
```

**Step 3: Verify server starts**

```bash
npm run dev
```
Expected: `✓ Ready` on http://localhost:3000

**Step 4: Commit**

```bash
cd "E:/下班自學用/destiny"
git add destiny-mvp/
git commit -m "chore(mvp): scaffold destiny-mvp Next.js 16 app"
```

---

## Task 2: Supabase Client Setup + Environment

**Files:**
- Create: `destiny-mvp/.env.local`
- Create: `destiny-mvp/lib/supabase/client.ts`
- Create: `destiny-mvp/lib/supabase/server.ts`

**Step 1: Create .env.local** (copy values from `destiny-app/.env.local`)

```
NEXT_PUBLIC_SUPABASE_URL=https://masninqgihbazjirweiy.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<copy from destiny-app/.env.local>
ASTRO_SERVICE_URL=http://localhost:8001
```

**Step 2: Create `destiny-mvp/lib/supabase/client.ts`**

```typescript
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  )
}
```

**Step 3: Create `destiny-mvp/lib/supabase/server.ts`**

```typescript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function createClient() {
  const cookieStore = await cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {}
        },
      },
    }
  )
}
```

**Step 4: Commit**

```bash
git add destiny-mvp/lib/ destiny-mvp/.env.local
git commit -m "feat(mvp): Supabase client + environment setup"
```

---

## Task 3: DB Migration — soul_cards + matches Tables

**Files:**
- Create: `destiny-mvp/supabase/migrations/013_mvp_tables.sql`

**Step 1: Run this SQL in Supabase SQL Editor** (project `masninqgihbazjirweiy`)

```sql
-- Extend users with token balance (skip if already exists)
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS tokens INT DEFAULT 3;

-- Soul cards: cached natal chart per person-entry
CREATE TABLE IF NOT EXISTS public.soul_cards (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  birth_date   DATE NOT NULL,
  birth_time   TIME,
  lat          DECIMAL(9,6),
  lng          DECIMAL(9,6),
  timezone     TEXT,
  data_tier    SMALLINT DEFAULT 3 CHECK (data_tier IN (1,2,3)),
  gender       CHAR(1) CHECK (gender IN ('M','F')),
  natal_cache  JSONB,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.soul_cards ENABLE ROW LEVEL SECURITY;
CREATE POLICY "soul_cards_owner_all" ON public.soul_cards
  FOR ALL USING (auth.uid() = owner_id)
  WITH CHECK (auth.uid() = owner_id);

-- Matches: synastry results
CREATE TABLE IF NOT EXISTS public.mvp_matches (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name_a          TEXT,
  name_b          TEXT,
  harmony_score   INT,
  lust_score      INT,
  soul_score      INT,
  tracks          JSONB,
  labels          JSONB,
  report_json     JSONB,
  share_token     TEXT UNIQUE DEFAULT encode(gen_random_bytes(12), 'hex'),
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.mvp_matches ENABLE ROW LEVEL SECURITY;
CREATE POLICY "mvp_matches_owner_select" ON public.mvp_matches
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "mvp_matches_owner_insert" ON public.mvp_matches
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Public share policy (no auth required, read by share_token)
CREATE POLICY "mvp_matches_public_share" ON public.mvp_matches
  FOR SELECT USING (share_token IS NOT NULL);
```

**Step 2: Verify** — tables `soul_cards` and `mvp_matches` appear in Supabase Table Editor.

**Step 3: Save migration file**

Save the above SQL to `destiny-mvp/supabase/migrations/013_mvp_tables.sql`.

**Step 4: Commit**

```bash
git add destiny-mvp/supabase/
git commit -m "feat(mvp): DB migration — soul_cards + mvp_matches tables"
```

---

## Task 4: Dark Mystic Theme + Layout

**Files:**
- Modify: `destiny-mvp/app/globals.css`
- Modify: `destiny-mvp/app/layout.tsx`

**Step 1: Replace `globals.css` content**

```css
@import "tailwindcss";

:root {
  --bg: #0a0a0f;
  --surface: #111827;
  --surface-2: #1f2937;
  --border: #374151;
  --text: #e0dff8;
  --text-muted: #9ca3af;
  --text-dim: #6b7280;
  --primary: #7c3aed;
  --primary-light: #c084fc;
  --primary-dark: #6d28d9;
  --accent: #818cf8;
  --lust-color: #f472b6;
  --soul-color: #34d399;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

a { color: inherit; text-decoration: none; }

input, select {
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-family: inherit;
  outline: none;
}
input:focus, select:focus { border-color: var(--primary); }

button:disabled { opacity: 0.5; cursor: not-allowed; }
```

**Step 2: Update `destiny-mvp/app/layout.tsx`**

```tsx
import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'DESTINY — Match Source Codes',
  description: "We don't match faces. We match Source Codes.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-TW">
      <body>{children}</body>
    </html>
  )
}
```

**Step 3: Commit**

```bash
git commit -m "feat(mvp): dark mystic theme + root layout"
```

---

## Task 5: Login Page + Google OAuth

**Files:**
- Create: `destiny-mvp/app/login/page.tsx`
- Create: `destiny-mvp/app/auth/callback/route.ts`
- Create: `destiny-mvp/middleware.ts`

**Step 1: Create `app/login/page.tsx`**

```tsx
'use client'
import { createClient } from '@/lib/supabase/client'

export default function LoginPage() {
  async function handleGoogle() {
    const supabase = createClient()
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${location.origin}/auth/callback` },
    })
  }

  return (
    <main style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center',
      justifyContent: 'center', background: 'var(--bg)',
    }}>
      <div style={{
        background: 'var(--surface)', border: '1px solid var(--border)',
        borderRadius: 12, padding: 40, maxWidth: 400, width: '100%', textAlign: 'center',
      }}>
        {/* Logo */}
        <div style={{ fontSize: 28, marginBottom: 8 }}>✦</div>
        <h1 style={{ color: 'var(--primary-light)', fontSize: 22, letterSpacing: '4px', marginBottom: 8 }}>
          DESTINY
        </h1>
        <p style={{ color: 'var(--text-dim)', fontSize: 11, marginBottom: 32, lineHeight: 1.6 }}>
          We don&apos;t match faces.<br />We match Source Codes.
        </p>

        {/* Google OAuth button */}
        <button
          onClick={handleGoogle}
          style={{
            width: '100%', background: 'var(--primary)', color: '#fff',
            border: 'none', padding: '12px 24px', borderRadius: 8,
            fontSize: 13, cursor: 'pointer', letterSpacing: '1px',
            transition: 'background 0.2s',
          }}
          onMouseOver={e => (e.currentTarget.style.background = 'var(--primary-dark)')}
          onMouseOut={e => (e.currentTarget.style.background = 'var(--primary)')}
        >
          ▶ Continue with Google
        </button>

        <p style={{ color: 'var(--text-dim)', fontSize: 10, marginTop: 20 }}>
          登入即表示同意服務條款與隱私政策
        </p>
      </div>
    </main>
  )
}
```

**Step 2: Create `app/auth/callback/route.ts`**

```typescript
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')

  if (code) {
    const cookieStore = await cookies()
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll() { return cookieStore.getAll() },
          setAll(cs) {
            cs.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          },
        },
      }
    )
    await supabase.auth.exchangeCodeForSession(code)
  }

  return NextResponse.redirect(`${origin}/lounge`)
}
```

**Step 3: Create `middleware.ts`** (at `destiny-mvp/middleware.ts`)

```typescript
import { createServerClient } from '@supabase/ssr'
import { NextRequest, NextResponse } from 'next/server'

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return request.cookies.getAll() },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          response = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  const { data: { user } } = await supabase.auth.getUser()
  const path = request.nextUrl.pathname

  const isPublic = path.startsWith('/login') ||
    path.startsWith('/auth') ||
    path.startsWith('/share')

  if (!user && !isPublic) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return response
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
```

**Step 4: Enable Google OAuth in Supabase Dashboard**
- Authentication → Providers → Google → Enable
- Requires Google Cloud Console: create OAuth client, set redirect URI to
  `https://masninqgihbazjirweiy.supabase.co/auth/v1/callback`

**Step 5: Commit**

```bash
git commit -m "feat(mvp): login page + Google OAuth + middleware auth guard"
```

---

## Task 6: TarotCard 3D Flip Component

**Files:**
- Create: `destiny-mvp/components/TarotCard.tsx`

**Step 1: Write component**

```tsx
'use client'
import { useState } from 'react'
import { motion } from 'framer-motion'

interface TarotCardFront {
  archetype: string
  resonance: string[]
  vibeScore: number
  chemScore: number
}

interface TarotCardBack {
  shadow: string[]
  toxicTraps: string[]
  reportText: string
}

interface TarotCardProps {
  front: TarotCardFront
  back: TarotCardBack
}

export function TarotCard({ front, back }: TarotCardProps) {
  const [flipped, setFlipped] = useState(false)

  return (
    <div
      style={{ perspective: '1200px', width: 320, height: 500, cursor: 'pointer' }}
      onClick={() => setFlipped(f => !f)}
      aria-label={flipped ? '點擊查看正面' : '點擊查看陰暗面'}
    >
      <motion.div
        animate={{ rotateY: flipped ? 180 : 0 }}
        transition={{ duration: 0.65, ease: [0.43, 0.13, 0.23, 0.96] }}
        style={{ width: '100%', height: '100%', position: 'relative', transformStyle: 'preserve-3d' }}
      >
        {/* ── FRONT: Light Side ── */}
        <div style={{
          position: 'absolute', inset: 0, backfaceVisibility: 'hidden',
          background: 'linear-gradient(145deg, #1e1b4b 0%, #2d1b4e 100%)',
          border: '1px solid #4338ca', borderRadius: 16, padding: 24,
          display: 'flex', flexDirection: 'column', gap: 16,
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 10, color: 'var(--text-dim)', letterSpacing: '2px', marginBottom: 6 }}>
              RELATIONSHIP ARCHETYPE
            </div>
            <div style={{ fontSize: 18, color: 'var(--primary-light)', fontWeight: 'bold', letterSpacing: '1px' }}>
              {front.archetype}
            </div>
          </div>

          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 8, letterSpacing: '1px' }}>
              RESONANCE TAGS
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {front.resonance.map(tag => (
                <span key={tag} style={{
                  background: '#1e1b4b', color: '#a78bfa',
                  border: '1px solid #4338ca', padding: '2px 10px',
                  borderRadius: 12, fontSize: 11,
                }}>
                  {tag}
                </span>
              ))}
            </div>
          </div>

          <div>
            {([
              ['VibeScore', front.vibeScore, 'var(--lust-color)'],
              ['ChemistryScore', front.chemScore, 'var(--soul-color)'],
            ] as [string, number, string][]).map(([label, val, color]) => (
              <div key={label} style={{ marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>{label}</span>
                  <span style={{ fontSize: 14, fontWeight: 'bold', color }}>{val}</span>
                </div>
                <div style={{ background: 'var(--border)', borderRadius: 4, height: 6, overflow: 'hidden' }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${val}%` }}
                    transition={{ duration: 0.8, delay: 0.3 }}
                    style={{ height: '100%', background: color, borderRadius: 4 }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div style={{ textAlign: 'center', color: '#4b5563', fontSize: 10 }}>
            點擊翻面 → 查看陰暗面 ▼
          </div>
        </div>

        {/* ── BACK: Dark Side ── */}
        <div style={{
          position: 'absolute', inset: 0,
          backfaceVisibility: 'hidden', transform: 'rotateY(180deg)',
          background: 'linear-gradient(145deg, #1c0533 0%, #0f0a1e 100%)',
          border: '1px solid var(--primary)', borderRadius: 16, padding: 24,
          display: 'flex', flexDirection: 'column', gap: 14, overflow: 'hidden',
        }}>
          <div style={{ fontSize: 10, color: 'var(--primary-light)', letterSpacing: '2px' }}>
            ⚠ SHADOW DYNAMICS
          </div>

          <div>
            <div style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 6 }}>暗面標籤</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {back.shadow.map(tag => (
                <span key={tag} style={{
                  background: '#2d1b4e', color: 'var(--primary-light)',
                  border: '1px solid var(--primary)', padding: '2px 8px',
                  borderRadius: 10, fontSize: 10,
                }}>
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {back.toxicTraps.length > 0 && (
            <div>
              <div style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 6 }}>⚡ 絕對死穴</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {back.toxicTraps.map(trap => (
                  <span key={trap} style={{
                    background: '#450a0a', color: '#fca5a5',
                    border: '1px solid #dc2626', padding: '2px 8px',
                    borderRadius: 10, fontSize: 10,
                  }}>
                    {trap}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div style={{ flex: 1, overflowY: 'auto' }}>
            <div style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 6 }}>關係解析</div>
            <div style={{
              color: '#d1d5db', fontSize: 11, lineHeight: 1.7,
              background: '#0f172a', padding: 10, borderRadius: 6,
              borderLeft: '3px solid var(--primary)',
            }}>
              {back.reportText || '命運解析生成中...'}
            </div>
          </div>

          <div style={{ textAlign: 'center', color: '#4b5563', fontSize: 10 }}>
            ▲ 點擊翻面 → 查看正面
          </div>
        </div>
      </motion.div>
    </div>
  )
}
```

**Step 2: Verify** — import and render `<TarotCard />` in a test page; confirm it flips on click.

**Step 3: Commit**

```bash
git commit -m "feat(mvp): TarotCard 3D flip component (framer-motion)"
```

---

## Task 7: BirthInput Form Component

**Files:**
- Create: `destiny-mvp/components/BirthInput.tsx`

**Step 1: Write component**

```tsx
// components/BirthInput.tsx

export interface BirthData {
  name: string
  birth_date: string
  birth_time: string   // '' if unknown (triggers Tier 3)
  lat: number
  lng: number
  data_tier: 1 | 2 | 3
  gender: 'M' | 'F'
}

interface Props {
  label: 'A' | 'B'
  value: BirthData
  onChange: (v: BirthData) => void
}

const S = {
  card: { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8, padding: 16 } as React.CSSProperties,
  heading: { color: 'var(--accent)', fontSize: 12, marginBottom: 12, letterSpacing: '1px' } as React.CSSProperties,
  label: { display: 'block', color: 'var(--text-muted)', fontSize: 11, marginBottom: 2 } as React.CSSProperties,
  input: { width: '100%', marginBottom: 8 } as React.CSSProperties,
  grid2: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 8 } as React.CSSProperties,
}

export function BirthInput({ label, value, onChange }: Props) {
  const set = (k: keyof BirthData, v: string | number) =>
    onChange({ ...value, [k]: v })

  return (
    <div style={S.card}>
      <h3 style={S.heading}>PERSON {label}</h3>

      <label style={S.label}>顯示名稱</label>
      <input
        type="text" value={value.name} style={S.input}
        onChange={e => set('name', e.target.value)}
      />

      <label style={S.label}>出生日期</label>
      <input
        type="date" value={value.birth_date} style={S.input}
        onChange={e => set('birth_date', e.target.value)}
      />

      <label style={S.label}>出生時間（可留空 → Tier 3）</label>
      <input
        type="time" value={value.birth_time} style={S.input}
        onChange={e => set('birth_time', e.target.value)}
      />

      <div style={S.grid2}>
        <div>
          <label style={S.label}>緯度</label>
          <input
            type="number" value={value.lat} step="0.001"
            style={{ width: '100%' }}
            onChange={e => set('lat', parseFloat(e.target.value))}
          />
        </div>
        <div>
          <label style={S.label}>經度</label>
          <input
            type="number" value={value.lng} step="0.001"
            style={{ width: '100%' }}
            onChange={e => set('lng', parseFloat(e.target.value))}
          />
        </div>
      </div>

      <label style={S.label}>Data Tier</label>
      <select
        value={value.data_tier} style={S.input}
        onChange={e => set('data_tier', parseInt(e.target.value) as 1 | 2 | 3)}
      >
        <option value={1}>Tier 1 — 精確出生時間</option>
        <option value={2}>Tier 2 — 模糊時段</option>
        <option value={3}>Tier 3 — 只有日期</option>
      </select>

      <label style={S.label}>性別</label>
      <select
        value={value.gender} style={{ width: '100%' }}
        onChange={e => set('gender', e.target.value as 'M' | 'F')}
      >
        <option value="M">男（M）</option>
        <option value="F">女（F）</option>
      </select>
    </div>
  )
}
```

**Step 2: Commit**

```bash
git commit -m "feat(mvp): BirthInput form component"
```

---

## Task 8: Server-Side API Proxy Routes

**Files:**
- Create: `destiny-mvp/app/api/calculate-chart/route.ts`
- Create: `destiny-mvp/app/api/compute-match/route.ts`

These routes sit between the browser and astro-service, ensuring the raw natal data never leaves the server.

**Step 1: `app/api/calculate-chart/route.ts`**

```typescript
import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function POST(request: NextRequest) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const body = await request.json()
  const astroUrl = process.env.ASTRO_SERVICE_URL ?? 'http://localhost:8001'

  try {
    const res = await fetch(`${astroUrl}/calculate-chart`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`astro-service: ${res.status}`)
    return NextResponse.json(await res.json())
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : 'astro-service unavailable' },
      { status: 502 }
    )
  }
}
```

**Step 2: `app/api/compute-match/route.ts`**

```typescript
import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function POST(request: NextRequest) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const body = await request.json()
  const astroUrl = process.env.ASTRO_SERVICE_URL ?? 'http://localhost:8001'

  try {
    const res = await fetch(`${astroUrl}/compute-match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) throw new Error(`astro-service: ${res.status}`)
    return NextResponse.json(await res.json())
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : 'astro-service unavailable' },
      { status: 502 }
    )
  }
}
```

**Step 3: Verify** — with astro-service running, test:

```bash
curl -X POST http://localhost:3000/api/calculate-chart \
  -H "Content-Type: application/json" \
  -d '{"birth_date":"1990-03-15","birth_time":"14:30","lat":25.033,"lng":121.565,"data_tier":1}'
```
Expected: JSON with planetary positions.

**Step 4: Commit**

```bash
git commit -m "feat(mvp): server-side API proxy routes to astro-service"
```

---

## Task 9: Lounge Page — Main Hub

**Files:**
- Create: `destiny-mvp/app/lounge/page.tsx`

This is the platform equivalent of sandbox.html Tab A (伴侶驗證).

**Step 1: Write `app/lounge/page.tsx`**

```tsx
'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { BirthInput, type BirthData } from '@/components/BirthInput'
import { createClient } from '@/lib/supabase/client'

const DEFAULT_A: BirthData = {
  name: 'Person A', birth_date: '1990-03-15', birth_time: '14:30',
  lat: 25.033, lng: 121.565, data_tier: 1, gender: 'M',
}
const DEFAULT_B: BirthData = {
  name: 'Person B', birth_date: '1992-08-22', birth_time: '09:15',
  lat: 25.033, lng: 121.565, data_tier: 1, gender: 'F',
}

// Default RPV values (can be wired to a form in Phase 2)
const DEFAULT_RPV = { rpv_conflict: 'argue', rpv_power: 'follow', rpv_energy: 'home' }

export default function LoungePage() {
  const router = useRouter()
  const supabase = createClient()
  const [a, setA] = useState<BirthData>(DEFAULT_A)
  const [b, setB] = useState<BirthData>(DEFAULT_B)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  async function runMatch() {
    setLoading(true)
    setError('')
    setStatus('⟳ 運算星盤中...')

    try {
      // 1. Calculate charts (parallel)
      const buildChartPayload = (p: BirthData) => ({
        birth_date: p.birth_date,
        birth_time: p.birth_time || null,
        lat: p.lat,
        lng: p.lng,
        data_tier: p.data_tier,
      })

      const [chartA, chartB] = await Promise.all([
        fetch('/api/calculate-chart', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(buildChartPayload(a)),
        }).then(r => r.json()),
        fetch('/api/calculate-chart', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(buildChartPayload(b)),
        }).then(r => r.json()),
      ])

      if (chartA.error || chartB.error) {
        throw new Error(chartA.error ?? chartB.error)
      }

      setStatus('⟳ 解析命運共振...')

      // 2. Compute match
      const matchRes = await fetch('/api/compute-match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          person_a: { ...chartA, gender: a.gender, data_tier: a.data_tier, ...DEFAULT_RPV },
          person_b: { ...chartB, gender: b.gender, data_tier: b.data_tier, ...DEFAULT_RPV },
        }),
      }).then(r => r.json())

      if (matchRes.error) throw new Error(matchRes.error)

      setStatus('⟳ 儲存報告...')

      // 3. Save to DB
      const { data: { user } } = await supabase.auth.getUser()
      const { data: match, error: dbErr } = await supabase
        .from('mvp_matches')
        .insert({
          user_id: user!.id,
          name_a: a.name,
          name_b: b.name,
          harmony_score: Math.round(((matchRes.lust_score ?? 50) + (matchRes.soul_score ?? 50)) / 2),
          lust_score: Math.round(matchRes.lust_score ?? 50),
          soul_score: Math.round(matchRes.soul_score ?? 50),
          tracks: matchRes.tracks ?? {},
          labels: matchRes.labels ?? [],
          report_json: matchRes,
        })
        .select('id')
        .single()

      if (dbErr) throw new Error(dbErr.message)

      router.push(`/report/${match.id}`)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      setLoading(false)
      setStatus('')
    }
  }

  return (
    <main style={{ maxWidth: 920, margin: '0 auto', padding: 24 }}>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ color: 'var(--primary-light)', fontSize: 18, letterSpacing: '2px', marginBottom: 4 }}>
          ✦ DESTINY — 命運解析大廳
        </h1>
        <p style={{ color: 'var(--text-dim)', fontSize: 11 }}>
          輸入雙方生辰資料，解析命運共振
        </p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
        <BirthInput label="A" value={a} onChange={setA} />
        <BirthInput label="B" value={b} onChange={setB} />
      </div>

      {error && (
        <p style={{ color: '#fca5a5', fontSize: 11, marginBottom: 12 }}>
          ✕ {error}
        </p>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <button
          onClick={runMatch}
          disabled={loading}
          style={{
            background: loading ? 'var(--surface-2)' : 'var(--primary)',
            color: '#fff', border: 'none', padding: '10px 28px',
            borderRadius: 6, fontSize: 13, cursor: loading ? 'not-allowed' : 'pointer',
            letterSpacing: '1px', transition: 'background 0.2s',
          }}
        >
          {loading ? status || '⟳ 運算中...' : '✦ 解析命運'}
        </button>
      </div>
    </main>
  )
}
```

**Step 2: Commit**

```bash
git commit -m "feat(mvp): /lounge main hub page with two-person input + match trigger"
```

---

## Task 10: Report Page — 3D Tarot Card Display

**Files:**
- Create: `destiny-mvp/app/report/[id]/page.tsx`

Since the page needs both server data fetch AND the client-side TarotCard, split into a server component + client display component.

**Step 1: Create `app/report/[id]/ReportClient.tsx`** (client component)

```tsx
'use client'
import { TarotCard } from '@/components/TarotCard'

interface ReportClientProps {
  nameA: string
  nameB: string
  lust: number
  soul: number
  harmony: number
  tracks: Record<string, number>
  labels: string[]
  shadowTags: string[]
  toxicTraps: string[]
  archetype: string
  reportText: string
}

export function ReportClient({
  nameA, nameB, lust, soul, harmony, tracks,
  labels, shadowTags, toxicTraps, archetype, reportText,
}: ReportClientProps) {
  const trackItems = [
    { label: 'Friend', val: tracks.friend ?? 0, color: '#60a5fa' },
    { label: 'Passion', val: tracks.passion ?? 0, color: '#f472b6' },
    { label: 'Partner', val: tracks.partner ?? 0, color: '#34d399' },
    { label: 'Soul', val: tracks.soul ?? 0, color: '#c084fc' },
  ]

  return (
    <>
      {/* Title */}
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ color: 'var(--primary-light)', fontSize: 18, letterSpacing: '2px', marginBottom: 4 }}>
          ✦ 命運解析報告
        </h1>
        <p style={{ color: 'var(--text-dim)', fontSize: 11 }}>
          {nameA} × {nameB}
        </p>
      </div>

      {/* Score overview */}
      <div style={{
        background: 'var(--surface)', border: '1px solid var(--border)',
        borderRadius: 8, padding: 16, marginBottom: 24,
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12, textAlign: 'center' }}>
          {[
            { label: 'Harmony', val: harmony, color: 'var(--primary-light)' },
            { label: 'VibeScore', val: lust, color: 'var(--lust-color)' },
            { label: 'ChemScore', val: soul, color: 'var(--soul-color)' },
            ...trackItems,
          ].map(({ label, val, color }) => (
            <div key={label}>
              <div style={{ fontSize: 10, color: 'var(--text-dim)', marginBottom: 4 }}>{label}</div>
              <div style={{ fontSize: 20, fontWeight: 'bold', color }}>{Math.round(val)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Labels */}
      {labels.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 20 }}>
          {labels.map(tag => (
            <span key={tag} style={{
              background: '#1e1b4b', color: '#a78bfa',
              border: '1px solid #4338ca', padding: '2px 10px',
              borderRadius: 12, fontSize: 11,
            }}>
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* 3D Tarot Card */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 24 }}>
        <TarotCard
          front={{ archetype, resonance: labels.slice(0, 5), vibeScore: lust, chemScore: soul }}
          back={{ shadow: shadowTags, toxicTraps, reportText }}
        />
      </div>

      <p style={{ textAlign: 'center', color: 'var(--text-dim)', fontSize: 10 }}>
        點擊卡片翻面查看陰暗面分析
      </p>
    </>
  )
}
```

**Step 2: Create `app/report/[id]/page.tsx`** (server component)

```tsx
import { createClient } from '@/lib/supabase/server'
import { notFound } from 'next/navigation'
import { ReportClient } from './ReportClient'

export default async function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const supabase = await createClient()

  const { data: match, error } = await supabase
    .from('mvp_matches')
    .select('*')
    .eq('id', id)
    .single()

  if (error || !match) notFound()

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const r = (match.report_json ?? {}) as Record<string, any>
  const tracks = (match.tracks ?? {}) as Record<string, number>
  const labels = (match.labels ?? []) as string[]

  return (
    <main style={{ maxWidth: 920, margin: '0 auto', padding: 24 }}>
      <ReportClient
        nameA={match.name_a ?? 'A'}
        nameB={match.name_b ?? 'B'}
        lust={match.lust_score ?? 50}
        soul={match.soul_score ?? 50}
        harmony={match.harmony_score ?? 50}
        tracks={tracks}
        labels={labels}
        archetype={r.archetype ?? '神秘原型'}
        shadowTags={(r.shadow_tags ?? []) as string[]}
        toxicTraps={(r.toxic_traps ?? []) as string[]}
        reportText={r.report_text ?? ''}
      />
    </main>
  )
}
```

**Step 3: Test**
- Run match from lounge → should redirect to `/report/[id]`
- Verify scores display + tarot card flips

**Step 4: Commit**

```bash
git commit -m "feat(mvp): /report/[id] page with 3D TarotCard display"
```

---

## Task 11: Navigation + Root Redirect

**Files:**
- Modify: `destiny-mvp/app/page.tsx`
- Create: `destiny-mvp/components/NavBar.tsx`
- Modify: `destiny-mvp/app/layout.tsx`

**Step 1: Root redirect**

```tsx
// app/page.tsx
import { redirect } from 'next/navigation'
export default function Home() { redirect('/lounge') }
```

**Step 2: NavBar component**

```tsx
// components/NavBar.tsx
'use client'
import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

export function NavBar() {
  const router = useRouter()
  const pathname = usePathname()

  // Don't show nav on login / auth pages
  if (pathname.startsWith('/login') || pathname.startsWith('/auth')) return null

  async function logout() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
  }

  return (
    <nav style={{
      background: 'var(--surface)', borderBottom: '1px solid var(--border)',
      padding: '10px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    }}>
      <Link href="/lounge" style={{ color: 'var(--primary-light)', fontSize: 14, letterSpacing: '2px' }}>
        ✦ DESTINY
      </Link>
      <button
        onClick={logout}
        style={{
          background: 'none', border: '1px solid var(--border)', color: 'var(--text-muted)',
          padding: '4px 12px', borderRadius: 4, cursor: 'pointer', fontSize: 11,
        }}
      >
        登出
      </button>
    </nav>
  )
}
```

**Step 3: Add NavBar to layout**

```tsx
// app/layout.tsx
import type { Metadata } from 'next'
import './globals.css'
import { NavBar } from '@/components/NavBar'

export const metadata: Metadata = {
  title: 'DESTINY — Match Source Codes',
  description: "We don't match faces. We match Source Codes.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-TW">
      <body>
        <NavBar />
        {children}
      </body>
    </html>
  )
}
```

**Step 4: Commit**

```bash
git commit -m "feat(mvp): NavBar + root redirect to /lounge"
```

---

## Task 12: End-to-End Smoke Test

**Step 1: Start all services**

```bash
# Terminal 1 — astro-service
cd "E:/下班自學用/destiny/astro-service"
uvicorn main:app --port 8001

# Terminal 2 — destiny-mvp
cd "E:/下班自學用/destiny/destiny-mvp"
npm run dev
```

**Step 2: Test the full journey**

1. Open http://localhost:3000 → should redirect to `/login`
2. Click "Continue with Google" → complete OAuth flow → lands on `/lounge`
3. Fill in birth data for two people (leave defaults if needed)
4. Click "✦ 解析命運"
5. Wait for loading → should redirect to `/report/[uuid]`
6. Verify: scores display, tarot card renders, clicking flips to dark side

**Step 3: Verify DB** — check Supabase Table Editor → `mvp_matches` has a new row.

**Step 4: Final commit**

```bash
git commit -m "chore(mvp): e2e smoke test passed — MVP v1 complete"
```

---

## Deferred (Phase 2+)

These items from the dev plan are **not** in this MVP implementation:

| Feature | Dev Plan Section | Priority |
|---------|-----------------|----------|
| Token system (3 tokens, deduction RPC) | §3, §5.2 | Phase 2 |
| Survey → earn token | §6.3 | Phase 2 |
| Share page `/share/[token]` | §6.2 | Phase 2 |
| Streaming report (打字機效果) | §5.2 | Phase 2 |
| Tab C: Personal card (single person) | sandbox Tab C | Phase 2 |
| Tab B: Birth time rectification | sandbox Tab B | Phase 3 |
| OG image + IG share | §6.1 | Phase 3 |
| Referral code | §6.3 | Phase 3 |
| Location autocomplete (Google Places) | §4.2 | Phase 3 |

---

## File Structure After Completion

```
destiny-mvp/
├── app/
│   ├── api/
│   │   ├── calculate-chart/route.ts
│   │   └── compute-match/route.ts
│   ├── auth/callback/route.ts
│   ├── login/page.tsx
│   ├── lounge/page.tsx
│   ├── report/[id]/
│   │   ├── page.tsx           (server component)
│   │   └── ReportClient.tsx   (client component)
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx               (redirect → /lounge)
├── components/
│   ├── BirthInput.tsx
│   ├── NavBar.tsx
│   └── TarotCard.tsx
├── lib/supabase/
│   ├── client.ts
│   └── server.ts
├── supabase/migrations/
│   └── 013_mvp_tables.sql
├── middleware.ts
├── .env.local
└── package.json
```

---

## 後續待做事項（Backlog）

### 分享功能 — Phase 2

目前 `/report/[id]` 只有「複製連結」按鈕（需登入才能查看）。

**待做：公開分享頁 `/share/[id]`**

- 建立 `/app/share/[id]/page.tsx` — 無需登入的公開只讀報告頁
- `middleware.ts` 的 auth guard 加入 `/share/*` 例外（已預留）
- 從 `mvp_matches` 讀取資料時不驗證 user_id（只讀，RLS 可設 public select）
- 在 `/report/[id]` 報告頁加入「生成分享頁」按鈕，呼叫 API 將該筆記錄標記為 `is_public = true`
- Supabase migration：`mvp_matches` 加 `is_public boolean DEFAULT false`
- 分享頁顯示簡化版報告（分數 + 原型 + 暗影動態），不顯示開發者 PromptPreviewPanel
