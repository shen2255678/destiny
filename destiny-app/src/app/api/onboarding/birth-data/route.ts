import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

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
  // Direct match
  if (TAIWAN_CITIES[city]) return TAIWAN_CITIES[city]
  // Partial match: check if city name contains any key
  for (const [key, coords] of Object.entries(TAIWAN_CITIES)) {
    if (city.includes(key) || key.includes(city)) return coords
  }
  return null
}

function computeDataTier(birthTime: string): number {
  if (birthTime === 'precise') return 1
  if (birthTime === 'morning' || birthTime === 'afternoon' || birthTime === 'evening') return 2
  return 3
}

export async function POST(request: Request) {
  const body = await request.json()
  const { birth_date, birth_time, birth_time_exact, birth_city, birth_lat, birth_lng } = body

  if (!birth_date || !birth_time || !birth_city) {
    return NextResponse.json(
      { error: 'Missing required fields: birth_date, birth_time, birth_city' },
      { status: 400 }
    )
  }

  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  const data_tier = computeDataTier(birth_time)

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
        gender: 'male', // will be set from registration, placeholder for upsert
        birth_date,
        birth_time,
        birth_time_exact: birth_time_exact || null,
        birth_city,
        birth_lat: lat,
        birth_lng: lng,
        data_tier,
        onboarding_step: 'rpv_test',
      },
      { onConflict: 'id' }
    )
    .select()
    .single()

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  // Call astro-service to calculate natal chart and write signs back to DB
  const astroUrl = process.env.ASTRO_SERVICE_URL || 'http://localhost:8001'
  try {
    const chartRes = await fetch(`${astroUrl}/calculate-chart`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        birth_date,
        birth_time,
        birth_time_exact: birth_time_exact || null,
        lat: lat ?? 25.033,
        lng: lng ?? 121.565,
        data_tier,
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
        })
        .eq('id', user.id)
    }
  } catch {
    // Astro service unavailable — signs stay null, non-blocking
    console.warn('[birth-data] astro-service unreachable, skipping chart calculation')
  }

  // Re-fetch to include chart data in response
  const { data: updated } = await supabase
    .from('users')
    .select('*')
    .eq('id', user.id)
    .single()

  return NextResponse.json({ data: updated })
}
