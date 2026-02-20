import { describe, it, expect, vi, beforeEach } from 'vitest'

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
    storage: {
      from: (_bucket: string) => ({
        createSignedUrl: vi.fn(async () => ({
          data: { signedUrl: 'https://example.com/blurred.jpg' },
          error: null,
        })),
      }),
    },
  })),
}))

import { GET } from '@/app/api/connections/route'

const MOCK_USER_ID = 'user-a'

const MOCK_CONNECTION = {
  id: 'conn-uuid-1',
  user_a_id: MOCK_USER_ID,
  user_b_id: 'user-b',
  match_id: 'match-uuid-1',
  sync_level: 1,
  message_count: 3,
  status: 'active',
  last_activity: new Date().toISOString(),
  icebreaker_question: null,
  user_a_answer: null,
  user_b_answer: null,
  icebreaker_tags: null,
}

const MOCK_OTHER_USER = {
  id: 'user-b',
  archetype_name: 'The Anchor',
  display_name: null,
}

const MOCK_MATCH = {
  id: 'match-uuid-1',
  tags: ['Tender', 'Grounding'],
  total_score: 0.78,
}

describe('GET /api/connections', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    mockGetUser.mockResolvedValue({
      data: { user: { id: MOCK_USER_ID } },
      error: null,
    })

    mockFrom.mockImplementation((table: string) => {
      if (table === 'connections') {
        return {
          select: () => ({
            or: () => ({
              neq: () => ({
                order: () => Promise.resolve({ data: [MOCK_CONNECTION], error: null }),
              }),
            }),
          }),
        }
      }
      return {}
    })

    mockAdminFrom.mockImplementation((table: string) => {
      if (table === 'users') {
        return {
          select: () => ({
            in: () => Promise.resolve({ data: [MOCK_OTHER_USER], error: null }),
          }),
        }
      }
      if (table === 'daily_matches') {
        return {
          select: () => ({
            in: () => Promise.resolve({ data: [MOCK_MATCH], error: null }),
          }),
        }
      }
      if (table === 'photos') {
        return {
          select: () => ({
            in: () => ({
              eq: () => Promise.resolve({
                data: [{ user_id: 'user-b', blurred_path: 'user-b/blurred_1.jpg' }],
                error: null,
              }),
            }),
          }),
        }
      }
      return {}
    })
  })

  it('returns 401 when not authenticated', async () => {
    mockGetUser.mockResolvedValue({ data: { user: null }, error: { message: 'Not authenticated' } })
    const res = await GET(new Request('http://localhost/api/connections'))
    expect(res.status).toBe(401)
  })

  it('returns connections list with correct shape', async () => {
    const res = await GET(new Request('http://localhost/api/connections'))
    const json = await res.json()

    expect(res.status).toBe(200)
    expect(Array.isArray(json.connections)).toBe(true)
    expect(json.connections).toHaveLength(1)

    const conn = json.connections[0]
    expect(conn).toMatchObject({
      id: 'conn-uuid-1',
      sync_level: 1,
      message_count: 3,
      status: 'active',
    })
  })

  it('includes other_user archetype in each connection', async () => {
    const res = await GET(new Request('http://localhost/api/connections'))
    const json = await res.json()

    expect(json.connections[0].other_user).toMatchObject({
      id: 'user-b',
      archetype_name: 'The Anchor',
    })
  })

  it('includes tags from the daily match', async () => {
    const res = await GET(new Request('http://localhost/api/connections'))
    const json = await res.json()

    expect(json.connections[0].tags).toEqual(['Tender', 'Grounding'])
  })

  it('returns empty array when no connections', async () => {
    mockFrom.mockImplementation(() => ({
      select: () => ({
        or: () => ({
          neq: () => ({
            order: () => Promise.resolve({ data: [], error: null }),
          }),
        }),
      }),
    }))

    const res = await GET(new Request('http://localhost/api/connections'))
    const json = await res.json()

    expect(res.status).toBe(200)
    expect(json.connections).toHaveLength(0)
  })
})
