import { apiClient } from './client'
import type { SetupStepResponse } from '@/types/api'
import type {
  SetupStatus,
  EncryptionKeyRequest,
  EncryptionKeyGenerateResponse,
  AdminCredentialsRequest,
  SSLRequest,
  ServerSetupRequest,
  DatabaseSetupRequest,
  CompleteSetupRequest,
  CertificateInfo,
  CertificateValidationResult,
} from '@/types/setup'

export const setupApi = {
  getStatus: () => apiClient.get<SetupStatus>('/api/setup/status'),

  generateEncryptionKey: () =>
    apiClient.get<EncryptionKeyGenerateResponse>('/api/setup/encryption-key/generate'),

  setEncryptionKey: (data: EncryptionKeyRequest) =>
    apiClient.post<SetupStepResponse>('/api/setup/encryption-key', data),

  setAdminCredentials: (data: AdminCredentialsRequest) =>
    apiClient.post<SetupStepResponse>('/api/setup/admin-credentials', data),

  setSSL: (data: SSLRequest) =>
    apiClient.post<SetupStepResponse>('/api/setup/ssl', data),

  setServer: (data: ServerSetupRequest) =>
    apiClient.post<SetupStepResponse>('/api/setup/server', data),

  setDatabase: (data: DatabaseSetupRequest) =>
    apiClient.post<SetupStepResponse>('/api/setup/database', data),

  complete: (data: CompleteSetupRequest) =>
    apiClient.post<SetupStepResponse>('/api/setup/complete', data),

  restart: () =>
    apiClient.post<SetupStepResponse>('/api/setup/restart'),

  getCertificate: () => apiClient.get<CertificateInfo>('/api/setup/certificate'),

  renewCertificate: () =>
    apiClient.post<SetupStepResponse>('/api/setup/certificate/renew'),

  uploadCertificate: (files: { certificate: File; private_key: File; chain?: File | null }) =>
    apiClient.uploadMultiple<SetupStepResponse>('/api/setup/ssl/upload', {
      certificate: files.certificate,
      private_key: files.private_key,
      chain: files.chain ?? null,
    }),

  validateCertificate: (files: { certificate: File; private_key: File; chain?: File | null }) =>
    apiClient.uploadMultiple<CertificateValidationResult>('/api/setup/ssl/validate', {
      certificate: files.certificate,
      private_key: files.private_key,
      chain: files.chain ?? null,
    }),
}
