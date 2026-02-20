import { NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase/server'

const ASTRO_URL = process.env.ASTRO_SERVICE_URL || 'http://localhost:8001'
const CRON_SECRET = process.env.CRON_SECRET || ''

// Profile fields needed for matching
const USER_MATCH_FIELDS = [
  'id', 'data_tier',
  'sun_sign', 'moon_sign', 'venus_sign', 'mars_sign', 'saturn_sign', 'ascendant_sign',
  'bazi_element',
  'rpv_conflict', 'rpv_power', 'rpv_energy',
].join(', ')

interface UserProfile {
  id: string
  data_tier: number
  sun_sign: string | null
  moon_sign: string | null
  venus_sign: string | null
  mars_sign: string | null
  saturn_sign: string | null
  ascendant_sign: string | null
  bazi_element: string | null
  rpv_conflict: string | null
  rpv_power: string | null
  rpv_energy: string | null
}

interface MatchResult {
  kernel_score: number
  power_score: number
  glitch_score: number
  total_score: number
  match_type: 'complementary' | 'similar' | 'tension'
  radar_passion: number
  radar_stability: number
  radar_communication: number
  card_color: string
  tags: string[]
}

async function callComputeMatch(userA: UserProfile, userB: UserProfile): Promise<MatchResult | null> {
  try {
    const res = await fetch(`${ASTRO_URL}/compute-match`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_a: userA, user_b: userB }),
    })
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}

/**
 * Select 3 matches per user: one per type (complementary/similar/tension).
 * If a type is missing, fills with next highest score.
 */
function selectTopMatches(
  scored: Array<{ candidate: UserProfile; result: MatchResult }>
): Array<{ candidate: UserProfile; result: MatchResult }> {
  const byType: Record<string, Array<{ candidate: UserProfile; result: MatchResult }>> = {
    complementary: [],
    similar: [],
    tension: [],
  }

  for (const item of scored) {
    byType[item.result.match_type]?.push(item)
  }

  // Sort each type bucket by total_score descending
  for (const type of Object.keys(byType)) {
    byType[type].sort((a, b) => b.result.total_score - a.result.total_score)
  }

  const selected: Array<{ candidate: UserProfile; result: MatchResult }> = []
  const used = new Set<string>()

  // Pick one from each type first
  for (const type of ['complementary', 'tension', 'similar']) {
    const bucket = byType[type]
    const pick = bucket.find(item => !used.has(item.candidate.id))
    if (pick) {
      selected.push(pick)
      used.add(pick.candidate.id)
    }
  }

  // Fill remaining slots with highest remaining scores
  if (selected.length < 3) {
    const allSorted = [...scored].sort((a, b) => b.result.total_score - a.result.total_score)
    for (const item of allSorted) {
      if (selected.length >= 3) break
      if (!used.has(item.candidate.id)) {
        selected.push(item)
        used.add(item.candidate.id)
      }
    }
  }

  return selected.slice(0, 3)
}

export async function POST(request: Request) {
  // Guard: require CRON_SECRET header (skip check if secret not configured)
  if (CRON_SECRET) {
    const authHeader = request.headers.get('authorization')
    if (authHeader !== `Bearer ${CRON_SECRET}`) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
  }

  const admin = createAdminClient()
  const today = new Date().toISOString().slice(0, 10) // "YYYY-MM-DD"

  // 1. Fetch all users who have completed onboarding
  const { data: users, error: usersError } = await admin
    .from('users')
    .select(USER_MATCH_FIELDS)
    .eq('onboarding_step', 'complete')

  if (usersError) {
    return NextResponse.json({ error: usersError.message }, { status: 500 })
  }

  if (!users || users.length < 2) {
    return NextResponse.json({ message: 'Not enough users for matching', matched: 0 })
  }

  const profiles = users as UserProfile[]

  // 2. For each user, compute scores against all other users
  let totalInserted = 0

  for (const user of profiles) {
    // Skip users who already have matches today
    const { count } = await admin
      .from('daily_matches')
      .select('id', { count: 'exact', head: true })
      .eq('user_id', user.id)
      .eq('match_date', today)

    if ((count ?? 0) >= 3) continue // already matched today

    // Collect other users
    const candidates = profiles.filter(p => p.id !== user.id)

    // Compute scores in parallel (batch size to avoid overloading)
    const scored: Array<{ candidate: UserProfile; result: MatchResult }> = []

    for (const candidate of candidates) {
      const result = await callComputeMatch(user, candidate)
      if (result) {
        scored.push({ candidate, result })
      }
    }

    if (scored.length === 0) continue

    // 3. Select top 3
    const picks = selectTopMatches(scored)

    // 4. Insert into daily_matches
    const rows = picks.map(({ candidate, result }) => ({
      user_id: user.id,
      matched_user_id: candidate.id,
      match_date: today,
      kernel_score: result.kernel_score,
      power_score: result.power_score,
      glitch_score: result.glitch_score,
      total_score: result.total_score,
      match_type: result.match_type,
      tags: result.tags,
      radar_passion: result.radar_passion,
      radar_stability: result.radar_stability,
      radar_communication: result.radar_communication,
      card_color: result.card_color,
      user_action: 'pending',
    }))

    const { error: insertError } = await admin
      .from('daily_matches')
      .upsert(rows, { onConflict: 'user_id,matched_user_id,match_date', ignoreDuplicates: true })

    if (!insertError) totalInserted += rows.length
  }

  return NextResponse.json({ message: 'Daily matching complete', inserted: totalInserted, date: today })
}
