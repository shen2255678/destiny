import { NextResponse } from 'next/server'
import { createClient, createAdminClient } from '@/lib/supabase/server'

export async function GET() {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  // Fetch all non-expired connections for this user
  const { data: connections, error } = await supabase
    .from('connections')
    .select('*')
    .or(`user_a_id.eq.${user.id},user_b_id.eq.${user.id}`)
    .neq('status', 'expired')
    .order('last_activity', { ascending: false })

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  if (!connections || connections.length === 0) {
    return NextResponse.json({ connections: [] })
  }

  const admin = createAdminClient()

  // Collect other user IDs and match IDs
  const otherUserIds = connections.map((c) =>
    c.user_a_id === user.id ? c.user_b_id : c.user_a_id
  )
  const matchIds = connections.map((c) => c.match_id).filter(Boolean)

  // Fetch other users, matches, and photos in parallel
  const [usersRes, matchesRes, photosRes] = await Promise.all([
    admin.from('users').select('id, archetype_name, display_name').in('id', otherUserIds),
    matchIds.length > 0
      ? admin.from('daily_matches').select('id, tags, total_score').in('id', matchIds)
      : Promise.resolve({ data: [] }),
    admin.from('photos').select('user_id, blurred_path').in('user_id', otherUserIds).eq('upload_order', 1),
  ])

  const usersMap = new Map((usersRes.data ?? []).map((u: any) => [u.id, u]))
  const matchesMap = new Map((matchesRes.data ?? []).map((m: any) => [m.id, m]))

  // Build signed URLs for blurred photos
  const photoSignedUrls = new Map<string, string>()
  for (const photo of photosRes.data ?? []) {
    const { data: signed } = await admin.storage.from('photos').createSignedUrl(photo.blurred_path, 3600)
    if (signed?.signedUrl) photoSignedUrls.set(photo.user_id, signed.signedUrl)
  }

  // Assemble response
  const result = connections.map((c) => {
    const otherId = c.user_a_id === user.id ? c.user_b_id : c.user_a_id
    const match = matchesMap.get(c.match_id)
    return {
      id: c.id,
      status: c.status,
      sync_level: c.sync_level,
      message_count: c.message_count,
      last_activity: c.last_activity,
      tags: match?.tags ?? [],
      other_user: usersMap.get(otherId) ?? { id: otherId, archetype_name: null, display_name: null },
      blurred_photo_url: photoSignedUrls.get(otherId) ?? null,
    }
  })

  return NextResponse.json({ connections: result })
}
