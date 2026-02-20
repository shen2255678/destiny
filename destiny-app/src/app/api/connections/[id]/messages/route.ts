import { NextResponse } from 'next/server'
import { createClient, createAdminClient } from '@/lib/supabase/server'

type RouteContext = { params: Promise<{ id: string }> }

/** GET /api/connections/:id/messages — connection detail + message history */
export async function GET(_req: Request, { params }: RouteContext) {
  const { id: connectionId } = await params

  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  // Fetch connection and verify membership
  const { data: connection, error: connError } = await supabase
    .from('connections')
    .select('*')
    .eq('id', connectionId)
    .single()

  if (connError || !connection) {
    return NextResponse.json({ error: 'Connection not found' }, { status: 404 })
  }

  if (connection.user_a_id !== user.id && connection.user_b_id !== user.id) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  // Fetch messages (newest 50, ordered ascending for display)
  const { data: rawMessages, error: msgError } = await supabase
    .from('messages')
    .select('*')
    .eq('connection_id', connectionId)
    .order('created_at', { ascending: true })
    .limit(50)

  if (msgError) {
    return NextResponse.json({ error: msgError.message }, { status: 500 })
  }

  const messages = (rawMessages ?? []).map((m) => ({
    ...m,
    is_self: m.sender_id === user.id,
  }))

  // Fetch other user info and match tags
  const admin = createAdminClient()
  const otherId = connection.user_a_id === user.id ? connection.user_b_id : connection.user_a_id

  const [otherUserRes, matchRes, photoRes] = await Promise.all([
    admin.from('users').select('id, archetype_name, display_name').eq('id', otherId).single(),
    connection.match_id
      ? admin.from('daily_matches').select('id, tags').eq('id', connection.match_id).single()
      : Promise.resolve({ data: null }),
    admin.from('photos').select('blurred_path').eq('user_id', otherId).eq('upload_order', 1).single(),
  ])

  let blurredPhotoUrl: string | null = null
  if (photoRes.data?.blurred_path) {
    const { data: signed } = await admin.storage.from('photos').createSignedUrl(photoRes.data.blurred_path, 3600)
    blurredPhotoUrl = signed?.signedUrl ?? null
  }

  return NextResponse.json({
    connection: {
      id: connection.id,
      status: connection.status,
      sync_level: connection.sync_level,
      message_count: connection.message_count,
      last_activity: connection.last_activity,
      tags: matchRes.data?.tags ?? [],
      other_user: otherUserRes.data ?? { id: otherId, archetype_name: null, display_name: null },
      blurred_photo_url: blurredPhotoUrl,
    },
    messages,
  })
}

/** POST /api/connections/:id/messages — send a text message */
export async function POST(req: Request, { params }: RouteContext) {
  const { id: connectionId } = await params

  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()
  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  const body = await req.json()
  const { content } = body

  if (!content?.trim()) {
    return NextResponse.json({ error: 'content is required' }, { status: 400 })
  }

  // Verify membership
  const { data: connection } = await supabase
    .from('connections')
    .select('user_a_id, user_b_id')
    .eq('id', connectionId)
    .single()

  if (!connection || (connection.user_a_id !== user.id && connection.user_b_id !== user.id)) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  // Insert message — DB trigger auto-updates message_count + sync_level + last_activity
  const { data: message, error: insertError } = await supabase
    .from('messages')
    .insert({ connection_id: connectionId, sender_id: user.id, content: content.trim() })
    .select()
    .single()

  if (insertError) {
    return NextResponse.json({ error: insertError.message }, { status: 500 })
  }

  return NextResponse.json({ message }, { status: 201 })
}
