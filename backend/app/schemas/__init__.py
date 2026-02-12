"""Pydantic schemas for API validation."""
from .mailbox_config import (
    MailboxConfigBase,
    MailboxConfigCreate,
    MailboxConfigUpdate,
    MailboxConfigResponse,
    IMAPSettings,
    MSGraphSettings,
    GmailSettings,
    MaildirSettings
)
from .output_config import (
    OutputConfigBase,
    OutputConfigCreate,
    OutputConfigUpdate,
    OutputConfigResponse,
    ElasticsearchSettings,
    OpenSearchSettings,
    SplunkSettings,
    KafkaSettings,
    S3Settings,
    SyslogSettings,
    GELFSettings,
    WebhookSettings
)

__all__ = [
    "MailboxConfigBase",
    "MailboxConfigCreate",
    "MailboxConfigUpdate",
    "MailboxConfigResponse",
    "IMAPSettings",
    "MSGraphSettings",
    "GmailSettings",
    "MaildirSettings",
    "OutputConfigBase",
    "OutputConfigCreate",
    "OutputConfigUpdate",
    "OutputConfigResponse",
    "ElasticsearchSettings",
    "OpenSearchSettings",
    "SplunkSettings",
    "KafkaSettings",
    "S3Settings",
    "SyslogSettings",
    "GELFSettings",
    "WebhookSettings"
]
