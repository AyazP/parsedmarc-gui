"""Setup wizard model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON
from app.db.session import Base


class SetupStatus(Base):
    """Model for tracking application setup status."""

    __tablename__ = "setup_status"

    id = Column(Integer, primary_key=True, index=True)
    is_complete = Column(Boolean, default=False, nullable=False)
    setup_version = Column(String(50), default="1.0.0", nullable=False)

    # Setup steps completion tracking
    encryption_key_set = Column(Boolean, default=False)
    admin_credentials_set = Column(Boolean, default=False)
    ssl_configured = Column(Boolean, default=False)
    database_configured = Column(Boolean, default=False)
    server_configured = Column(Boolean, default=False)

    # SSL/TLS configuration
    ssl_type = Column(String(50), nullable=True)  # 'self-signed', 'letsencrypt', 'custom'
    ssl_domain = Column(String(255), nullable=True)
    ssl_email = Column(String(255), nullable=True)
    letsencrypt_staging = Column(Boolean, default=False)

    # Additional metadata
    setup_metadata = Column(JSON, nullable=True)  # Flexible storage for future setup data

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<SetupStatus(id={self.id}, is_complete={self.is_complete}, ssl_type='{self.ssl_type}')>"
