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

import { POST } from '@/app/api/onboarding/rpv-test/route'

function makeRequest(body: Record<string, unknown>) {
  return new Request('http://localhost/api/onboarding/rpv-test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

describe('POST /api/onboarding/rpv-test', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetUser.mockResolvedValue({
      data: { user: { id: 'user-uuid-123' } },
      error: null,
    })
    mockFrom.mockReturnValue({ update: mockUpdate })
    mockUpdate.mockReturnValue({
      eq: () => ({
        select: () => ({
          single: () => Promise.resolve({
            data: { id: 'user-uuid-123', rpv_conflict: 'cold_war' },
            error: null,
          }),
        }),
      }),
    })
  })

  it('saves RPV results mapped from option IDs', async () => {
    const res = await POST(makeRequest({
      rpv_conflict: 'cold_war',
      rpv_power: 'control',
      rpv_energy: 'home',
    }))

    expect(res.status).toBe(200)
    expect(mockFrom).toHaveBeenCalledWith('users')
    expect(mockUpdate).toHaveBeenCalledWith({
      rpv_conflict: 'cold_war',
      rpv_power: 'control',
      rpv_energy: 'home',
      onboarding_step: 'photos',
    })
  })

  it('returns 401 when not authenticated', async () => {
    mockGetUser.mockResolvedValue({
      data: { user: null },
      error: { message: 'Not authenticated' },
    })

    const res = await POST(makeRequest({
      rpv_conflict: 'cold_war',
      rpv_power: 'control',
      rpv_energy: 'home',
    }))

    expect(res.status).toBe(401)
  })

  it('returns 400 when RPV fields are missing', async () => {
    const res = await POST(makeRequest({
      rpv_conflict: 'cold_war',
      // missing rpv_power and rpv_energy
    }))

    expect(res.status).toBe(400)
  })
})
