import { createClient } from '@/lib/supabase/client'

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export async function register(email: string, password: string) {
  if (!EMAIL_REGEX.test(email)) {
    return { data: { user: null }, error: { message: 'Invalid email format' } }
  }
  if (password.length < 8) {
    return { data: { user: null }, error: { message: 'Password must be at least 8 characters' } }
  }

  const supabase = createClient()
  return await supabase.auth.signUp({ email, password })
}

export async function login(email: string, password: string) {
  if (!EMAIL_REGEX.test(email)) {
    return { data: { user: null, session: null }, error: { message: 'Invalid email format' } }
  }

  const supabase = createClient()
  return await supabase.auth.signInWithPassword({ email, password })
}

export async function logout() {
  const supabase = createClient()
  return await supabase.auth.signOut()
}

export async function getCurrentUser() {
  const supabase = createClient()
  return await supabase.auth.getUser()
}
