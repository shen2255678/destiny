import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGetUser = vi.fn()
const mockUpdate = vi.fn()
const mockFrom = vi.fn()

vi.mock('@/lib/supabase/server', () => ({
  createClient: vi.fn(async () => ({
    auth: { getUser: mockGetUser },
    from: mockFrom,
  })),
}))

import { POST } from '@/app/api/onboarding/attachment/route'

function makeRequest(body: Record<string, unknown>) {
  return new Request('http://localhost/api/onboarding/attachment', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

describe('POST /api/onboarding/attachment', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetUser.mockResolvedValue({
      data: { user: { id: 'user-uuid-123' } },
      error: null,
    })
    mockFrom.mockReturnValue({ update: mockUpdate })
    mockUpdate.mockReturnValue({
      eq: () => Promise.resolve({ error: null }),
    })
  })

  it('returns 400 if attachment_style is missing', async () => {
    const res = await POST(makeRequest({}))
    expect(res.status).toBe(400)
    const json = await res.json()
    expect(json.error).toMatch(/attachment_style/)
  })

  it('returns 400 for invalid attachment_style value', async () => {
    const res = await POST(makeRequest({ attachment_style: 'invalid' }))
    expect(res.status).toBe(400)
    const json = await res.json()
    expect(json.error).toMatch(/Invalid attachment_style/)
  })

  it('returns 200 and calls supabase update for valid data (secure)', async () => {
    const res = await POST(makeRequest({ attachment_style: 'secure' }))
    expect(res.status).toBe(200)
    const json = await res.json()
    expect(json.success).toBe(true)
    expect(mockFrom).toHaveBeenCalledWith('users')
    expect(mockUpdate).toHaveBeenCalledWith({
      attachment_style: 'secure',
      onboarding_step: 'photos',
    })
  })

  it('returns 200 for all three valid styles', async () => {
    for (const style of ['anxious', 'avoidant', 'secure'] as const) {
      vi.clearAllMocks()
      mockGetUser.mockResolvedValue({
        data: { user: { id: 'user-uuid-123' } },
        error: null,
      })
      mockFrom.mockReturnValue({ update: mockUpdate })
      mockUpdate.mockReturnValue({
        eq: () => Promise.resolve({ error: null }),
      })

      const res = await POST(makeRequest({ attachment_style: style }))
      expect(res.status).toBe(200)
      const json = await res.json()
      expect(json.success).toBe(true)
    }
  })

  it('returns 401 when not authenticated', async () => {
    mockGetUser.mockResolvedValue({
      data: { user: null },
      error: { message: 'Not authenticated' },
    })

    const res = await POST(makeRequest({ attachment_style: 'secure' }))
    expect(res.status).toBe(401)
    const json = await res.json()
    expect(json.error).toBe('Not authenticated')
  })

  it('includes attachment_role in update when provided and valid', async () => {
    const res = await POST(makeRequest({
      attachment_style: 'anxious',
      attachment_role: 'dom_secure',
    }))
    expect(res.status).toBe(200)
    expect(mockUpdate).toHaveBeenCalledWith({
      attachment_style: 'anxious',
      attachment_role: 'dom_secure',
      onboarding_step: 'photos',
    })
  })

  it('returns 400 for invalid attachment_role value', async () => {
    const res = await POST(makeRequest({
      attachment_style: 'secure',
      attachment_role: 'bad_role',
    }))
    expect(res.status).toBe(400)
    const json = await res.json()
    expect(json.error).toMatch(/Invalid attachment_role/)
  })
})
