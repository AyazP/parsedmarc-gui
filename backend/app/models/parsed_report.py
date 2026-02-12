"""Parsed report model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from app.db.session import Base


class ParsedReport(Base):
    """Model for storing parsed report metadata (for dashboard display)."""

    __tablename__ = "parsed_reports"

    id = Column(Integer, primary_key=True, index=True)
    parse_job_id = Column(Integer, ForeignKey("parse_jobs.id", ondelete="CASCADE"), nullable=True)
    report_type = Column(String(50), nullable=False)  # 'aggregate', 'forensic', 'smtp_tls'

    # Metadata for dashboard (extracted from report)
    org_name = Column(String(255), nullable=True)
    report_id = Column(String(255), nullable=True)
    domain = Column(String(255), nullable=True, index=True)
    date_begin = Column(DateTime, nullable=True)
    date_end = Column(DateTime, nullable=True)

    # Full JSON (optional - can be large)
    report_json = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ParsedReport(id={self.id}, type='{self.report_type}', domain='{self.domain}')>"
