export type MailboxType = 'imap' | 'msgraph' | 'gmail' | 'maildir'

export interface IMAPSettings {
  host: string
  port: number
  username: string
  password: string
  ssl: boolean
  skip_certificate_verification: boolean
  folder: string
  batch_size: number
}

export interface MSGraphSettings {
  auth_method: 'DeviceCode' | 'ClientSecret' | 'UsernamePassword'
  tenant_id: string
  client_id: string
  client_secret?: string
  username?: string
  password?: string
  mailbox: string
  token_file?: string
  graph_url: string
  batch_size: number
}

export interface GmailSettings {
  credentials_file: string
  token_file?: string
  scopes: string[]
  include_spam_trash: boolean
  batch_size: number
}

export interface MaildirSettings {
  path: string
}

export interface MailboxConfig {
  id: number
  name: string
  type: MailboxType
  enabled: boolean
  delete_after_processing: boolean
  watch_interval: number
  created_at: string
  updated_at: string
  imap_settings?: Record<string, unknown>
  msgraph_settings?: Record<string, unknown>
  gmail_settings?: Record<string, unknown>
  maildir_settings?: Record<string, unknown>
}

export interface MailboxConfigCreate {
  name: string
  type: MailboxType
  enabled: boolean
  delete_after_processing: boolean
  watch_interval: number
  imap_settings?: IMAPSettings
  msgraph_settings?: MSGraphSettings
  gmail_settings?: GmailSettings
  maildir_settings?: MaildirSettings
}

export interface MailboxConfigUpdate {
  name?: string
  enabled?: boolean
  delete_after_processing?: boolean
  watch_interval?: number
  imap_settings?: IMAPSettings
  msgraph_settings?: MSGraphSettings
  gmail_settings?: GmailSettings
  maildir_settings?: MaildirSettings
}

export interface ConnectionTestResult {
  success: boolean
  message: string
  details?: Record<string, unknown>
}
