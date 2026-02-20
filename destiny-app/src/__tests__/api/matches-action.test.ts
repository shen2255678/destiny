import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock Supabase clients
const mockGetUser = vi.fn()
const mockFrom = vi.fn()
const mockAdminFrom = vi.fn()

vi.mock('@/lib/supabase/server', () => ({
  createClient: vi.fn(async () => ({
    auth: { getUser: mockGetUser },
    from: mockFrom,
  })),
  createAdminClient: vi.fn(() => ({
    from: mockAdminFrom,
  })),
}))

import { POST } from '@/app/api/matches/[id]/route'

const TODAY = new Date().toISOString().slice(0, 10)

function makeRequest(action: string) {
  return new Request('http://localhost/api/matches/match-uuid-1', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action }),
  })
}

const PARAMS = Promise.resolve({ id: 'match-uuid-1' })

describe('POST /api/matches/[id]/action', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    mockGetUser.mockResolvedValue({
      data: { user: { id: 'user-a', email: 'a@test.com' } },
      error: null,
    })

    // Default: update succeeds, no mutual match
    mockFrom.mockImplementation(() => ({
      update: () => ({
        eq: () => ({
          eq: () => ({
            select: () => ({
              single: () => Promise.resolve({
                data: { matched_user_id: 'user-b', match_date: TODAY },
                error: null,
              }),
            }),
          }),
        }),
      }),
    }))

    // Admin client: no symmetric match by default
    mockAdminFrom.mockImplementation(() => ({
      select: () => ({
        eq: () => ({
          eq: () => ({
            eq: () => ({
              single: () => Promise.resolve({ data: null, error: null }),
            }),
          }),
        }),
      }),
      insert: vi.fn(() => Promise.resolve({ error: null })),
    }))
  })

  it('returns 401 when not authenticated', async () => {
    mockGetUser.mockResolvedValue({ data: { user: null }, error: { message: 'Not authenticated' } })

    const res = await POST(makeRequest('pass'), { params: PARAMS })
    expect(res.status).toBe(401)
  })

  it('returns 400 for invalid action', async () => {
    const res = await POST(makeRequest('invalid'), { params: PARAMS })
    expect(res.status).toBe(400)
  })

  it('records pass action and returns matched=false', async () => {
    const res = await POST(makeRequest('pass'), { params: PARAMS })
    const json = await res.json()

    expect(res.status).toBe(200)
    expect(json.action).toBe('pass')
    expect(json.matched).toBe(false)
  })

  it('records accept action, no mutual = matched false', async () => {
    const res = await POST(makeRequest('accept'), { params: PARAMS })
    const json = await res.json()

    expect(res.status).toBe(200)
    expect(json.action).toBe('accept')
    expect(json.matched).toBe(false)
  })

  it('creates connection when both users accept (mutual accept)', async () => {
    // Admin returns symmetric match with user_action=accept
    const mockInsert = vi.fn(() => Promise.resolve({ error: null }))
    mockAdminFrom.mockImplementation((table: string) => {
      if (table === 'daily_matches') {
        return {
          select: () => ({
            eq: () => ({
              eq: () => ({
                eq: () => ({
                  single: () => Promise.resolve({
                    data: { id: 'sym-match-uuid', user_action: 'accept' },
                    error: null,
                  }),
                }),
              }),
            }),
          }),
        }
      }
      if (table === 'connections') {
        return {
          select: () => ({
            or: () => ({
              eq: () => ({
                maybeSingle: () => Promise.resolve({ data: null, error: null }),
              }),
            }),
          }),
          insert: mockInsert,
        }
      }
      return {}
    })

    const res = await POST(makeRequest('accept'), { params: PARAMS })
    const json = await res.json()

    expect(res.status).toBe(200)
    expect(json.matched).toBe(true)
    expect(mockInsert).toHaveBeenCalledWith(
      expect.objectContaining({
        user_a_id: 'user-a',
        user_b_id: 'user-b',
        status: 'icebreaker',
        sync_level: 1,
      })
    )
  })

  it('does not create duplicate connection', async () => {
    const mockInsert = vi.fn()
    mockAdminFrom.mockImplementation((table: string) => {
      if (table === 'daily_matches') {
        return {
          select: () => ({
            eq: () => ({
              eq: () => ({
                eq: () => ({
                  single: () => Promise.resolve({
                    data: { id: 'sym-match-uuid', user_action: 'accept' },
                    error: null,
                  }),
                }),
              }),
            }),
          }),
        }
      }
      if (table === 'connections') {
        return {
          select: () => ({
            or: () => ({
              eq: () => ({
                // Existing connection found
                maybeSingle: () => Promise.resolve({ data: { id: 'existing-conn' }, error: null }),
              }),
            }),
          }),
          insert: mockInsert,
        }
      }
      return {}
    })

    const res = await POST(makeRequest('accept'), { params: PARAMS })
    expect(mockInsert).not.toHaveBeenCalled()
  })

  it('returns 404 when match not found or wrong user', async () => {
    mockFrom.mockImplementation(() => ({
      update: () => ({
        eq: () => ({
          eq: () => ({
            select: () => ({
              single: () => Promise.resolve({
                data: null,
                error: { message: 'No rows found' },
              }),
            }),
          }),
        }),
      }),
    }))

    const res = await POST(makeRequest('accept'), { params: PARAMS })
    expect(res.status).toBe(404)
  })
})
