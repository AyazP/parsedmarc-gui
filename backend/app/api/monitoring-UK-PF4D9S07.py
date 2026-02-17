"""Monitoring API endpoints for managing background mailbox monitoring."""
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.mailbox_config import MailboxConfig
from app.models.monitoring_job import MonitoringJob

logger = logging.getLogger(__name__)

# ---------- Schemas ----------


class MonitoringJobResponse(BaseModel):
    """Response schema for a monitoring job."""
    id: int
    mailbox_config_id: int
    status: str
    watch_mode: bool
    last_run_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None
    reports_processed: int = 0
    scheduler_job_id: Optional[str] = None

    class Config:
        from_attributes = True


class MonitoringJobCreate(BaseModel):
    """Request schema to start monitoring a mailbox."""
    watch_mode: bool = True


class MonitoringStatusResponse(BaseModel):
    """Overall monitoring service status."""
    is_running: bool
    active_jobs: int
    total_jobs: int


# ---------- Router ----------

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])


def _get_monitoring_service():
    """Get the global monitoring service instance from main."""
    from app.main import monitoring_service
    if monitoring_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Monitoring service is not initialized",
        )
    return monitoring_service


@router.get("/status", response_model=MonitoringStatusResponse)
def get_monitoring_status(db: Session = Depends(get_db)):
    """Get overall monitoring service status."""
    svc = _get_monitoring_service()
    total = db.query(MonitoringJob).count()
    active = db.query(MonitoringJob).filter(MonitoringJob.status == "running").count()
    return MonitoringStatusResponse(
        is_running=svc.is_running(),
        active_jobs=active,
        total_jobs=total,
    )


@router.get("/jobs", response_model=List[MonitoringJobResponse])
def list_monitoring_jobs(db: Session = Depends(get_db)):
    """List all monitoring jobs."""
    jobs = db.query(MonitoringJob).all()
    return jobs


@router.get("/jobs/{mailbox_config_id}", response_model=MonitoringJobResponse)
def get_monitoring_job(
    mailbox_config_id: int,
    db: Session = Depends(get_db),
):
    """Get monitoring job for a specific mailbox config."""
    job = (
        db.query(MonitoringJob)
        .filter(MonitoringJob.mailbox_config_id == mailbox_config_id)
        .first()
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No monitoring job for mailbox config {mailbox_config_id}",
        )
    return job


@router.post("/jobs/{mailbox_config_id}/start", response_model=MonitoringJobResponse)
async def start_monitoring(
    mailbox_config_id: int,
    request: MonitoringJobCreate = MonitoringJobCreate(),
    db: Session = Depends(get_db),
):
    """Start monitoring a mailbox configuration."""
    svc = _get_monitoring_service()

    config = db.query(MailboxConfig).filter(MailboxConfig.id == mailbox_config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mailbox config {mailbox_config_id} not found",
        )

    if not config.enabled:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Mailbox config '{config.name}' is disabled",
        )

    # Create or update monitoring job record
    job = (
        db.query(MonitoringJob)
        .filter(MonitoringJob.mailbox_config_id == mailbox_config_id)
        .first()
    )
    if not job:
        job = MonitoringJob(
            mailbox_config_id=mailbox_config_id,
            watch_mode=request.watch_mode,
        )
        db.add(job)

    job.status = "running"
    job.watch_mode = request.watch_mode
    job.scheduler_job_id = f"monitor_mailbox_{mailbox_config_id}"
    db.commit()
    db.refresh(job)

    # Add to APScheduler
    await svc.add_monitoring_job(mailbox_config_id, config.watch_interval)

    logger.info(f"Started monitoring for mailbox config {mailbox_config_id} ({config.name})")
    return job


@router.post("/jobs/{mailbox_config_id}/stop", response_model=MonitoringJobResponse)
async def stop_monitoring(
    mailbox_config_id: int,
    db: Session = Depends(get_db),
):
    """Stop monitoring a mailbox configuration."""
    svc = _get_monitoring_service()

    job = (
        db.query(MonitoringJob)
        .filter(MonitoringJob.mailbox_config_id == mailbox_config_id)
        .first()
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No monitoring job for mailbox config {mailbox_config_id}",
        )

    # Remove from APScheduler
    await svc.remove_monitoring_job(mailbox_config_id)

    job.status = "stopped"
    db.commit()
    db.refresh(job)

    logger.info(f"Stopped monitoring for mailbox config {mailbox_config_id}")
    return job
