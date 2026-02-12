"""Activity log model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db.session import Base


class ActivityLog(Base):
    """Model for application activity logging."""

    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(50), nullable=False)  # 'info', 'warning', 'error'
    source = Column(String(255), nullable=False)  # 'mailbox_monitor', 'file_upload', 'config_change'
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON with additional context

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, level='{self.level}', source='{self.source}')>"
