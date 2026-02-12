"""Pydantic schemas for mailbox configuration."""
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# Settings schemas for each mailbox type
class IMAPSettings(BaseModel):
    """IMAP mailbox settings."""
    host: str = Field(..., description="IMAP server hostname")
    port: int = Field(default=993, description="IMAP server port")
    username: str = Field(..., description="IMAP username")
    password: str = Field(..., description="IMAP password")
    ssl: bool = Field(default=True, description="Use SSL/TLS")
    skip_certificate_verification: bool = Field(default=False, description="Skip SSL certificate verification")
    folder: str = Field(default="INBOX", description="Mailbox folder to monitor")
    batch_size: int = Field(default=10, description="Number of messages to process at once")


class MSGraphSettings(BaseModel):
    """Microsoft Graph mailbox settings."""
    auth_method: Literal["DeviceCode", "ClientSecret", "UsernamePassword"] = Field(
        ..., description="Authentication method"
    )
    tenant_id: str = Field(..., description="Azure AD tenant ID")
    client_id: str = Field(..., description="Azure AD application (client) ID")
    client_secret: Optional[str] = Field(None, description="Client secret (for ClientSecret auth)")
    username: Optional[str] = Field(None, description="Username (for UsernamePassword auth)")
    password: Optional[str] = Field(None, description="Password (for UsernamePassword auth)")
    mailbox: str = Field(..., description="Mailbox email address to monitor")
    token_file: Optional[str] = Field(None, description="Path to token cache file")
    graph_url: str = Field(default="https://graph.microsoft.com", description="Microsoft Graph API URL")
    batch_size: int = Field(default=10, description="Number of messages to process at once")


class GmailSettings(BaseModel):
    """Gmail API mailbox settings."""
    credentials_file: str = Field(..., description="Path to Google OAuth2 credentials JSON")
    token_file: Optional[str] = Field(None, description="Path to token cache file")
    scopes: list[str] = Field(
        default=["https://www.googleapis.com/auth/gmail.modify"],
        description="OAuth2 scopes"
    )
    include_spam_trash: bool = Field(default=False, description="Include spam and trash folders")
    batch_size: int = Field(default=10, description="Number of messages to process at once")


class MaildirSettings(BaseModel):
    """Maildir mailbox settings."""
    path: str = Field(..., description="Path to Maildir directory")


# Base schema for mailbox config
class MailboxConfigBase(BaseModel):
    """Base schema for mailbox configuration."""
    name: str = Field(..., min_length=1, max_length=255, description="Unique name for this mailbox")
    type: Literal["imap", "msgraph", "gmail", "maildir"] = Field(..., description="Mailbox type")
    enabled: bool = Field(default=True, description="Whether this mailbox is enabled")
    delete_after_processing: bool = Field(default=False, description="Delete messages after processing")
    watch_interval: int = Field(default=60, description="Interval in seconds for mailbox monitoring")


class MailboxConfigCreate(MailboxConfigBase):
    """Schema for creating a mailbox configuration."""
    imap_settings: Optional[IMAPSettings] = None
    msgraph_settings: Optional[MSGraphSettings] = None
    gmail_settings: Optional[GmailSettings] = None
    maildir_settings: Optional[MaildirSettings] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Office365 DMARC Reports",
                "type": "msgraph",
                "enabled": True,
                "delete_after_processing": False,
                "watch_interval": 60,
                "msgraph_settings": {
                    "auth_method": "ClientSecret",
                    "tenant_id": "12345678-1234-1234-1234-123456789012",
                    "client_id": "87654321-4321-4321-4321-210987654321",
                    "client_secret": "your-secret-here",
                    "mailbox": "dmarc@company.com",
                    "graph_url": "https://graph.microsoft.com",
                    "batch_size": 10
                }
            }
        }


class MailboxConfigUpdate(BaseModel):
    """Schema for updating a mailbox configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    enabled: Optional[bool] = None
    delete_after_processing: Optional[bool] = None
    watch_interval: Optional[int] = None
    imap_settings: Optional[IMAPSettings] = None
    msgraph_settings: Optional[MSGraphSettings] = None
    gmail_settings: Optional[GmailSettings] = None
    maildir_settings: Optional[MaildirSettings] = None


class MailboxConfigResponse(MailboxConfigBase):
    """Schema for mailbox configuration response (passwords hidden)."""
    id: int
    created_at: datetime
    updated_at: datetime
    imap_settings: Optional[dict] = None
    msgraph_settings: Optional[dict] = None
    gmail_settings: Optional[dict] = None
    maildir_settings: Optional[dict] = None

    class Config:
        from_attributes = True
