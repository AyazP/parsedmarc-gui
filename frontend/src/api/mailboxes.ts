import { apiClient } from './client'
import type {
  MailboxConfig,
  MailboxConfigCreate,
  MailboxConfigUpdate,
  ConnectionTestResult,
} from '@/types/mailbox'

export const mailboxApi = {
  list: () => apiClient.get<MailboxConfig[]>('/api/configs/mailboxes/'),

  get: (id: number) => apiClient.get<MailboxConfig>(`/api/configs/mailboxes/${id}`),

  create: (data: MailboxConfigCreate) =>
    apiClient.post<MailboxConfig>('/api/configs/mailboxes/', data),

  update: (id: number, data: MailboxConfigUpdate) =>
    apiClient.put<MailboxConfig>(`/api/configs/mailboxes/${id}`, data),

  delete: (id: number) => apiClient.delete<void>(`/api/configs/mailboxes/${id}`),

  testConnection: (id: number) =>
    apiClient.post<ConnectionTestResult>(`/api/configs/mailboxes/${id}/test`),
}
