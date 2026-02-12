"""Mailbox configuration model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from app.db.session import Base


class MailboxConfig(Base):
    """Model for storing mailbox configurations (IMAP, MS Graph, Gmail, Maildir)."""

    __tablename__ = "mailbox_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    type = Column(String(50), nullable=False)  # 'imap', 'msgraph', 'gmail', 'maildir'
    enabled = Column(Boolean, default=True, nullable=False)

    # Common settings
    reports_folder = Column(String(255), default="INBOX")
    archive_folder = Column(String(255), default="Archive")
    delete_after_processing = Column(Boolean, default=False)
    watch_interval = Column(Integer, default=60)  # Interval in seconds for mailbox monitoring
    batch_size = Column(Integer, default=10)

    # Type-specific settings (encrypted JSON blobs)
    imap_settings = Column(Text, nullable=True)  # {host, port, user, password_encrypted, ssl, verify, timeout}
    msgraph_settings = Column(Text, nullable=True)  # {auth_method, user, password, client_id, client_secret, tenant_id, mailbox}
    gmail_settings = Column(Text, nullable=True)  # {credentials_file_path, token_file_path, scopes}
    maildir_settings = Column(Text, nullable=True)  # {path}

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<MailboxConfig(id={self.id}, name='{self.name}', type='{self.type}', enabled={self.enabled})>"
