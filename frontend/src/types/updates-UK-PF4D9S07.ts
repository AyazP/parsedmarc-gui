export interface UpdateStatus {
  update_available: boolean
  current_version: string
  latest_version: string
  release_url: string
  release_notes: string
  published_at: string | null
  checked_at: string | null
  is_docker: boolean
  error: string | null
}

export interface UpdateSettings {
  enabled: boolean
  interval_hours: number
  is_docker: boolean
}
