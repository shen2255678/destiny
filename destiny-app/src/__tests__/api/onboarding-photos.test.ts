// @vitest-environment node
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockGetUser = vi.fn()
const mockFrom = vi.fn()
const mockUpload = vi.fn()
const mockInsert = vi.fn()
const mockUpdate = vi.fn()

vi.mock('@/lib/supabase/server', () => ({
  createClient: vi.fn(async () => ({
    auth: { getUser: mockGetUser },
    from: mockFrom,
    storage: {
      from: () => ({ upload: mockUpload }),
    },
  })),
}))

vi.mock('sharp', () => ({
  default: vi.fn(() => ({
    blur: vi.fn().mockReturnThis(),
    jpeg: vi.fn().mockReturnThis(),
    toBuffer: vi.fn().mockResolvedValue(Buffer.from('blurred')),
  })),
}))

import { POST } from '@/app/api/onboarding/photos/route'

function makeFormData(files: Record<string, Blob>): Request {
  const form = new FormData()
  for (const [key, blob] of Object.entries(files)) {
    form.append(key, blob, `${key}.jpg`)
  }
  return new Request('http://localhost/api/onboarding/photos', {
    method: 'POST',
    body: form,
  })
}

describe('POST /api/onboarding/photos', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockGetUser.mockResolvedValue({
      data: { user: { id: 'user-uuid-123' } },
      error: null,
    })
    mockUpload.mockResolvedValue({ data: { path: 'photos/user-uuid-123/original_1.jpg' }, error: null })
    mockFrom.mockImplementation((table: string) => {
      if (table === 'photos') return { insert: mockInsert }
      if (table === 'users') return { update: mockUpdate }
      return {}
    })
    mockInsert.mockReturnValue({
      select: () => Promise.resolve({
        data: [{ id: 1 }],
        error: null,
      }),
    })
    mockUpdate.mockReturnValue({
      eq: () => Promise.resolve({ data: null, error: null }),
    })
  })

  it('uploads 2 photos with blur processing and saves to DB', async () => {
    const photo1 = new Blob(['fake-image-1'], { type: 'image/jpeg' })
    const photo2 = new Blob(['fake-image-2'], { type: 'image/jpeg' })

    const res = await POST(makeFormData({ photo1, photo2 }))
    expect(res.status).toBe(200)

    // Should upload 4 files: 2 originals + 2 blurred
    expect(mockUpload).toHaveBeenCalledTimes(4)

    // Should insert 2 photo records
    expect(mockInsert).toHaveBeenCalled()

    // Should update onboarding_step
    expect(mockFrom).toHaveBeenCalledWith('users')
  })

  it('returns 401 when not authenticated', async () => {
    mockGetUser.mockResolvedValue({
      data: { user: null },
      error: { message: 'Not authenticated' },
    })

    const photo1 = new Blob(['fake'], { type: 'image/jpeg' })
    const photo2 = new Blob(['fake'], { type: 'image/jpeg' })

    const res = await POST(makeFormData({ photo1, photo2 }))
    expect(res.status).toBe(401)
  })

  it('returns 400 when photos are missing', async () => {
    const res = await POST(makeFormData({}))
    expect(res.status).toBe(400)
  })

  it('returns 400 for non-image MIME type', async () => {
    const textFile = new Blob(['not an image'], { type: 'text/plain' })
    const photo2 = new Blob(['fake-image'], { type: 'image/jpeg' })

    const form = new FormData()
    form.append('photo1', textFile, 'document.txt')
    form.append('photo2', photo2, 'photo2.jpg')

    const req = new Request('http://localhost/api/onboarding/photos', {
      method: 'POST',
      body: form,
    })
    const res = await POST(req)
    const json = await res.json()

    expect(res.status).toBe(400)
    expect(json.error).toContain('Invalid file type')
  })

  it('returns 400 for oversized file', async () => {
    // Create a blob > 10MB using Uint8Array (more reliable in jsdom)
    const bigBlob = new Blob([new Uint8Array(11 * 1024 * 1024)], { type: 'image/jpeg' })
    const photo2 = new Blob(['fake-image'], { type: 'image/jpeg' })

    const form = new FormData()
    form.append('photo1', bigBlob, 'big.jpg')
    form.append('photo2', photo2, 'photo2.jpg')

    const req = new Request('http://localhost/api/onboarding/photos', {
      method: 'POST',
      body: form,
    })
    const res = await POST(req)
    const json = await res.json()

    expect(res.status).toBe(400)
    expect(json.error).toContain('too large')
  })
})
