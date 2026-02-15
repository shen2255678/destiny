import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

const VALID_LEVELS = ['high', 'medium', 'low'] as const

export async function GET() {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  const { data, error } = await supabase
    .from('users')
    .select('social_energy')
    .eq('id', user.id)
    .single()

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json({ social_energy: data.social_energy || 'medium' })
}

export async function PATCH(request: Request) {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  const body = await request.json()
  const { social_energy } = body

  if (!VALID_LEVELS.includes(social_energy)) {
    return NextResponse.json(
      { error: 'Invalid value. Must be: high, medium, or low' },
      { status: 400 }
    )
  }

  const { error } = await supabase
    .from('users')
    .update({ social_energy })
    .eq('id', user.id)

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json({ social_energy })
}
