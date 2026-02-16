import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock global fetch for astro-service call
const originalFetch = globalThis.fetch
vi.stubGlobal('fetch', vi.fn(() =>
  Promise.resolve(new Response(JSON.stringify({
    sun_sign: 'capricorn', moon_sign: null, venus_sign: 'aquarius',
    mars_sign: 'scorpio', saturn_sign: 'capricorn', ascendant_sign: null,
    element_primary: 'earth', data_tier: 3,
  }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
))

// Mock Supabase server client
const mockGetUser = vi.fn()
const mockUpsert = vi.fn()
const mockUpdate = vi.fn()
const mockFrom = vi.fn()

vi.mock('@/lib/supabase/server', () => ({
  createClient: vi.fn(async () => ({
    auth: { getUser: mockGetUser },
    from: mockFrom,
  })),
}))

import { POST } from '@/app/api/onboarding/birth-data/route'

function makeRequest(body: Record<string, unknown>) {
  return new Request('http://localhost/api/onboarding/birth-data', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

describe('POST /api/onboarding/birth-data', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetUser.mockResolvedValue({
      data: { user: { id: 'user-uuid-123' } },
      error: null,
    })
    // mockFrom needs to handle: upsert chain, update chain, and select chain
    const mockUserData = {
      id: 'user-uuid-123', birth_date: '1990-01-15', data_tier: 3,
      sun_sign: 'capricorn', moon_sign: null,
    }
    mockUpdate.mockReturnValue({
      eq: () => Promise.resolve({ data: mockUserData, error: null }),
    })
    mockFrom.mockImplementation(() => ({
      upsert: mockUpsert,
      update: mockUpdate,
      select: () => ({
        eq: () => ({
          single: () => Promise.resolve({ data: mockUserData, error: null }),
        }),
      }),
    }))
    mockUpsert.mockReturnValue({
      select: () => ({
        single: () => Promise.resolve({
          data: mockUserData,
          error: null,
        }),
      }),
    })
  })

  it('saves birth data and returns user with data_tier=3 for unknown time', async () => {
    const res = await POST(makeRequest({
      birth_date: '1990-01-15',
      birth_time: 'unknown',
      birth_city: '台北市',
    }))
    const json = await res.json()

    expect(res.status).toBe(200)
    expect(mockFrom).toHaveBeenCalledWith('users')
    expect(mockUpsert).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'user-uuid-123',
        birth_date: '1990-01-15',
        birth_time: 'unknown',
        birth_city: '台北市',
        data_tier: 3,
        onboarding_step: 'rpv_test',
      }),
      expect.anything()
    )
  })

  it('sets data_tier=2 for fuzzy birth time (morning/afternoon)', async () => {
    const res = await POST(makeRequest({
      birth_date: '1990-01-15',
      birth_time: 'morning',
      birth_city: '台北市',
    }))

    expect(mockUpsert).toHaveBeenCalledWith(
      expect.objectContaining({ data_tier: 2 }),
      expect.anything()
    )
  })

  it('sets data_tier=1 for precise birth time', async () => {
    const res = await POST(makeRequest({
      birth_date: '1990-01-15',
      birth_time: 'precise',
      birth_time_exact: '14:30',
      birth_city: '台北市',
    }))

    expect(mockUpsert).toHaveBeenCalledWith(
      expect.objectContaining({
        data_tier: 1,
        birth_time_exact: '14:30',
      }),
      expect.anything()
    )
  })

  it('returns 401 when not authenticated', async () => {
    mockGetUser.mockResolvedValue({
      data: { user: null },
      error: { message: 'Not authenticated' },
    })

    const res = await POST(makeRequest({
      birth_date: '1990-01-15',
      birth_time: 'unknown',
      birth_city: '台北市',
    }))

    expect(res.status).toBe(401)
  })

  it('returns 400 when required fields are missing', async () => {
    const res = await POST(makeRequest({
      birth_date: '1990-01-15',
      // missing birth_time and birth_city
    }))

    expect(res.status).toBe(400)
  })
})
