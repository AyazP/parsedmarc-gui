import { apiClient } from './client'
import type {
  DatabaseInfo,
  DatabaseTestRequest,
  DatabaseTestResponse,
  DatabaseMigrateRequest,
  DatabaseMigrateResponse,
  DatabasePurgeResponse,
} from '@/types/settings'

export const settingsApi = {
  getDatabaseInfo: () =>
    apiClient.get<DatabaseInfo>('/api/settings/database'),

  testDatabaseConnection: (config: DatabaseTestRequest) =>
    apiClient.post<DatabaseTestResponse>('/api/settings/database/test', config),

  migrateDatabase: (config: DatabaseMigrateRequest) =>
    apiClient.post<DatabaseMigrateResponse>('/api/settings/database/migrate', config),

  purgeDatabase: () =>
    apiClient.post<DatabasePurgeResponse>('/api/settings/database/purge', {}),
}
