export interface SetupStatus {
  is_complete: boolean
  setup_version: string
  encryption_key_set: boolean
  admin_credentials_set: boolean
  ssl_configured: boolean
  database_configured: boolean
  server_configured: boolean
  ssl_type: string | null
  ssl_domain: string | null
  completed_at: string | null
  needs_setup: boolean
}

export interface EncryptionKeyRequest {
  encryption_key?: string
}

export interface EncryptionKeyGenerateResponse {
  success: boolean
  encryption_key: string
  message: string
}

export interface AdminCredentialsRequest {
  username: string
  password: string
  confirm_password: string
}

export type SSLType = 'self-signed' | 'letsencrypt' | 'custom' | 'skip'

export interface SSLSelfSignedRequest {
  type: 'self-signed'
  common_name: string
  organization: string
  validity_days: number
}

export interface SSLLetsEncryptRequest {
  type: 'letsencrypt'
  domain: string
  email: string
  staging: boolean
  webroot_path?: string
}

export interface SSLCustomRequest {
  type: 'custom'
  certificate_path: string
  private_key_path: string
  chain_path?: string
}

export type SSLRequest = SSLSelfSignedRequest | SSLLetsEncryptRequest | SSLCustomRequest

export interface ServerSetupRequest {
  host: string
  port: number
  cors_origins: string
  log_level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
}

export interface DatabaseSetupRequest {
  db_path: string
}

export interface CompleteSetupRequest {
  encryption_key?: string
  admin_username: string
  admin_password: string
  ssl_type: SSLType
  ssl_domain?: string
  ssl_email?: string
  ssl_staging?: boolean
  ssl_common_name?: string
  ssl_certificate_path?: string
  ssl_private_key_path?: string
  host: string
  port: number
  cors_origins: string
  log_level: string
  db_path: string
}

export interface CertificateInfo {
  type: string
  certificate?: string
  private_key?: string
  subject?: string
  issuer?: string
  expires?: string
  is_expired?: boolean
  days_until_expiry?: number
  is_self_signed?: boolean
  error?: string
}
