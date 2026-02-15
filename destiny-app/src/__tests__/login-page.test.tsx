import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mock next/navigation
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

// Mock auth functions
const mockLogin = vi.fn()
vi.mock('@/lib/auth', () => ({
  login: (...args: unknown[]) => mockLogin(...args),
}))

import LoginPage from '@/app/login/page'

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders email and password fields', () => {
    render(<LoginPage />)

    expect(screen.getByLabelText('Email address')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
  })

  it('calls login and redirects on success', async () => {
    mockLogin.mockResolvedValue({
      data: { user: { id: 'uuid-123' }, session: { access_token: 'tok' } },
      error: null,
    })
    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText('Email address'), 'test@example.com')
    await user.type(screen.getByLabelText('Password'), 'Password123!')
    await user.click(screen.getByRole('button', { name: /login to your account/i }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'Password123!')
    })
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/daily')
    })
  })

  it('displays error message on login failure', async () => {
    mockLogin.mockResolvedValue({
      data: { user: null, session: null },
      error: { message: 'Invalid login credentials' },
    })
    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText('Email address'), 'test@example.com')
    await user.type(screen.getByLabelText('Password'), 'wrong-password')
    await user.click(screen.getByRole('button', { name: /login to your account/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Invalid login credentials')
    })
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('shows loading state during submission', async () => {
    // Never resolves during this test
    mockLogin.mockReturnValue(new Promise(() => {}))
    const user = userEvent.setup()
    render(<LoginPage />)

    await user.type(screen.getByLabelText('Email address'), 'test@example.com')
    await user.type(screen.getByLabelText('Password'), 'Password123!')
    await user.click(screen.getByRole('button', { name: /login to your account/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /login to your account/i })).toBeDisabled()
    })
  })
})
