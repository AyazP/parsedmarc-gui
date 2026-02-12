import { apiClient } from './client'
import type { PaginatedResponse } from '@/types/api'
import type { ParseJob, ParsedReport, ParseMailboxRequest } from '@/types/parsing'

function buildQuery(params: Record<string, string | number | undefined>): string {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') {
      query.set(key, String(value))
    }
  }
  const qs = query.toString()
  return qs ? `?${qs}` : ''
}

export const parsingApi = {
  parseFromMailbox: (configId: number, data: ParseMailboxRequest) =>
    apiClient.post<ParseJob>(`/api/parse/mailbox/${configId}`, data),

  uploadFile: (file: File) => apiClient.upload<ParseJob>('/api/parse/upload', file),

  listJobs: (params: { skip?: number; limit?: number; status?: string } = {}) =>
    apiClient.get<ParseJob[]>(`/api/parse/jobs${buildQuery(params)}`),

  getJob: (id: number) => apiClient.get<ParseJob>(`/api/parse/jobs/${id}`),

  listReports: (
    params: {
      skip?: number
      limit?: number
      report_type?: string
      domain?: string
      org_name?: string
    } = {},
  ) => apiClient.get<PaginatedResponse<ParsedReport>>(`/api/parse/reports${buildQuery(params)}`),

  getReport: (id: number) => apiClient.get<ParsedReport>(`/api/parse/reports/${id}`),
}
