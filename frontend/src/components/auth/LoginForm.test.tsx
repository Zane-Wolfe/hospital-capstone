import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import LoginForm from './LoginForm'
import { AuthProvider } from '../../context/AuthContext'
import { BrowserRouter } from 'react-router-dom'

// Mock the auth API
vi.mock('../../api/auth', () => ({
  login: vi.fn(),
}))

import { login } from '../../api/auth'

const renderLoginForm = (onSuccess = vi.fn()) => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <LoginForm onSuccess={onSuccess} />
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders login form with username and password fields', () => {
    renderLoginForm()
    
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows validation error when submitting empty form', async () => {
    renderLoginForm()
    
    const submitButton = screen.getByRole('button', { name: /sign in/i })
    await userEvent.click(submitButton)
    
    // Form should not submit with empty fields due to required attribute
    expect(login).not.toHaveBeenCalled()
  })

  it('calls login API with correct credentials', async () => {
    const mockLogin = login as ReturnType<typeof vi.fn>
    mockLogin.mockResolvedValueOnce({
      access_token: 'test-token',
      refresh_token: 'test-refresh',
      token_type: 'bearer',
    })

    const onSuccess = vi.fn()
    renderLoginForm(onSuccess)

    await userEvent.type(screen.getByLabelText(/username/i), 'admin')
    await userEvent.type(screen.getByLabelText(/password/i), 'password123')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('admin', 'password123')
    })
  })

  it('displays error message on login failure', async () => {
    const mockLogin = login as ReturnType<typeof vi.fn>
    mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'))

    renderLoginForm()

    await userEvent.type(screen.getByLabelText(/username/i), 'admin')
    await userEvent.type(screen.getByLabelText(/password/i), 'wrongpassword')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText(/invalid username or password/i)).toBeInTheDocument()
    })
  })

  it('disables submit button while loading', async () => {
    const mockLogin = login as ReturnType<typeof vi.fn>
    mockLogin.mockImplementation(() => new Promise(() => {})) // Never resolves

    renderLoginForm()

    await userEvent.type(screen.getByLabelText(/username/i), 'admin')
    await userEvent.type(screen.getByLabelText(/password/i), 'password123')
    await userEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /signing in/i })).toBeDisabled()
    })
  })
})
