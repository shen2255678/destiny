import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock Supabase clients
const mockGetUser = vi.fn()
const mockFrom = vi.fn()
const mockAdminFrom = vi.fn()
const mockStorage = vi.fn()

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

import { GET } from '@/app/api/matches/daily/route'

const TODAY = new Date().toISOString().slice(0, 10)

const MOCK_MATCH = {
  id: 'match-uuid-1',
  user_id: 'user-a',
  matched_user_id: 'user-b',
  match_date: TODAY,
  kernel_score: 0.82,
  power_score: 0.75,
  glitch_score: 0.65,
  total_score: 0.77,
  match_type: 'complementary',
  tags: ['Magnetic', 'Nurturing', 'Grounding'],
  radar_passion: 80,
  radar_stability: 75,
  radar_communication: 72,
  card_color: 'coral',
  user_action: 'pending',
}

const MOCK_MATCHED_USER = {
  id: 'user-b',
  archetype_name: 'The Anchor',
  archetype_desc: '穩定的力量',
  display_name: 'TestUser',
  interest_tags: ['咖啡', '登山'],
}

describe('GET /api/matches/daily', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    mockGetUser.mockResolvedValue({
      data: { user: { id: 'user-a', email: 'a@test.com' } },
      error: null,
    })

    // Auth client: query daily_matches
    mockFrom.mockImplementation((table: string) => {
      if (table === 'daily_matches') {
        return {
          select: () => ({
            eq: () => ({
              eq: () => ({
                order: () => ({
                  limit: () => Promise.resolve({ data: [MOCK_MATCH], error: null }),
                }),
              }),
            }),
          }),
        }
      }
      return {}
    })

    // Admin client: query users and photos
    mockAdminFrom.mockImplementation((table: string) => {
      if (table === 'users') {
        return {
          select: () => ({
            in: () => Promise.resolve({ data: [MOCK_MATCHED_USER], error: null }),
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

    const req = new Request('http://localhost/api/matches/daily')
    const res = await GET(req)
    expect(res.status).toBe(401)
  })

  it('returns match cards with correct shape', async () => {
    const req = new Request('http://localhost/api/matches/daily')
    const res = await GET(req)
    const json = await res.json()

    expect(res.status).toBe(200)
    expect(Array.isArray(json.cards)).toBe(true)
    expect(json.cards).toHaveLength(1)

    const card = json.cards[0]
    expect(card).toMatchObject({
      id: 'match-uuid-1',
      match_type: 'complementary',
      archetype_name: 'The Anchor',
      tags: ['Magnetic', 'Nurturing', 'Grounding'],
      radar: { passion: 80, stability: 75, communication: 72 },
      user_action: 'pending',
    })
  })

  it('includes match_pct as percentage string', async () => {
    const req = new Request('http://localhost/api/matches/daily')
    const res = await GET(req)
    const json = await res.json()

    expect(json.cards[0].match_pct).toBe('77%')
  })

  it('returns empty cards array when no matches today', async () => {
    mockFrom.mockImplementation(() => ({
      select: () => ({
        eq: () => ({
          eq: () => ({
            order: () => ({
              limit: () => Promise.resolve({ data: [], error: null }),
            }),
          }),
        }),
      }),
    }))

    const req = new Request('http://localhost/api/matches/daily')
    const res = await GET(req)
    const json = await res.json()

    expect(res.status).toBe(200)
    expect(json.cards).toHaveLength(0)
  })

  it('includes interest_tags from matched user', async () => {
    const req = new Request('http://localhost/api/matches/daily')
    const res = await GET(req)
    const json = await res.json()

    expect(json.cards[0].interest_tags).toEqual(['咖啡', '登山'])
  })
})
