"""Output configuration model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from app.db.session import Base


class OutputConfig(Base):
    """Model for storing output destination configurations."""

    __tablename__ = "output_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    type = Column(String(50), nullable=False)  # 'elasticsearch', 'opensearch', 'splunk', 'kafka', 's3', 'syslog', 'gelf', 'webhook'
    enabled = Column(Boolean, default=True, nullable=False)

    # Type-specific settings (encrypted JSON blob)
    settings = Column(Text, nullable=False)

    # Report type filters
    save_aggregate = Column(Boolean, default=True)
    save_forensic = Column(Boolean, default=True)
    save_smtp_tls = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<OutputConfig(id={self.id}, name='{self.name}', type='{self.type}', enabled={self.enabled})>"
