import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock Supabase client before importing auth functions
const mockSignUp = vi.fn()
const mockSignInWithPassword = vi.fn()
const mockSignOut = vi.fn()
const mockGetUser = vi.fn()

vi.mock('@/lib/supabase/client', () => ({
  createClient: () => ({
    auth: {
      signUp: mockSignUp,
      signInWithPassword: mockSignInWithPassword,
      signOut: mockSignOut,
      getUser: mockGetUser,
    },
  }),
}))

// Import AFTER mock setup
import { register, login, logout, getCurrentUser } from '@/lib/auth'

describe('Auth: register', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('registers a new user with email and password', async () => {
    mockSignUp.mockResolvedValue({
      data: { user: { id: 'uuid-123', email: 'test@example.com' } },
      error: null,
    })

    const result = await register('test@example.com', 'Password123!')

    expect(mockSignUp).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'Password123!',
    })
    expect(result.data?.user?.email).toBe('test@example.com')
    expect(result.error).toBeNull()
  })

  it('returns error for duplicate email', async () => {
    mockSignUp.mockResolvedValue({
      data: { user: null },
      error: { message: 'User already registered' },
    })

    const result = await register('existing@example.com', 'Password123!')

    expect(result.error?.message).toBe('User already registered')
    expect(result.data?.user).toBeNull()
  })

  it('validates email format before calling Supabase', async () => {
    const result = await register('not-an-email', 'Password123!')

    expect(mockSignUp).not.toHaveBeenCalled()
    expect(result.error?.message).toBe('Invalid email format')
  })

  it('validates password minimum length', async () => {
    const result = await register('test@example.com', '123')

    expect(mockSignUp).not.toHaveBeenCalled()
    expect(result.error?.message).toBe('Password must be at least 8 characters')
  })
})

describe('Auth: login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('logs in with valid email and password', async () => {
    mockSignInWithPassword.mockResolvedValue({
      data: { user: { id: 'uuid-123', email: 'test@example.com' }, session: { access_token: 'token' } },
      error: null,
    })

    const result = await login('test@example.com', 'Password123!')

    expect(mockSignInWithPassword).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'Password123!',
    })
    expect(result.data?.user?.email).toBe('test@example.com')
    expect(result.data?.session).toBeTruthy()
    expect(result.error).toBeNull()
  })

  it('returns error for wrong password', async () => {
    mockSignInWithPassword.mockResolvedValue({
      data: { user: null, session: null },
      error: { message: 'Invalid login credentials' },
    })

    const result = await login('test@example.com', 'wrong-password')

    expect(result.error?.message).toBe('Invalid login credentials')
  })

  it('validates email format before calling Supabase', async () => {
    const result = await login('bad-email', 'Password123!')

    expect(mockSignInWithPassword).not.toHaveBeenCalled()
    expect(result.error?.message).toBe('Invalid email format')
  })
})

describe('Auth: logout', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('signs out the current user', async () => {
    mockSignOut.mockResolvedValue({ error: null })

    const result = await logout()

    expect(mockSignOut).toHaveBeenCalled()
    expect(result.error).toBeNull()
  })
})

describe('Auth: getCurrentUser', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns the current authenticated user', async () => {
    mockGetUser.mockResolvedValue({
      data: { user: { id: 'uuid-123', email: 'test@example.com' } },
      error: null,
    })

    const result = await getCurrentUser()

    expect(result.data?.user?.id).toBe('uuid-123')
    expect(result.error).toBeNull()
  })

  it('returns null user when not authenticated', async () => {
    mockGetUser.mockResolvedValue({
      data: { user: null },
      error: { message: 'Not authenticated' },
    })

    const result = await getCurrentUser()

    expect(result.data?.user).toBeNull()
  })
})
