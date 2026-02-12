"""Pydantic schemas for output configuration."""
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# Settings schemas for each output type
class ElasticsearchSettings(BaseModel):
    """Elasticsearch output settings."""
    hosts: list[str] = Field(..., description="List of Elasticsearch hosts")
    username: Optional[str] = Field(None, description="Elasticsearch username")
    password: Optional[str] = Field(None, description="Elasticsearch password")
    api_key: Optional[str] = Field(None, description="Elasticsearch API key")
    ssl: bool = Field(default=True, description="Use SSL/TLS")
    cert_path: Optional[str] = Field(None, description="Path to SSL certificate")
    index_suffix: Optional[str] = Field(None, description="Custom index suffix")
    monthly_indexes: bool = Field(default=True, description="Use monthly indexes")


class OpenSearchSettings(BaseModel):
    """OpenSearch output settings."""
    hosts: list[str] = Field(..., description="List of OpenSearch hosts")
    username: Optional[str] = Field(None, description="OpenSearch username")
    password: Optional[str] = Field(None, description="OpenSearch password")
    ssl: bool = Field(default=True, description="Use SSL/TLS")
    cert_path: Optional[str] = Field(None, description="Path to SSL certificate")
    index_suffix: Optional[str] = Field(None, description="Custom index suffix")


class SplunkSettings(BaseModel):
    """Splunk HEC output settings."""
    url: str = Field(..., description="Splunk HEC URL")
    token: str = Field(..., description="Splunk HEC token")
    index: str = Field(..., description="Splunk index name")
    skip_certificate_verification: bool = Field(default=False, description="Skip SSL certificate verification")


class KafkaSettings(BaseModel):
    """Kafka output settings."""
    servers: list[str] = Field(..., description="List of Kafka broker addresses")
    aggregate_topic: str = Field(default="dmarc_aggregate", description="Topic for aggregate reports")
    forensic_topic: str = Field(default="dmarc_forensic", description="Topic for forensic reports")
    smtp_tls_topic: str = Field(default="smtp_tls", description="Topic for SMTP TLS reports")
    ssl: bool = Field(default=False, description="Use SSL/TLS")
    username: Optional[str] = Field(None, description="SASL username")
    password: Optional[str] = Field(None, description="SASL password")


class S3Settings(BaseModel):
    """AWS S3 output settings."""
    bucket: str = Field(..., description="S3 bucket name")
    region: str = Field(default="us-east-1", description="AWS region")
    access_key_id: Optional[str] = Field(None, description="AWS access key ID")
    secret_access_key: Optional[str] = Field(None, description="AWS secret access key")
    prefix: Optional[str] = Field(None, description="S3 key prefix")


class SyslogSettings(BaseModel):
    """Syslog output settings."""
    server: str = Field(..., description="Syslog server address")
    port: int = Field(default=514, description="Syslog port")


class GELFSettings(BaseModel):
    """GELF (Graylog) output settings."""
    server: str = Field(..., description="GELF server address")
    port: int = Field(default=12201, description="GELF port")


class WebhookSettings(BaseModel):
    """Webhook output settings."""
    url: str = Field(..., description="Webhook URL")
    headers: Optional[dict[str, str]] = Field(default=None, description="Custom HTTP headers")
    timeout: int = Field(default=30, description="Request timeout in seconds")


# Base schema for output config
class OutputConfigBase(BaseModel):
    """Base schema for output configuration."""
    name: str = Field(..., min_length=1, max_length=255, description="Unique name for this output")
    type: Literal[
        "elasticsearch", "opensearch", "splunk", "kafka", "s3", "syslog", "gelf", "webhook"
    ] = Field(..., description="Output destination type")
    enabled: bool = Field(default=True, description="Whether this output is enabled")
    save_aggregate: bool = Field(default=True, description="Save aggregate reports to this output")
    save_forensic: bool = Field(default=True, description="Save forensic reports to this output")
    save_smtp_tls: bool = Field(default=True, description="Save SMTP TLS reports to this output")


class OutputConfigCreate(OutputConfigBase):
    """Schema for creating an output configuration."""
    elasticsearch_settings: Optional[ElasticsearchSettings] = None
    opensearch_settings: Optional[OpenSearchSettings] = None
    splunk_settings: Optional[SplunkSettings] = None
    kafka_settings: Optional[KafkaSettings] = None
    s3_settings: Optional[S3Settings] = None
    syslog_settings: Optional[SyslogSettings] = None
    gelf_settings: Optional[GELFSettings] = None
    webhook_settings: Optional[WebhookSettings] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Production Elasticsearch",
                "type": "elasticsearch",
                "enabled": True,
                "save_aggregate": True,
                "save_forensic": True,
                "save_smtp_tls": True,
                "elasticsearch_settings": {
                    "hosts": ["https://elasticsearch.company.com:9200"],
                    "username": "parsedmarc",
                    "password": "secret",
                    "ssl": True,
                    "monthly_indexes": True
                }
            }
        }


class OutputConfigUpdate(BaseModel):
    """Schema for updating an output configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    enabled: Optional[bool] = None
    save_aggregate: Optional[bool] = None
    save_forensic: Optional[bool] = None
    save_smtp_tls: Optional[bool] = None
    elasticsearch_settings: Optional[ElasticsearchSettings] = None
    opensearch_settings: Optional[OpenSearchSettings] = None
    splunk_settings: Optional[SplunkSettings] = None
    kafka_settings: Optional[KafkaSettings] = None
    s3_settings: Optional[S3Settings] = None
    syslog_settings: Optional[SyslogSettings] = None
    gelf_settings: Optional[GELFSettings] = None
    webhook_settings: Optional[WebhookSettings] = None


class OutputConfigResponse(OutputConfigBase):
    """Schema for output configuration response (passwords hidden)."""
    id: int
    created_at: datetime
    updated_at: datetime
    elasticsearch_settings: Optional[dict] = None
    opensearch_settings: Optional[dict] = None
    splunk_settings: Optional[dict] = None
    kafka_settings: Optional[dict] = None
    s3_settings: Optional[dict] = None
    syslog_settings: Optional[dict] = None
    gelf_settings: Optional[dict] = None
    webhook_settings: Optional[dict] = None

    class Config:
        from_attributes = True
