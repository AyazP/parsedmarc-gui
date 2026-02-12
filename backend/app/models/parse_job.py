"""Parse job model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.db.session import Base


class ParseJob(Base):
    """Model for tracking parsing jobs (file upload or mailbox fetch)."""

    __tablename__ = "parse_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(50), nullable=False)  # 'file_upload', 'mailbox_fetch'
    status = Column(String(50), default="pending", nullable=False)  # 'pending', 'running', 'completed', 'failed'

    # Input details
    input_source = Column(Text, nullable=True)  # Filename or mailbox name
    file_path = Column(Text, nullable=True)  # For uploaded files

    # Results
    aggregate_reports_count = Column(Integer, default=0)
    forensic_reports_count = Column(Integer, default=0)
    smtp_tls_reports_count = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ParseJob(id={self.id}, type='{self.job_type}', status='{self.status}')>"
