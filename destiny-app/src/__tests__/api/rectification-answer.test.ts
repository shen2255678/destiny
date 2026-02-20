import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGetUser = vi.fn()
const mockFrom = vi.fn()
const mockUpdate = vi.fn()
const mockInsertEvent = vi.fn()

vi.mock('@/lib/supabase/server', () => ({
  createClient: vi.fn(async () => ({
    auth: { getUser: mockGetUser },
    from: mockFrom,
  })),
}))

import { POST } from '@/app/api/rectification/answer/route'

const MOCK_USER = { id: 'user-uuid-123', email: 'test@example.com' }

function makeRequest(body: Record<string, unknown>) {
  return new Request('http://localhost/api/rectification/answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function mockUserRecord(overrides: Record<string, unknown> = {}) {
  return {
    id: 'user-uuid-123',
    accuracy_type: 'FUZZY_DAY',
    rectification_status: 'collecting_signals',
    current_confidence: 0.15,
    window_size_minutes: 360,
    is_boundary_case: false,
    dealbreakers: [],
    ...overrides,
  }
}

describe('POST /api/rectification/answer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetUser.mockResolvedValue({
      data: { user: MOCK_USER },
      error: null,
    })
    mockInsertEvent.mockResolvedValue({ error: null })
    mockUpdate.mockReturnValue({
      eq: () => Promise.resolve({ data: null, error: null }),
    })
    mockFrom.mockImplementation((table: string) => {
      if (table === 'users') {
        return {
          select: () => ({
            eq: () => ({
              single: () => Promise.resolve({ data: mockUserRecord(), error: null }),
            }),
          }),
          update: mockUpdate,
        }
      }
      if (table === 'rectification_events') {
        return { insert: mockInsertEvent }
      }
      return {}
    })
  })

  it('returns 401 when not authenticated', async () => {
    mockGetUser.mockResolvedValue({ data: { user: null }, error: { message: 'Not authenticated' } })
    const res = await POST(makeRequest({ question_id: 'moon_exclusion', selected_option: 'A', source: 'daily_quiz' }))
    expect(res.status).toBe(401)
  })

  it('returns 400 when question_id is missing', async () => {
    const res = await POST(makeRequest({ selected_option: 'A', source: 'daily_quiz' }))
    expect(res.status).toBe(400)
  })

  it('returns 400 when selected_option is missing', async () => {
    const res = await POST(makeRequest({ question_id: 'moon_exclusion', source: 'daily_quiz' }))
    expect(res.status).toBe(400)
  })

  it('returns 400 when selected_option is not A or B', async () => {
    const res = await POST(makeRequest({ question_id: 'moon_exclusion', selected_option: 'C', source: 'daily_quiz' }))
    expect(res.status).toBe(400)
  })

  it('returns 200 with updated rectification state', async () => {
    const res = await POST(makeRequest({
      question_id: 'moon_exclusion_aries_taurus',
      selected_option: 'A',
      source: 'daily_quiz',
    }))
    const json = await res.json()

    expect(res.status).toBe(200)
    expect(json).toMatchObject({
      rectification_status: expect.any(String),
      current_confidence: expect.any(Number),
      next_question_available: expect.any(Boolean),
    })
  })

  it('increases current_confidence after a valid answer', async () => {
    const res = await POST(makeRequest({
      question_id: 'moon_exclusion_aries_taurus',
      selected_option: 'A',
      source: 'daily_quiz',
    }))
    const json = await res.json()

    expect(json.current_confidence).toBeGreaterThan(0.15)
  })

  it('logs candidate_eliminated event in rectification_events', async () => {
    await POST(makeRequest({
      question_id: 'moon_exclusion_aries_taurus',
      selected_option: 'B',
      source: 'daily_quiz',
    }))

    expect(mockInsertEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        user_id: 'user-uuid-123',
        source: 'daily_quiz',
        event_type: 'candidate_eliminated',
        payload: expect.objectContaining({
          question_id: 'moon_exclusion_aries_taurus',
          selected_option: 'B',
        }),
      })
    )
  })

  it('updates users table with new confidence and status', async () => {
    await POST(makeRequest({
      question_id: 'moon_exclusion_aries_taurus',
      selected_option: 'A',
      source: 'onboarding_post',
    }))

    expect(mockUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        current_confidence: expect.any(Number),
        rectification_status: expect.any(String),
      })
    )
  })

  it('sets tier_upgraded=true when confidence reaches locked threshold', async () => {
    mockFrom.mockImplementation((table: string) => {
      if (table === 'users') {
        return {
          select: () => ({
            eq: () => ({
              single: () => Promise.resolve({
                data: mockUserRecord({ current_confidence: 0.79, rectification_status: 'narrowed_to_d9' }),
                error: null,
              }),
            }),
          }),
          update: mockUpdate,
        }
      }
      if (table === 'rectification_events') return { insert: mockInsertEvent }
      return {}
    })

    const res = await POST(makeRequest({
      question_id: 'ascendant_exclusion_fire_earth',
      selected_option: 'A',
      source: 'daily_quiz',
    }))
    const json = await res.json()

    expect(json.tier_upgraded).toBe(true)
    expect(json.rectification_status).toBe('locked')
  })
})
