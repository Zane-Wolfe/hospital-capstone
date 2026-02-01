import client from './client'
import type { AuthTokens, User } from '../types'

export const login = async (username: string, password: string): Promise<AuthTokens> => {
  const response = await client.post<AuthTokens>('/api/auth/login', {
    username,
    password,
  })
  return response.data
}

export const logout = async (): Promise<void> => {
  await client.post('/api/auth/logout')
}

export const refreshToken = async (refresh_token: string): Promise<AuthTokens> => {
  const response = await client.post<AuthTokens>('/api/auth/refresh', {
    refresh_token,
  })
  return response.data
}

export const getCurrentUser = async (): Promise<User> => {
  const response = await client.get<User>('/api/auth/me')
  return response.data
}
