export interface DatabaseInfo {
  db_type: string
  connection_string: string
  table_counts: Record<string, number>
}

export interface DatabaseTestRequest {
  db_type: 'postgresql' | 'mysql'
  host: string
  port: number
  database: string
  username: string
  password: string
}

export interface DatabaseMigrateRequest extends DatabaseTestRequest {
  migrate_data: boolean
}

export interface DatabaseTestResponse {
  success: boolean
  message: string
  details?: Record<string, string>
}

export interface DatabaseMigrateResponse {
  success: boolean
  message: string
  tables_migrated: number
  row_counts?: Record<string, number>
  restart_required: boolean
}

export interface DatabasePurgeResponse {
  success: boolean
  message: string
  rows_deleted?: Record<string, number>
}
