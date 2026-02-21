import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import type { AccuracyType } from '@/lib/supabase/types'

// Taiwan city coordinates for astrology chart calculation
const TAIWAN_CITIES: Record<string, { lat: number; lng: number }> = {
  '台北': { lat: 25.0330, lng: 121.5654 },
  '台北市': { lat: 25.0330, lng: 121.5654 },
  '新北': { lat: 25.0120, lng: 121.4657 },
  '新北市': { lat: 25.0120, lng: 121.4657 },
  '桃園': { lat: 24.9936, lng: 121.3010 },
  '桃園市': { lat: 24.9936, lng: 121.3010 },
  '台中': { lat: 24.1477, lng: 120.6736 },
  '台中市': { lat: 24.1477, lng: 120.6736 },
  '台南': { lat: 22.9998, lng: 120.2269 },
  '台南市': { lat: 22.9998, lng: 120.2269 },
  '高雄': { lat: 22.6273, lng: 120.3014 },
  '高雄市': { lat: 22.6273, lng: 120.3014 },
  '基隆': { lat: 25.1276, lng: 121.7392 },
  '基隆市': { lat: 25.1276, lng: 121.7392 },
  '新竹': { lat: 24.8138, lng: 120.9675 },
  '新竹市': { lat: 24.8138, lng: 120.9675 },
  '新竹縣': { lat: 24.8387, lng: 121.0178 },
  '嘉義': { lat: 23.4801, lng: 120.4491 },
  '嘉義市': { lat: 23.4801, lng: 120.4491 },
  '嘉義縣': { lat: 23.4518, lng: 120.2551 },
  '苗栗': { lat: 24.5602, lng: 120.8214 },
  '苗栗縣': { lat: 24.5602, lng: 120.8214 },
  '彰化': { lat: 24.0518, lng: 120.5161 },
  '彰化縣': { lat: 24.0518, lng: 120.5161 },
  '南投': { lat: 23.9609, lng: 120.6847 },
  '南投縣': { lat: 23.9609, lng: 120.6847 },
  '雲林': { lat: 23.7092, lng: 120.4313 },
  '雲林縣': { lat: 23.7092, lng: 120.4313 },
  '屏東': { lat: 22.6820, lng: 120.4844 },
  '屏東縣': { lat: 22.6820, lng: 120.4844 },
  '宜蘭': { lat: 24.7570, lng: 121.7533 },
  '宜蘭縣': { lat: 24.7570, lng: 121.7533 },
  '花蓮': { lat: 23.9910, lng: 121.6017 },
  '花蓮縣': { lat: 23.9910, lng: 121.6017 },
  '台東': { lat: 22.7583, lng: 121.1444 },
  '台東縣': { lat: 22.7583, lng: 121.1444 },
  '澎湖': { lat: 23.5711, lng: 119.5793 },
  '澎湖縣': { lat: 23.5711, lng: 119.5793 },
  '金門': { lat: 24.4493, lng: 118.3767 },
  '金門縣': { lat: 24.4493, lng: 118.3767 },
  '連江': { lat: 26.1505, lng: 119.9499 },
  '連江縣': { lat: 26.1505, lng: 119.9499 },
  '馬祖': { lat: 26.1505, lng: 119.9499 },
}

function lookupCityCoords(city: string): { lat: number; lng: number } | null {
  if (TAIWAN_CITIES[city]) return TAIWAN_CITIES[city]
  for (const [key, coords] of Object.entries(TAIWAN_CITIES)) {
    if (city.includes(key) || key.includes(city)) return coords
  }
  return null
}

// ---------------------------------------------------------------------------
// Rectification helpers
// ---------------------------------------------------------------------------

type FuzzyPeriod = 'morning' | 'afternoon' | 'evening' | 'unknown'

const FUZZY_WINDOWS: Record<FuzzyPeriod, { start: string; end: string; size: number; legacy: string }> = {
  morning:   { start: '06:00', end: '12:00', size: 360,  legacy: 'morning' },
  afternoon: { start: '12:00', end: '18:00', size: 360,  legacy: 'afternoon' },
  evening:   { start: '18:00', end: '24:00', size: 360,  legacy: 'evening' },
  unknown:   { start: '00:00', end: '24:00', size: 1440, legacy: 'unknown' },
}

interface RectificationDefaults {
  accuracy_type: AccuracyType
  current_confidence: number
  window_size_minutes: number
  window_start: string | null
  window_end: string | null
  birth_time: string
  data_tier: number
}

function computeRectification(
  accuracyType: AccuracyType,
  birthTimeExact: string | null,
  windowStart: string | null,
  windowEnd: string | null,
  fuzzyPeriod: string | null,
): RectificationDefaults {
  switch (accuracyType) {
    case 'PRECISE':
      return {
        accuracy_type: 'PRECISE',
        current_confidence: 0.90,
        window_size_minutes: 0,
        window_start: birthTimeExact,
        window_end: birthTimeExact,
        birth_time: 'precise',
        data_tier: 1,
      }
    case 'TWO_HOUR_SLOT':
      return {
        accuracy_type: 'TWO_HOUR_SLOT',
        current_confidence: 0.30,
        window_size_minutes: 120,
        window_start: windowStart,
        window_end: windowEnd,
        birth_time: 'unknown', // no legacy equivalent; use unknown as fallback
        data_tier: 2,
      }
    case 'FUZZY_DAY': {
      const period = (fuzzyPeriod as FuzzyPeriod) || 'unknown'
      const pw = FUZZY_WINDOWS[period] ?? FUZZY_WINDOWS.unknown
      return {
        accuracy_type: 'FUZZY_DAY',
        current_confidence: period === 'unknown' ? 0.05 : 0.15,
        window_size_minutes: pw.size,
        window_start: pw.start,
        window_end: pw.end,
        birth_time: pw.legacy,
        data_tier: period === 'unknown' ? 3 : 2,
      }
    }
  }
}

/** Legacy mapping: convert old birth_time to accuracy_type. */
function legacyToAccuracyType(birthTime: string): { accuracyType: AccuracyType; fuzzyPeriod: string | null } {
  if (birthTime === 'precise') return { accuracyType: 'PRECISE', fuzzyPeriod: null }
  const period = ['morning', 'afternoon', 'evening', 'unknown'].includes(birthTime) ? birthTime : 'unknown'
  return { accuracyType: 'FUZZY_DAY', fuzzyPeriod: period }
}

function computeDataTier(birthTime: string): number {
  if (birthTime === 'precise') return 1
  if (birthTime === 'morning' || birthTime === 'afternoon' || birthTime === 'evening') return 2
  return 3
}

// ---------------------------------------------------------------------------
// Route handler
// ---------------------------------------------------------------------------

export async function POST(request: Request) {
  const body = await request.json()
  const {
    birth_date,
    birth_city,
    birth_lat,
    birth_lng,
    // New accuracy_type system
    accuracy_type,
    fuzzy_period,
    window_start: bodyWindowStart,
    window_end: bodyWindowEnd,
    // Legacy system
    birth_time: legacyBirthTime,
    birth_time_exact,
  } = body

  // Require birth_date, birth_city, and at least one of accuracy_type or birth_time
  if (!birth_date || !birth_city || (!accuracy_type && !legacyBirthTime)) {
    return NextResponse.json(
      { error: 'Missing required fields: birth_date, birth_city, and accuracy_type or birth_time' },
      { status: 400 }
    )
  }

  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  // Resolve accuracy_type (new system takes priority over legacy)
  let rectData: RectificationDefaults
  if (accuracy_type) {
    rectData = computeRectification(accuracy_type, birth_time_exact || null, bodyWindowStart || null, bodyWindowEnd || null, fuzzy_period || null)
  } else {
    // Backward compat: derive from legacy birth_time
    const { accuracyType, fuzzyPeriod } = legacyToAccuracyType(legacyBirthTime)
    rectData = computeRectification(accuracyType, birth_time_exact || null, null, null, fuzzyPeriod)
    // Keep legacy data_tier for backward compat
    rectData.data_tier = computeDataTier(legacyBirthTime)
  }

  // Auto-lookup coordinates for Taiwan cities if not provided
  let lat = birth_lat || null
  let lng = birth_lng || null
  if (!lat || !lng) {
    const coords = lookupCityCoords(birth_city)
    if (coords) {
      lat = coords.lat
      lng = coords.lng
    }
  }

  const { data, error } = await supabase
    .from('users')
    .upsert(
      {
        id: user.id,
        email: user.email!,
        gender: 'male',
        birth_date,
        birth_time: rectData.birth_time,
        birth_time_exact: birth_time_exact || null,
        birth_city,
        birth_lat: lat,
        birth_lng: lng,
        data_tier: rectData.data_tier,
        accuracy_type: rectData.accuracy_type,
        window_start: rectData.window_start,
        window_end: rectData.window_end,
        window_size_minutes: rectData.window_size_minutes,
        rectification_status: 'collecting_signals',
        current_confidence: rectData.current_confidence,
        onboarding_step: 'rpv_test',
      },
      { onConflict: 'id' }
    )
    .select()
    .single()

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  // Log range_initialized event (non-blocking)
  supabase.from('rectification_events').insert({
    user_id: user.id,
    source: 'signup',
    event_type: 'range_initialized',
    payload: {
      accuracy_type: rectData.accuracy_type,
      window_start: rectData.window_start,
      window_end: rectData.window_end,
      window_size_minutes: rectData.window_size_minutes,
      initial_confidence: rectData.current_confidence,
    },
  }).catch(() => {
    console.warn('[birth-data] failed to log range_initialized event')
  })

  // Call astro-service to calculate natal chart (non-blocking)
  const astroUrl = process.env.ASTRO_SERVICE_URL || 'http://localhost:8001'
  try {
    const chartRes = await fetch(`${astroUrl}/calculate-chart`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        birth_date,
        birth_time: rectData.birth_time,
        birth_time_exact: birth_time_exact || null,
        lat: lat ?? 25.033,
        lng: lng ?? 121.565,
        data_tier: rectData.data_tier,
      }),
    })

    if (chartRes.ok) {
      const chart = await chartRes.json()
      await supabase
        .from('users')
        .update({
          sun_sign: chart.sun_sign ?? null,
          moon_sign: chart.moon_sign ?? null,
          venus_sign: chart.venus_sign ?? null,
          mars_sign: chart.mars_sign ?? null,
          saturn_sign: chart.saturn_sign ?? null,
          ascendant_sign: chart.ascendant_sign ?? null,
          element_primary: chart.element_primary ?? null,
          bazi_day_master: chart.bazi?.day_master ?? null,
          bazi_element: chart.bazi?.day_master_element ?? null,
          bazi_four_pillars: chart.bazi ?? null,
          // Phase G new chart fields
          mercury_sign:  chart.mercury_sign ?? null,
          jupiter_sign:  chart.jupiter_sign ?? null,
          pluto_sign:    chart.pluto_sign ?? null,
          uranus_sign:   chart.uranus_sign ?? null,
          neptune_sign:  chart.neptune_sign ?? null,
          chiron_sign:   chart.chiron_sign ?? null,
          juno_sign:     chart.juno_sign ?? null,
          house4_sign:   chart.house4_sign ?? null,
          house8_sign:   chart.house8_sign ?? null,
          house12_sign:  chart.house12_sign ?? null,
          // Phase H v1.4/v1.5 fields
          bazi_month_branch:  chart.bazi?.bazi_month_branch ?? null,
          bazi_day_branch:    chart.bazi?.bazi_day_branch ?? null,
          emotional_capacity: chart.emotional_capacity ?? 50,
        })
        .eq('id', user.id)
    }
  } catch {
    console.warn('[birth-data] astro-service unreachable, skipping chart calculation')
  }

  // Non-blocking ZWDS computation for Tier 1 / PRECISE users
  if (rectData.data_tier === 1 && rectData.accuracy_type === 'PRECISE') {
    const astroServiceUrl = process.env.ASTRO_SERVICE_URL ?? 'http://localhost:8001'
    try {
      // Parse birth_year, birth_month, birth_day from birth_date (YYYY-MM-DD)
      const [birthYear, birthMonth, birthDay] = birth_date.split('-').map(Number)
      const zwdsRes = await fetch(`${astroServiceUrl}/compute-zwds-chart`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          birth_year: birthYear,
          birth_month: birthMonth,
          birth_day: birthDay,
          birth_time: birth_time_exact || null,
          gender: 'M',
        }),
      })
      if (zwdsRes.ok) {
        const { chart } = await zwdsRes.json()
        if (chart) {
          await supabase.from('users').update({
            zwds_life_palace_stars:   chart.palaces?.ming?.main_stars ?? [],
            zwds_spouse_palace_stars: chart.palaces?.spouse?.main_stars ?? [],
            zwds_karma_palace_stars:  chart.palaces?.karma?.main_stars ?? [],
            zwds_four_transforms:     chart.four_transforms ?? null,
            zwds_five_element:        chart.five_element ?? null,
            zwds_body_palace_name:    chart.body_palace_name ?? null,
          }).eq('id', user.id)
        }
      }
    } catch {
      // Non-blocking: ZWDS failure never blocks onboarding
    }
  }

  // Re-fetch to include chart data in response
  const { data: updated } = await supabase
    .from('users')
    .select('*')
    .eq('id', user.id)
    .single()

  return NextResponse.json({ data: updated ?? data })
}
