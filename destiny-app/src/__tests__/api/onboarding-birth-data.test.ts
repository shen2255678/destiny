import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock global fetch for astro-service call
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
const mockInsertEvent = vi.fn()

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

const MOCK_USER_DATA = {
  id: 'user-uuid-123', birth_date: '1990-01-15', data_tier: 3,
  sun_sign: 'capricorn', moon_sign: null,
}

describe('POST /api/onboarding/birth-data', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetUser.mockResolvedValue({
      data: { user: { id: 'user-uuid-123', email: 'test@example.com' } },
      error: null,
    })
    mockUpdate.mockReturnValue({
      eq: () => Promise.resolve({ data: MOCK_USER_DATA, error: null }),
    })
    mockInsertEvent.mockResolvedValue({ error: null })
    mockFrom.mockImplementation((table: string) => {
      if (table === 'users') {
        return {
          upsert: mockUpsert,
          update: mockUpdate,
          select: () => ({
            eq: () => ({
              single: () => Promise.resolve({ data: MOCK_USER_DATA, error: null }),
            }),
          }),
        }
      }
      if (table === 'rectification_events') {
        return { insert: mockInsertEvent }
      }
      return {}
    })
    mockUpsert.mockReturnValue({
      select: () => ({
        single: () => Promise.resolve({
          data: MOCK_USER_DATA,
          error: null,
        }),
      }),
    })
  })

  // -----------------------------------------------------------------------
  // Legacy birth_time format (backward compat)
  // -----------------------------------------------------------------------

  it('saves birth data and returns user with data_tier=3 for unknown time', async () => {
    const res = await POST(makeRequest({
      birth_date: '1990-01-15',
      birth_time: 'unknown',
      birth_city: '台北市',
    }))

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
    await POST(makeRequest({
      birth_date: '1990-01-15',
      birth_time: 'morning',
      birth_city: '台北市',
    }))

    expect(mockUpsert).toHaveBeenCalledWith(
      expect.objectContaining({ data_tier: 2 }),
      expect.anything()
    )
  })

  it('sets data_tier=2 for evening birth time', async () => {
    await POST(makeRequest({
      birth_date: '1990-01-15',
      birth_time: 'evening',
      birth_city: '台北市',
    }))

    expect(mockUpsert).toHaveBeenCalledWith(
      expect.objectContaining({ birth_time: 'evening', data_tier: 2 }),
      expect.anything()
    )
  })

  it('sets data_tier=1 for precise birth time', async () => {
    await POST(makeRequest({
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
      // missing birth_time/accuracy_type and birth_city
    }))

    expect(res.status).toBe(400)
  })

  // -----------------------------------------------------------------------
  // New accuracy_type system
  // -----------------------------------------------------------------------

  it('sets current_confidence=0.90 and rectification_status=collecting_signals for PRECISE', async () => {
    await POST(makeRequest({
      birth_date: '1990-01-15',
      accuracy_type: 'PRECISE',
      birth_time_exact: '14:30',
      birth_city: '台北市',
    }))

    expect(mockUpsert).toHaveBeenCalledWith(
      expect.objectContaining({
        accuracy_type: 'PRECISE',
        current_confidence: 0.90,
        rectification_status: 'collecting_signals',
        window_size_minutes: 0,
        birth_time: 'precise',
        data_tier: 1,
      }),
      expect.anything()
    )
  })

  it('sets current_confidence=0.30 and window_size_minutes=120 for TWO_HOUR_SLOT', async () => {
    await POST(makeRequest({
      birth_date: '1990-01-15',
      accuracy_type: 'TWO_HOUR_SLOT',
      window_start: '13:00',
      window_end: '15:00',
      birth_city: '台北市',
    }))

    expect(mockUpsert).toHaveBeenCalledWith(
      expect.objectContaining({
        accuracy_type: 'TWO_HOUR_SLOT',
        current_confidence: 0.30,
        rectification_status: 'collecting_signals',
        window_size_minutes: 120,
        window_start: '13:00',
        window_end: '15:00',
        data_tier: 2,
      }),
      expect.anything()
    )
  })

  it('sets current_confidence=0.15 and window_size_minutes=360 for FUZZY_DAY morning', async () => {
    await POST(makeRequest({
      birth_date: '1990-01-15',
      accuracy_type: 'FUZZY_DAY',
      fuzzy_period: 'morning',
      birth_city: '台北市',
    }))

    expect(mockUpsert).toHaveBeenCalledWith(
      expect.objectContaining({
        accuracy_type: 'FUZZY_DAY',
        current_confidence: 0.15,
        rectification_status: 'collecting_signals',
        window_size_minutes: 360,
        window_start: '06:00',
        window_end: '12:00',
        birth_time: 'morning',
        data_tier: 2,
      }),
      expect.anything()
    )
  })

  it('sets current_confidence=0.05 and window_size_minutes=1440 for FUZZY_DAY unknown', async () => {
    await POST(makeRequest({
      birth_date: '1990-01-15',
      accuracy_type: 'FUZZY_DAY',
      birth_city: '台北市',
      // no fuzzy_period → unknown
    }))

    expect(mockUpsert).toHaveBeenCalledWith(
      expect.objectContaining({
        accuracy_type: 'FUZZY_DAY',
        current_confidence: 0.05,
        rectification_status: 'collecting_signals',
        window_size_minutes: 1440,
        window_start: '00:00',
        window_end: '24:00',
        birth_time: 'unknown',
        data_tier: 3,
      }),
      expect.anything()
    )
  })

  it('logs range_initialized event in rectification_events', async () => {
    await POST(makeRequest({
      birth_date: '1990-01-15',
      accuracy_type: 'PRECISE',
      birth_time_exact: '14:30',
      birth_city: '台北市',
    }))

    expect(mockInsertEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        user_id: 'user-uuid-123',
        source: 'signup',
        event_type: 'range_initialized',
        payload: expect.objectContaining({
          accuracy_type: 'PRECISE',
          window_size_minutes: 0,
        }),
      })
    )
  })

  it('sets window_start and window_end from FUZZY_DAY evening period', async () => {
    await POST(makeRequest({
      birth_date: '1990-01-15',
      accuracy_type: 'FUZZY_DAY',
      fuzzy_period: 'evening',
      birth_city: '台北市',
    }))

    expect(mockUpsert).toHaveBeenCalledWith(
      expect.objectContaining({
        window_start: '18:00',
        window_end: '24:00',
        birth_time: 'evening',
        current_confidence: 0.15,
      }),
      expect.anything()
    )
  })
})
