import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { createAdminClient } from '@/lib/supabase/admin'

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB

function validateFile(file: File, label: string): string | null {
  if (!ALLOWED_TYPES.includes(file.type)) {
    return `${label}: Invalid file type. Only JPEG, PNG, and WebP are accepted.`
  }
  if (file.size > MAX_FILE_SIZE) {
    return `${label}: File too large. Maximum size is 10MB.`
  }
  return null
}

export async function POST(request: Request) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  const formData = await request.formData()
  const photo1 = formData.get('photo1') as File | null
  const photo2 = formData.get('photo2') as File | null

  if (!photo1 || !photo2) {
    return NextResponse.json(
      { error: 'Both photo1 and photo2 are required' },
      { status: 400 }
    )
  }

  // Validate all files before processing
  for (const [label, file] of [['Photo 1', photo1], ['Photo 2', photo2]] as const) {
    const error = validateFile(file, label)
    if (error) {
      return NextResponse.json({ error }, { status: 400 })
    }
  }

  // Use admin client for storage & DB (bypasses RLS, auth already verified above)
  const admin = createAdminClient()

  const photos = [photo1, photo2]
  const photoRecords = []

  for (let i = 0; i < photos.length; i++) {
    const file = photos[i]
    const buffer = Buffer.from(await file.arrayBuffer())
    const slot = i + 1

    // Upload photo
    const storagePath = `${user.id}/photo_${slot}.jpg`
    const { error: uploadError } = await admin.storage
      .from('photos')
      .upload(storagePath, buffer, { contentType: 'image/jpeg', upsert: true })

    if (uploadError) {
      return NextResponse.json({ error: `Upload failed: ${uploadError.message}` }, { status: 500 })
    }

    photoRecords.push({
      user_id: user.id,
      upload_order: slot,
      storage_path: storagePath,
      blurred_path: storagePath,
    })
  }

  // Insert photo records
  const { data: insertedPhotos, error: insertError } = await admin
    .from('photos')
    .upsert(photoRecords, { onConflict: 'user_id,upload_order' })
    .select()

  if (insertError) {
    return NextResponse.json({ error: insertError.message }, { status: 500 })
  }

  // Update onboarding step
  await admin
    .from('users')
    .update({ onboarding_step: 'soul_report' })
    .eq('id', user.id)

  return NextResponse.json({ data: insertedPhotos })
}
