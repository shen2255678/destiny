import { NextResponse } from 'next/server'
import { createClient, createAdminClient } from '@/lib/supabase/server'

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: matchId } = await params
  const body = await request.json()
  const { action } = body

  if (!action || !['accept', 'pass'].includes(action)) {
    return NextResponse.json(
      { error: "Invalid action. Must be 'accept' or 'pass'" },
      { status: 400 }
    )
  }

  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  // Update the match action (RLS ensures user can only update their own match)
  const { data: match, error: updateError } = await supabase
    .from('daily_matches')
    .update({ user_action: action })
    .eq('id', matchId)
    .eq('user_id', user.id) // safety guard
    .select('matched_user_id, match_date')
    .single()

  if (updateError || !match) {
    return NextResponse.json(
      { error: updateError?.message ?? 'Match not found' },
      { status: 404 }
    )
  }

  // If accepted, check for mutual accept → create connection
  if (action === 'accept') {
    const admin = createAdminClient()
    const { matched_user_id: matchedUserId, match_date } = match

    // Look up the symmetric match (matched user's view of current user)
    const { data: symmetricMatch } = await admin
      .from('daily_matches')
      .select('id, user_action')
      .eq('user_id', matchedUserId)
      .eq('matched_user_id', user.id)
      .eq('match_date', match_date)
      .single()

    if (symmetricMatch?.user_action === 'accept') {
      // Mutual accept → create connection
      // Check connection doesn't already exist
      const { data: existing } = await admin
        .from('connections')
        .select('id')
        .or(
          `and(user_a_id.eq.${user.id},user_b_id.eq.${matchedUserId}),` +
          `and(user_a_id.eq.${matchedUserId},user_b_id.eq.${user.id})`
        )
        .eq('status', 'active')
        .maybeSingle()

      if (!existing) {
        const { error: connError } = await admin
          .from('connections')
          .insert({
            user_a_id: user.id,
            user_b_id: matchedUserId,
            match_id: matchId,
            status: 'icebreaker',
            sync_level: 1,
            message_count: 0,
          })

        if (connError) {
          console.error('[matches/action] Failed to create connection:', connError.message)
        } else {
          return NextResponse.json({ action, matched: true, message: '雙向配對成功！連結已建立' })
        }
      }
    }
  }

  return NextResponse.json({ action, matched: false })
}
