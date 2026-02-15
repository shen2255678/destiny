import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { createAdminClient } from '@/lib/supabase/admin'

// Taiwan city coordinates (shared with birth-data API)
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

function computeDataTier(birthTime: string): number {
  if (birthTime === 'precise') return 1
  if (birthTime === 'morning' || birthTime === 'afternoon' || birthTime === 'evening') return 2
  return 3
}

export async function GET() {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  const { data, error } = await supabase
    .from('users')
    .select('display_name, gender, birth_date, birth_time, birth_time_exact, birth_city, data_tier, rpv_conflict, rpv_power, rpv_energy, sun_sign, moon_sign, venus_sign, archetype_name, archetype_desc, bio, interest_tags')
    .eq('id', user.id)
    .single()

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  // Fetch photos with signed URLs
  const { data: photos } = await supabase
    .from('photos')
    .select('id, storage_path, blurred_path, upload_order')
    .eq('user_id', user.id)
    .order('upload_order')

  const photosWithUrls = []
  if (photos && photos.length > 0) {
    const admin = createAdminClient()
    for (const photo of photos) {
      const { data: signedData } = await admin.storage
        .from('photos')
        .createSignedUrl(photo.storage_path, 3600) // 1 hour
      photosWithUrls.push({
        ...photo,
        photo_url: signedData?.signedUrl || null,
      })
    }
  }

  return NextResponse.json({ data: { ...data, photos: photosWithUrls } })
}

const ALLOWED_FIELDS = [
  'display_name',
  'birth_date', 'birth_time', 'birth_time_exact', 'birth_city',
  'rpv_conflict', 'rpv_power', 'rpv_energy',
  'bio', 'interest_tags',
] as const

export async function PATCH(request: Request) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  const body = await request.json()

  // Filter to allowed fields only
  const updates: Record<string, unknown> = {}
  for (const field of ALLOWED_FIELDS) {
    if (field in body) {
      updates[field] = body[field]
    }
  }

  if (Object.keys(updates).length === 0) {
    return NextResponse.json({ error: 'No valid fields to update' }, { status: 400 })
  }

  // Recalculate data_tier if birth_time changed
  if (updates.birth_time) {
    updates.data_tier = computeDataTier(updates.birth_time as string)
  }

  // Re-lookup city coordinates if birth_city changed
  if (updates.birth_city) {
    const coords = lookupCityCoords(updates.birth_city as string)
    if (coords) {
      updates.birth_lat = coords.lat
      updates.birth_lng = coords.lng
    }
  }

  const { data, error } = await supabase
    .from('users')
    .update(updates)
    .eq('id', user.id)
    .select()
    .single()

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json({ data })
}
