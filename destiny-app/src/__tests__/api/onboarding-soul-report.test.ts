import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGetUser = vi.fn()
const mockFrom = vi.fn()
const mockUpdate = vi.fn()

vi.mock('@/lib/supabase/server', () => ({
  createClient: vi.fn(async () => ({
    auth: { getUser: mockGetUser },
    from: mockFrom,
  })),
}))

import { GET } from '@/app/api/onboarding/soul-report/route'

function makeRequest() {
  return new Request('http://localhost/api/onboarding/soul-report', {
    method: 'GET',
  })
}

const mockUser = {
  id: 'user-uuid-123',
  rpv_conflict: 'cold_war',
  rpv_power: 'control',
  rpv_energy: 'home',
  data_tier: 1,
  sun_sign: 'aries',
  moon_sign: 'cancer',
}

describe('GET /api/onboarding/soul-report', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetUser.mockResolvedValue({
      data: { user: { id: 'user-uuid-123' } },
      error: null,
    })
    mockFrom.mockImplementation((table: string) => {
      if (table === 'users') {
        return {
          select: () => ({
            eq: () => ({
              single: () => Promise.resolve({ data: mockUser, error: null }),
            }),
          }),
          update: mockUpdate,
        }
      }
      return {}
    })
    mockUpdate.mockReturnValue({
      eq: () => Promise.resolve({ data: null, error: null }),
    })
  })

  it('returns archetype with name, description, tags, and stats', async () => {
    const res = await GET(makeRequest())
    const json = await res.json()

    expect(res.status).toBe(200)
    expect(json.data).toHaveProperty('archetype_name')
    expect(json.data).toHaveProperty('archetype_desc')
    expect(json.data).toHaveProperty('tags')
    expect(json.data).toHaveProperty('stats')
    expect(json.data.stats).toHaveLength(3)
  })

  it('updates onboarding_step to complete', async () => {
    await GET(makeRequest())

    expect(mockUpdate).toHaveBeenCalledWith(
      expect.objectContaining({ onboarding_step: 'complete' })
    )
  })

  it('returns 401 when not authenticated', async () => {
    mockGetUser.mockResolvedValue({
      data: { user: null },
      error: { message: 'Not authenticated' },
    })

    const res = await GET(makeRequest())
    expect(res.status).toBe(401)
  })
})
