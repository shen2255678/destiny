import { createClient } from '@supabase/supabase-js'
import type { Database } from './types'

// Admin client using service role key — bypasses RLS.
// Only use in server-side API routes after verifying auth manually.
export function createAdminClient() {
  return createClient<Database>(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  )
}
