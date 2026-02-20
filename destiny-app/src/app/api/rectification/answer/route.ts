import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import type { RectificationStatus } from '@/lib/supabase/types'

const LOCK_THRESHOLD = 0.8

// Confidence gain per answered question (Via Negativa incremental approach)
// Questions eliminate candidates, reducing uncertainty → confidence rises.
const CONFIDENCE_INCREMENT = 0.10

function resolveNewStatus(confidence: number, currentStatus: RectificationStatus): RectificationStatus {
  if (confidence >= LOCK_THRESHOLD) return 'locked'
  if (confidence >= 0.5) return 'narrowed_to_2hr'
  return currentStatus === 'unrectified' ? 'collecting_signals' : currentStatus
}

export async function POST(request: Request) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  const body = await request.json()
  const { question_id, selected_option, source } = body

  if (!question_id) {
    return NextResponse.json({ error: 'question_id is required' }, { status: 400 })
  }
  if (!selected_option) {
    return NextResponse.json({ error: 'selected_option is required' }, { status: 400 })
  }
  if (selected_option !== 'A' && selected_option !== 'B') {
    return NextResponse.json({ error: 'selected_option must be A or B' }, { status: 400 })
  }

  // Fetch current rectification state
  const { data: userData } = await supabase
    .from('users')
    .select('accuracy_type, rectification_status, current_confidence, window_size_minutes, is_boundary_case, dealbreakers')
    .eq('id', user.id)
    .single()

  if (!userData) {
    return NextResponse.json({ error: 'User not found' }, { status: 404 })
  }

  const oldConfidence: number = userData.current_confidence ?? 0
  const oldStatus: RectificationStatus = userData.rectification_status ?? 'unrectified'

  // Apply Via Negativa filter: increment confidence based on signal strength
  const newConfidence = Math.min(1.0, oldConfidence + CONFIDENCE_INCREMENT)
  const newStatus = resolveNewStatus(newConfidence, oldStatus)
  const isLocked = newStatus === 'locked'
  const tierUpgraded = isLocked && oldStatus !== 'locked'

  // Update users table
  await supabase
    .from('users')
    .update({
      current_confidence: newConfidence,
      rectification_status: newStatus,
      ...(isLocked ? { calibrated_time: new Date().toISOString() } : {}),
    })
    .eq('id', user.id)

  // Log event
  const eventType = isLocked ? 'locked' : 'candidate_eliminated'
  await supabase.from('rectification_events').insert({
    user_id: user.id,
    source: source ?? 'daily_quiz',
    event_type: eventType,
    payload: {
      question_id,
      selected_option,
      old_confidence: oldConfidence,
      new_confidence: newConfidence,
      old_status: oldStatus,
      new_status: newStatus,
    },
  })

  return NextResponse.json({
    rectification_status: newStatus,
    current_confidence: newConfidence,
    calibrated_time: isLocked ? new Date().toISOString() : null,
    tier_upgraded: tierUpgraded,
    next_question_available: !isLocked,
  })
}
