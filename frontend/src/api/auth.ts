import { apiClient } from './client'

export interface LoginResponse {
  success: boolean
  user: { username: string }
}

export interface UserResponse {
  username: string
}

export const authApi = {
  login: (username: string, password: string) =>
    apiClient.post<LoginResponse>('/api/auth/login', { username, password }),

  logout: () =>
    apiClient.post<{ success: boolean }>('/api/auth/logout'),

  me: () =>
    apiClient.get<UserResponse>('/api/auth/me'),
}
