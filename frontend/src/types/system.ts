export interface HealthStatus {
  status: string
  version: string
  monitoring_active: boolean
}

export interface SystemInfo {
  version: string
  database: string
  data_directory: string
}
