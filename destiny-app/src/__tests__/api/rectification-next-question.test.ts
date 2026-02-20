import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGetUser = vi.fn()
const mockFrom = vi.fn()

vi.mock('@/lib/supabase/server', () => ({
  createClient: vi.fn(async () => ({
    auth: { getUser: mockGetUser },
    from: mockFrom,
  })),
}))

import { GET } from '@/app/api/rectification/next-question/route'

const MOCK_USER = { id: 'user-uuid-123', email: 'test@example.com' }

function makeRequest() {
  return new Request('http://localhost/api/rectification/next-question', { method: 'GET' })
}

function mockUserRecord(overrides: Record<string, unknown> = {}) {
  return {
    id: 'user-uuid-123',
    accuracy_type: 'FUZZY_DAY',
    rectification_status: 'collecting_signals',
    current_confidence: 0.15,
    window_start: '06:00',
    window_end: '12:00',
    window_size_minutes: 360,
    is_boundary_case: false,
    ...overrides,
  }
}

describe('GET /api/rectification/next-question', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetUser.mockResolvedValue({
      data: { user: MOCK_USER },
      error: null,
    })
    mockFrom.mockImplementation(() => ({
      select: () => ({
        eq: () => ({
          single: () => Promise.resolve({ data: mockUserRecord(), error: null }),
        }),
      }),
    }))
  })

  it('returns 401 when not authenticated', async () => {
    mockGetUser.mockResolvedValue({ data: { user: null }, error: { message: 'Not authenticated' } })
    const res = await GET(makeRequest())
    expect(res.status).toBe(401)
  })

  it('returns 204 when rectification_status is locked', async () => {
    mockFrom.mockImplementation(() => ({
      select: () => ({
        eq: () => ({
          single: () => Promise.resolve({
            data: mockUserRecord({ rectification_status: 'locked', current_confidence: 0.90 }),
            error: null,
          }),
        }),
      }),
    }))

    const res = await GET(makeRequest())
    expect(res.status).toBe(204)
  })

  it('returns 204 for PRECISE users (no rectification needed)', async () => {
    mockFrom.mockImplementation(() => ({
      select: () => ({
        eq: () => ({
          single: () => Promise.resolve({
            data: mockUserRecord({ accuracy_type: 'PRECISE', current_confidence: 0.90 }),
            error: null,
          }),
        }),
      }),
    }))

    const res = await GET(makeRequest())
    expect(res.status).toBe(204)
  })

  it('returns a question with correct shape for non-precise user', async () => {
    const res = await GET(makeRequest())
    const json = await res.json()

    expect(res.status).toBe(200)
    expect(json).toMatchObject({
      question_id: expect.any(String),
      phase: expect.stringMatching(/^(coarse|fine)$/),
      question_text: expect.any(String),
      options: expect.arrayContaining([
        expect.objectContaining({
          id: expect.stringMatching(/^[AB]$/),
          label: expect.any(String),
          eliminates: expect.any(Array),
        }),
      ]),
      context: expect.objectContaining({
        current_confidence: expect.any(Number),
        rectification_status: expect.any(String),
        is_boundary_case: expect.any(Boolean),
      }),
    })
  })

  it('returns exactly 2 options per question', async () => {
    const res = await GET(makeRequest())
    const json = await res.json()
    expect(json.options).toHaveLength(2)
    expect(json.options[0].id).toBe('A')
    expect(json.options[1].id).toBe('B')
  })

  it('prioritizes ascendant exclusion question for boundary case with asc/dsc change', async () => {
    mockFrom.mockImplementation(() => ({
      select: () => ({
        eq: () => ({
          single: () => Promise.resolve({
            data: mockUserRecord({
              is_boundary_case: true,
              rectification_status: 'collecting_signals',
            }),
            error: null,
          }),
        }),
      }),
    }))

    const res = await GET(makeRequest())
    const json = await res.json()

    expect(res.status).toBe(200)
    expect(json.question_id).toContain('ascendant')
  })
})
