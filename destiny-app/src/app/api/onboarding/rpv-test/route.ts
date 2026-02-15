import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

const RPV_FIELDS = ['rpv_conflict', 'rpv_power', 'rpv_energy'] as const

export async function POST(request: Request) {
  const body = await request.json()
  const { rpv_conflict, rpv_power, rpv_energy } = body

  if (!rpv_conflict || !rpv_power || !rpv_energy) {
    return NextResponse.json(
      { error: 'Missing required fields: rpv_conflict, rpv_power, rpv_energy' },
      { status: 400 }
    )
  }

  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  const { data, error } = await supabase
    .from('users')
    .update({
      rpv_conflict,
      rpv_power,
      rpv_energy,
      onboarding_step: 'photos',
    })
    .eq('id', user.id)
    .select()
    .single()

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json({ data })
}
