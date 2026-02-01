import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { AuthProvider } from '../context/AuthContext'
import { useAuth } from './useAuth'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock the auth API
vi.mock('../api/auth', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  refreshToken: vi.fn(),
  getMe: vi.fn(),
}))

import { login as loginApi, logout as logoutApi, getMe } from '../api/auth'

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <AuthProvider>{children}</AuthProvider>
)

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
  })

  it('returns isAuthenticated as false when no token', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('returns user as null when not authenticated', () => {
    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.user).toBeNull()
  })

  it('login sets user and isAuthenticated', async () => {
    const mockLoginApi = loginApi as ReturnType<typeof vi.fn>
    mockLoginApi.mockResolvedValueOnce({
      access_token: 'test-token',
      refresh_token: 'test-refresh',
      token_type: 'bearer',
    })

    const mockGetMe = getMe as ReturnType<typeof vi.fn>
    mockGetMe.mockResolvedValueOnce({ username: 'admin' })

    const { result } = renderHook(() => useAuth(), { wrapper })

    await act(async () => {
      await result.current.login('admin', 'password')
    })

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true)
      expect(result.current.user).toEqual({ username: 'admin' })
    })
  })

  it('logout clears user and token', async () => {
    const mockLogoutApi = logoutApi as ReturnType<typeof vi.fn>
    mockLogoutApi.mockResolvedValueOnce({})

    // First set up authenticated state
    localStorageMock.getItem.mockReturnValue('test-token')
    const mockGetMe = getMe as ReturnType<typeof vi.fn>
    mockGetMe.mockResolvedValueOnce({ username: 'admin' })

    const { result } = renderHook(() => useAuth(), { wrapper })

    await act(async () => {
      await result.current.logout()
    })

    expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token')
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('refresh_token')
  })

  it('isLoading is true during authentication check', () => {
    localStorageMock.getItem.mockReturnValue('test-token')
    const mockGetMe = getMe as ReturnType<typeof vi.fn>
    mockGetMe.mockImplementation(() => new Promise(() => {})) // Never resolves

    const { result } = renderHook(() => useAuth(), { wrapper })
    expect(result.current.isLoading).toBe(true)
  })
})
