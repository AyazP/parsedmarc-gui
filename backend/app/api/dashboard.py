"""Dashboard API endpoints for aggregated statistics."""
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.parse_job import ParseJob
from app.models.parsed_report import ParsedReport
from app.models.mailbox_config import MailboxConfig
from app.models.output_config import OutputConfig
from app.models.activity_log import ActivityLog

logger = logging.getLogger(__name__)

# ---------- Schemas ----------


class DashboardStats(BaseModel):
    """Aggregated dashboard statistics."""
    total_reports: int = 0
    aggregate_reports: int = 0
    forensic_reports: int = 0
    smtp_tls_reports: int = 0
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    mailbox_configs: int = 0
    output_configs: int = 0


class ActivityLogEntry(BaseModel):
    """Activity log entry for the dashboard feed."""
    id: int
    level: str
    source: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    """Full dashboard data."""
    stats: DashboardStats
    recent_activity: List[ActivityLogEntry]


# ---------- Router ----------

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), _user: str = Depends(get_current_user)):
    """Get aggregated dashboard statistics."""
    # Report counts by type
    report_counts = (
        db.query(
            ParsedReport.report_type,
            func.count(ParsedReport.id),
        )
        .group_by(ParsedReport.report_type)
        .all()
    )
    type_map = {row[0]: row[1] for row in report_counts}

    # Job counts by status
    job_counts = (
        db.query(
            ParseJob.status,
            func.count(ParseJob.id),
        )
        .group_by(ParseJob.status)
        .all()
    )
    status_map = {row[0]: row[1] for row in job_counts}

    total_reports = sum(type_map.values())
    total_jobs = sum(status_map.values())

    return DashboardStats(
        total_reports=total_reports,
        aggregate_reports=type_map.get("aggregate", 0),
        forensic_reports=type_map.get("forensic", 0),
        smtp_tls_reports=type_map.get("smtp_tls", 0),
        total_jobs=total_jobs,
        completed_jobs=status_map.get("completed", 0),
        failed_jobs=status_map.get("failed", 0),
        mailbox_configs=db.query(func.count(MailboxConfig.id)).scalar() or 0,
        output_configs=db.query(func.count(OutputConfig.id)).scalar() or 0,
    )


@router.get("/activity", response_model=List[ActivityLogEntry])
def get_recent_activity(
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    """Get recent activity log entries."""
    entries = (
        db.query(ActivityLog)
        .order_by(ActivityLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return entries


@router.get("", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db), _user: str = Depends(get_current_user)):
    """Get full dashboard data (stats + recent activity)."""
    stats = get_dashboard_stats(db)
    activity = get_recent_activity(limit=10, db=db)
    return DashboardResponse(stats=stats, recent_activity=activity)
