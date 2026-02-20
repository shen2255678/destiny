import { NextResponse } from 'next/server'
import { createClient, createAdminClient } from '@/lib/supabase/server'

const CARD_TYPE_MAP: Record<string, { label: string; type: string }> = {
  complementary: { label: '心靈共鳴', type: 'stability' },
  similar:       { label: '磁場相吸', type: 'passion' },
  tension:       { label: '張力拉鋸', type: 'wildcard' },
}

export async function GET() {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  const today = new Date().toISOString().slice(0, 10)

  // Fetch today's matches for this user
  const { data: matches, error: matchError } = await supabase
    .from('daily_matches')
    .select('*')
    .eq('user_id', user.id)
    .eq('match_date', today)
    .order('total_score', { ascending: false })
    .limit(3)

  if (matchError) {
    return NextResponse.json({ error: matchError.message }, { status: 500 })
  }

  if (!matches || matches.length === 0) {
    return NextResponse.json({ cards: [], message: 'No matches for today yet' })
  }

  // Fetch matched user profiles + blurred photos via admin client (bypasses RLS restrictions)
  const admin = createAdminClient()
  const matchedIds = matches.map(m => m.matched_user_id)

  const [usersResult, photosResult] = await Promise.all([
    admin
      .from('users')
      .select('id, archetype_name, archetype_desc, display_name, interest_tags')
      .in('id', matchedIds),
    admin
      .from('photos')
      .select('user_id, blurred_path')
      .in('user_id', matchedIds)
      .eq('upload_order', 1),
  ])

  const userMap = Object.fromEntries(
    (usersResult.data ?? []).map(u => [u.id, u])
  )
  const photoMap = Object.fromEntries(
    (photosResult.data ?? []).map(p => [p.user_id, p.blurred_path])
  )

  // Build blurred photo signed URLs
  const blurredUrls: Record<string, string | null> = {}
  for (const matchedId of matchedIds) {
    const blurredPath = photoMap[matchedId]
    if (blurredPath) {
      const { data: signedData } = await admin.storage
        .from('photos')
        .createSignedUrl(blurredPath, 3600)
      blurredUrls[matchedId] = signedData?.signedUrl ?? null
    } else {
      blurredUrls[matchedId] = null
    }
  }

  // Shape match cards
  const cards = matches.map(match => {
    const matchedUser = userMap[match.matched_user_id]
    const cardMeta = CARD_TYPE_MAP[match.match_type] ?? { label: '神秘連結', type: 'wildcard' }

    return {
      id: match.id,
      matched_user_id: match.matched_user_id,
      match_type: match.match_type,
      card_type: cardMeta.type,
      label: cardMeta.label,
      match_pct: `${Math.round(match.total_score * 100)}%`,
      card_color: match.card_color,
      archetype_name: matchedUser?.archetype_name ?? '神秘靈魂',
      archetype_desc: matchedUser?.archetype_desc ?? null,
      interest_tags: matchedUser?.interest_tags ?? [],
      tags: match.tags ?? [],
      radar: {
        passion: match.radar_passion,
        stability: match.radar_stability,
        communication: match.radar_communication,
      },
      scores: {
        kernel: match.kernel_score,
        power: match.power_score,
        glitch: match.glitch_score,
        total: match.total_score,
      },
      blurred_photo_url: blurredUrls[match.matched_user_id],
      user_action: match.user_action,
    }
  })

  return NextResponse.json({ cards, date: today })
}
