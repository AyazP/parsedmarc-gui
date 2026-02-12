export type OutputType =
  | 'elasticsearch'
  | 'opensearch'
  | 'splunk'
  | 'kafka'
  | 's3'
  | 'syslog'
  | 'gelf'
  | 'webhook'

export interface ElasticsearchSettings {
  hosts: string[]
  username?: string
  password?: string
  api_key?: string
  ssl: boolean
  cert_path?: string
  index_suffix?: string
  monthly_indexes: boolean
}

export interface OpenSearchSettings {
  hosts: string[]
  username?: string
  password?: string
  ssl: boolean
  cert_path?: string
  index_suffix?: string
}

export interface SplunkSettings {
  url: string
  token: string
  index: string
  skip_certificate_verification: boolean
}

export interface KafkaSettings {
  servers: string[]
  aggregate_topic: string
  forensic_topic: string
  smtp_tls_topic: string
  ssl: boolean
  username?: string
  password?: string
}

export interface S3Settings {
  bucket: string
  region: string
  access_key_id?: string
  secret_access_key?: string
  prefix?: string
}

export interface SyslogSettings {
  server: string
  port: number
}

export interface GELFSettings {
  server: string
  port: number
}

export interface WebhookSettings {
  url: string
  headers?: Record<string, string>
  timeout: number
}

export interface OutputConfig {
  id: number
  name: string
  type: OutputType
  enabled: boolean
  save_aggregate: boolean
  save_forensic: boolean
  save_smtp_tls: boolean
  created_at: string
  updated_at: string
  elasticsearch_settings?: Record<string, unknown>
  opensearch_settings?: Record<string, unknown>
  splunk_settings?: Record<string, unknown>
  kafka_settings?: Record<string, unknown>
  s3_settings?: Record<string, unknown>
  syslog_settings?: Record<string, unknown>
  gelf_settings?: Record<string, unknown>
  webhook_settings?: Record<string, unknown>
}

export interface OutputConfigCreate {
  name: string
  type: OutputType
  enabled: boolean
  save_aggregate: boolean
  save_forensic: boolean
  save_smtp_tls: boolean
  elasticsearch_settings?: ElasticsearchSettings
  opensearch_settings?: OpenSearchSettings
  splunk_settings?: SplunkSettings
  kafka_settings?: KafkaSettings
  s3_settings?: S3Settings
  syslog_settings?: SyslogSettings
  gelf_settings?: GELFSettings
  webhook_settings?: WebhookSettings
}

export interface OutputConfigUpdate {
  name?: string
  enabled?: boolean
  save_aggregate?: boolean
  save_forensic?: boolean
  save_smtp_tls?: boolean
  elasticsearch_settings?: ElasticsearchSettings
  opensearch_settings?: OpenSearchSettings
  splunk_settings?: SplunkSettings
  kafka_settings?: KafkaSettings
  s3_settings?: S3Settings
  syslog_settings?: SyslogSettings
  gelf_settings?: GELFSettings
  webhook_settings?: WebhookSettings
}
