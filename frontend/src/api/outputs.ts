import { apiClient } from './client'
import type { OutputConfig, OutputConfigCreate, OutputConfigUpdate } from '@/types/output'

export const outputApi = {
  list: () => apiClient.get<OutputConfig[]>('/api/configs/outputs/'),

  get: (id: number) => apiClient.get<OutputConfig>(`/api/configs/outputs/${id}`),

  create: (data: OutputConfigCreate) =>
    apiClient.post<OutputConfig>('/api/configs/outputs/', data),

  update: (id: number, data: OutputConfigUpdate) =>
    apiClient.put<OutputConfig>(`/api/configs/outputs/${id}`, data),

  delete: (id: number) => apiClient.delete<void>(`/api/configs/outputs/${id}`),
}
