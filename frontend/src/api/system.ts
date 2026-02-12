import { apiClient } from './client'
import type { HealthStatus, SystemInfo } from '@/types/system'

export const systemApi = {
  health: () => apiClient.get<HealthStatus>('/api/health'),
  systemInfo: () => apiClient.get<SystemInfo>('/api/system/info'),
}
