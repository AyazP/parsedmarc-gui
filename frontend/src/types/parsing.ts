export type JobStatus = 'pending' | 'running' | 'completed' | 'failed'
export type ReportType = 'aggregate' | 'forensic' | 'smtp_tls'

export interface ParseJob {
  id: number
  job_type: string
  status: JobStatus
  input_source: string | null
  file_path: string | null
  aggregate_reports_count: number
  forensic_reports_count: number
  smtp_tls_reports_count: number
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface ParsedReport {
  id: number
  parse_job_id: number | null
  report_type: ReportType
  org_name: string | null
  report_id: string | null
  domain: string | null
  date_begin: string | null
  date_end: string | null
  report_json: unknown
  created_at: string
}

export interface ParseMailboxRequest {
  batch_size?: number
  since?: string
  test_mode: boolean
}

export interface ReportFilters {
  report_type?: string
  domain?: string
  org_name?: string
}
