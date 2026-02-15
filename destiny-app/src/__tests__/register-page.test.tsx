import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mock next/navigation
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}))

// Mock auth functions
const mockRegister = vi.fn()
vi.mock('@/lib/auth', () => ({
  register: (...args: unknown[]) => mockRegister(...args),
}))

import RegisterPage from '@/app/register/page'

describe('Register Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all form fields', () => {
    render(<RegisterPage />)

    expect(screen.getByLabelText('Email address')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirm password')).toBeInTheDocument()
    expect(screen.getByText('男性')).toBeInTheDocument()
    expect(screen.getByText('女性')).toBeInTheDocument()
    expect(screen.getByText('非二元')).toBeInTheDocument()
  })

  it('calls register and redirects on success', async () => {
    mockRegister.mockResolvedValue({
      data: { user: { id: 'uuid-456', email: 'new@example.com' } },
      error: null,
    })
    const user = userEvent.setup()
    render(<RegisterPage />)

    await user.type(screen.getByLabelText('Email address'), 'new@example.com')
    await user.type(screen.getByLabelText('Password'), 'Password123!')
    await user.type(screen.getByLabelText('Confirm password'), 'Password123!')
    await user.click(screen.getByText('女性'))
    await user.click(screen.getByRole('button', { name: /create your destiny account/i }))

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith('new@example.com', 'Password123!')
    })
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/onboarding/birth-data')
    })
  })

  it('displays error message on registration failure', async () => {
    mockRegister.mockResolvedValue({
      data: { user: null },
      error: { message: 'User already registered' },
    })
    const user = userEvent.setup()
    render(<RegisterPage />)

    await user.type(screen.getByLabelText('Email address'), 'existing@example.com')
    await user.type(screen.getByLabelText('Password'), 'Password123!')
    await user.type(screen.getByLabelText('Confirm password'), 'Password123!')
    await user.click(screen.getByText('男性'))
    await user.click(screen.getByRole('button', { name: /create your destiny account/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('User already registered')
    })
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('prevents submission when passwords do not match', async () => {
    const user = userEvent.setup()
    render(<RegisterPage />)

    await user.type(screen.getByLabelText('Password'), 'Password123!')
    await user.type(screen.getByLabelText('Confirm password'), 'Different123!')

    expect(screen.getByRole('button', { name: /create your destiny account/i })).toBeDisabled()
    expect(screen.getByText('Passwords do not match.')).toBeInTheDocument()
  })

  it('shows loading state during submission', async () => {
    mockRegister.mockReturnValue(new Promise(() => {}))
    const user = userEvent.setup()
    render(<RegisterPage />)

    await user.type(screen.getByLabelText('Email address'), 'new@example.com')
    await user.type(screen.getByLabelText('Password'), 'Password123!')
    await user.type(screen.getByLabelText('Confirm password'), 'Password123!')
    await user.click(screen.getByText('女性'))
    await user.click(screen.getByRole('button', { name: /create your destiny account/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /create your destiny account/i })).toBeDisabled()
    })
  })
})
