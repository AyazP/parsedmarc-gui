"""Monitoring job model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from app.db.session import Base


class MonitoringJob(Base):
    """Model for tracking mailbox monitoring jobs."""

    __tablename__ = "monitoring_jobs"

    id = Column(Integer, primary_key=True, index=True)
    mailbox_config_id = Column(Integer, ForeignKey("mailbox_configs.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="stopped", nullable=False)  # 'running', 'stopped', 'error'
    watch_mode = Column(Boolean, default=False)  # TRUE = continuous watch, FALSE = scheduled fetch

    # Job tracking
    last_run_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    reports_processed = Column(Integer, default=0)

    # APScheduler job reference
    scheduler_job_id = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<MonitoringJob(id={self.id}, mailbox_config_id={self.mailbox_config_id}, status='{self.status}')>"
