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

import { GET, POST } from '@/app/api/connections/[id]/messages/route'

const MOCK_USER_ID = 'user-a'
const MOCK_CONN_ID = 'conn-uuid-1'

const MOCK_CONNECTION = {
  id: MOCK_CONN_ID,
  user_a_id: MOCK_USER_ID,
  user_b_id: 'user-b',
  match_id: 'match-uuid-1',
  sync_level: 1,
  message_count: 2,
  status: 'active',
  last_activity: new Date().toISOString(),
}

const MOCK_MESSAGES = [
  { id: 'msg-1', connection_id: MOCK_CONN_ID, sender_id: 'user-b', content: 'Hello!', created_at: new Date().toISOString() },
  { id: 'msg-2', connection_id: MOCK_CONN_ID, sender_id: MOCK_USER_ID, content: 'Hi there', created_at: new Date().toISOString() },
]

const MOCK_OTHER_USER = {
  id: 'user-b',
  archetype_name: 'The Anchor',
  display_name: null,
}

const MOCK_MATCH = {
  id: 'match-uuid-1',
  tags: ['Tender', 'Grounding'],
}

function makeRequest(method: string, body?: Record<string, unknown>) {
  return new Request(`http://localhost/api/connections/${MOCK_CONN_ID}/messages`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
}

describe('GET /api/connections/:id/messages', () => {
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
            eq: () => ({
              single: () => Promise.resolve({ data: MOCK_CONNECTION, error: null }),
            }),
          }),
        }
      }
      if (table === 'messages') {
        return {
          select: () => ({
            eq: () => ({
              order: () => ({
                limit: () => Promise.resolve({ data: MOCK_MESSAGES, error: null }),
              }),
            }),
          }),
          insert: () => ({
            select: () => ({
              single: () => Promise.resolve({
                data: { id: 'msg-new', connection_id: MOCK_CONN_ID, sender_id: MOCK_USER_ID, content: 'New message', created_at: new Date().toISOString() },
                error: null,
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
            eq: () => ({
              single: () => Promise.resolve({ data: MOCK_OTHER_USER, error: null }),
            }),
          }),
        }
      }
      if (table === 'daily_matches') {
        return {
          select: () => ({
            eq: () => ({
              single: () => Promise.resolve({ data: MOCK_MATCH, error: null }),
            }),
          }),
        }
      }
      if (table === 'photos') {
        return {
          select: () => ({
            eq: () => ({
              eq: () => ({
                single: () => Promise.resolve({
                  data: { blurred_path: 'user-b/blurred_1.jpg' },
                  error: null,
                }),
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
    const res = await GET(makeRequest('GET'), { params: Promise.resolve({ id: MOCK_CONN_ID }) })
    expect(res.status).toBe(401)
  })

  it('returns 403 when user is not part of this connection', async () => {
    mockFrom.mockImplementation((table: string) => {
      if (table === 'connections') {
        return {
          select: () => ({
            eq: () => ({
              single: () => Promise.resolve({
                data: { ...MOCK_CONNECTION, user_a_id: 'stranger-1', user_b_id: 'stranger-2' },
                error: null,
              }),
            }),
          }),
        }
      }
      return {}
    })

    const res = await GET(makeRequest('GET'), { params: Promise.resolve({ id: MOCK_CONN_ID }) })
    expect(res.status).toBe(403)
  })

  it('returns connection detail and messages', async () => {
    const res = await GET(makeRequest('GET'), { params: Promise.resolve({ id: MOCK_CONN_ID }) })
    const json = await res.json()

    expect(res.status).toBe(200)
    expect(json.connection).toMatchObject({
      id: MOCK_CONN_ID,
      sync_level: 1,
      message_count: 2,
    })
    expect(Array.isArray(json.messages)).toBe(true)
    expect(json.messages).toHaveLength(2)
  })

  it('marks messages with is_self flag', async () => {
    const res = await GET(makeRequest('GET'), { params: Promise.resolve({ id: MOCK_CONN_ID }) })
    const json = await res.json()

    const selfMsg = json.messages.find((m: any) => m.sender_id === MOCK_USER_ID)
    const otherMsg = json.messages.find((m: any) => m.sender_id !== MOCK_USER_ID)
    expect(selfMsg.is_self).toBe(true)
    expect(otherMsg.is_self).toBe(false)
  })
})

describe('POST /api/connections/:id/messages', () => {
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
            eq: () => ({
              single: () => Promise.resolve({ data: MOCK_CONNECTION, error: null }),
            }),
          }),
        }
      }
      if (table === 'messages') {
        return {
          insert: () => ({
            select: () => ({
              single: () => Promise.resolve({
                data: { id: 'msg-new', connection_id: MOCK_CONN_ID, sender_id: MOCK_USER_ID, content: 'New message', created_at: new Date().toISOString() },
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
    const res = await POST(makeRequest('POST', { content: 'Hello' }), { params: Promise.resolve({ id: MOCK_CONN_ID }) })
    expect(res.status).toBe(401)
  })

  it('returns 400 when content is missing', async () => {
    const res = await POST(makeRequest('POST', {}), { params: Promise.resolve({ id: MOCK_CONN_ID }) })
    expect(res.status).toBe(400)
  })

  it('returns 403 when user is not part of this connection', async () => {
    mockFrom.mockImplementation((table: string) => {
      if (table === 'connections') {
        return {
          select: () => ({
            eq: () => ({
              single: () => Promise.resolve({
                data: { ...MOCK_CONNECTION, user_a_id: 'stranger-1', user_b_id: 'stranger-2' },
                error: null,
              }),
            }),
          }),
        }
      }
      return {}
    })

    const res = await POST(makeRequest('POST', { content: 'Hello' }), { params: Promise.resolve({ id: MOCK_CONN_ID }) })
    expect(res.status).toBe(403)
  })

  it('inserts message and returns it', async () => {
    const res = await POST(makeRequest('POST', { content: 'New message' }), { params: Promise.resolve({ id: MOCK_CONN_ID }) })
    const json = await res.json()

    expect(res.status).toBe(201)
    expect(json.message).toMatchObject({
      id: 'msg-new',
      sender_id: MOCK_USER_ID,
      content: 'New message',
    })
  })
})
