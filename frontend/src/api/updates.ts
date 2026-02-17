import { apiClient } from './client'
import type { UpdateStatus, UpdateSettings } from '@/types/updates'

export const updatesApi = {
  getStatus: () => apiClient.get<UpdateStatus>('/api/updates/status'),
  checkNow: () => apiClient.post<UpdateStatus>('/api/updates/check'),
  getSettings: () => apiClient.get<UpdateSettings>('/api/updates/settings'),
}
