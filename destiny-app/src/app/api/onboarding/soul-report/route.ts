import { NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { generateArchetype } from '@/lib/ai/archetype'

export async function GET() {
  const supabase = await createClient()
  const { data: { user }, error: authError } = await supabase.auth.getUser()

  if (authError || !user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 })
  }

  // Fetch user data for archetype generation
  const { data: userData, error: fetchError } = await supabase
    .from('users')
    .select('*')
    .eq('id', user.id)
    .single()

  if (fetchError || !userData) {
    return NextResponse.json({ error: 'User data not found' }, { status: 404 })
  }

  // Generate archetype from user data
  const result = generateArchetype({
    rpv_conflict: userData.rpv_conflict ?? undefined,
    rpv_power: userData.rpv_power ?? undefined,
    rpv_energy: userData.rpv_energy ?? undefined,
    sun_sign: userData.sun_sign ?? undefined,
    moon_sign: userData.moon_sign ?? undefined,
  })

  // Save archetype to user record and mark onboarding complete
  await supabase
    .from('users')
    .update({
      archetype_name: result.archetype_name,
      archetype_desc: result.archetype_desc,
      onboarding_step: 'complete',
    })
    .eq('id', user.id)

  return NextResponse.json({ data: result })
}
