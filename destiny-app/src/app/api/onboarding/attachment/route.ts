import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

const VALID_STYLES = ['anxious', 'avoidant', 'secure'] as const
const VALID_ROLES  = ['dom_secure', 'sub_secure', 'balanced'] as const

export async function POST(request: Request) {
  const body = await request.json()
  const { attachment_style, attachment_role } = body

  if (!attachment_style) {
    return NextResponse.json(
      { error: 'Missing required field: attachment_style' },
      { status: 400 }
    )
  }
  if (!VALID_STYLES.includes(attachment_style)) {
    return NextResponse.json(
      { error: `Invalid attachment_style. Must be one of: ${VALID_STYLES.join(', ')}` },
      { status: 400 }
    )
  }
  if (attachment_role && !VALID_ROLES.includes(attachment_role)) {
    return NextResponse.json(
      { error: `Invalid attachment_role. Must be one of: ${VALID_ROLES.join(', ')}` },
      { status: 400 }
    )
  }

  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  const update: Record<string, string> = {
    attachment_style,
    onboarding_step: 'photos',
  }
  if (attachment_role) {
    update.attachment_role = attachment_role
  }

  const { error } = await supabase
    .from('users')
    .update(update)
    .eq('id', user.id)

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json({ success: true })
}
