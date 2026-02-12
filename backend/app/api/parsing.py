"""Parsing API endpoints and schemas."""
import logging
import shutil
import uuid
from pathlib import Path
from typing import Optional, List, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.mailbox_config import MailboxConfig
from app.models.parse_job import ParseJob
from app.models.parsed_report import ParsedReport
from app.services.parsing_service import parsing_service
from app.config import settings

logger = logging.getLogger(__name__)

# ---------- Schemas ----------


class ParseMailboxRequest(BaseModel):
    """Request schema for triggering mailbox parsing."""

    batch_size: Optional[int] = Field(
        default=None, description="Override batch size (uses config default if not set)"
    )
    since: Optional[str] = Field(
        default=None, description="Fetch messages since (e.g., '24h', '7d', '2w')"
    )
    test_mode: bool = Field(
        default=False,
        description="Test mode - do not move/delete messages after parsing",
    )


class ParseJobResponse(BaseModel):
    """Response schema for a parse job."""

    id: int
    job_type: str
    status: str
    input_source: Optional[str] = None
    file_path: Optional[str] = None
    aggregate_reports_count: int = 0
    forensic_reports_count: int = 0
    smtp_tls_reports_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ParsedReportResponse(BaseModel):
    """Response schema for a parsed report."""

    id: int
    parse_job_id: Optional[int] = None
    report_type: str
    org_name: Optional[str] = None
    report_id: Optional[str] = None
    domain: Optional[str] = None
    date_begin: Optional[datetime] = None
    date_end: Optional[datetime] = None
    report_json: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ParsedReportListResponse(BaseModel):
    """Paginated list of parsed reports."""

    total: int
    items: List[ParsedReportResponse]


class ConnectionTestResponse(BaseModel):
    """Response schema for connection test."""

    success: bool
    message: str
    details: Optional[dict] = None


# ---------- Router ----------

router = APIRouter(prefix="/api/parse", tags=["Parsing"])


@router.post("/mailbox/{config_id}", response_model=ParseJobResponse)
def parse_from_mailbox(
    config_id: int,
    request: ParseMailboxRequest = ParseMailboxRequest(),
    db: Session = Depends(get_db),
):
    """
    Trigger DMARC report parsing from a mailbox configuration.

    Connects to the mailbox, fetches reports, parses them,
    and stores results in the database.
    """
    config = db.query(MailboxConfig).filter(MailboxConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mailbox configuration with ID {config_id} not found",
        )

    if not config.enabled:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Mailbox configuration '{config.name}' is disabled",
        )

    job = parsing_service.parse_from_mailbox(
        db=db,
        config=config,
        batch_size=request.batch_size,
        since=request.since,
        test_mode=request.test_mode,
    )
    return job


@router.post("/upload", response_model=ParseJobResponse, status_code=status.HTTP_201_CREATED)
def parse_uploaded_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload and parse a DMARC report file.

    Supports .xml, .gz, .zip, .eml, and .msg files.
    """
    allowed_extensions = {".xml", ".gz", ".zip", ".eml", ".msg"}
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Unsupported file type '{file_ext}'. "
                f"Allowed: {', '.join(sorted(allowed_extensions))}"
            ),
        )

    # Save upload to data_dir/uploads/
    uploads_dir = Path(settings.data_dir) / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = uploads_dir / safe_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {e}",
        )

    job = parsing_service.parse_from_file(
        db=db,
        file_path=str(file_path),
        original_filename=file.filename or "unknown",
    )
    return job


@router.get("/jobs", response_model=List[ParseJobResponse])
def list_parse_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    """List parse jobs with optional status filtering."""
    query = db.query(ParseJob)
    if status_filter:
        query = query.filter(ParseJob.status == status_filter)
    query = query.order_by(ParseJob.created_at.desc())
    jobs = query.offset(skip).limit(limit).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=ParseJobResponse)
def get_parse_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific parse job by ID."""
    job = db.query(ParseJob).filter(ParseJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parse job with ID {job_id} not found",
        )
    return job


@router.get("/reports", response_model=ParsedReportListResponse)
def list_parsed_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    org_name: Optional[str] = Query(None, description="Filter by organization name"),
    db: Session = Depends(get_db),
):
    """List parsed reports with filtering and pagination."""
    query = db.query(ParsedReport)
    if report_type:
        query = query.filter(ParsedReport.report_type == report_type)
    if domain:
        query = query.filter(ParsedReport.domain.ilike(f"%{domain}%"))
    if org_name:
        query = query.filter(ParsedReport.org_name.ilike(f"%{org_name}%"))

    total = query.count()
    items = (
        query.order_by(ParsedReport.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return ParsedReportListResponse(total=total, items=items)


@router.get("/reports/{report_id}", response_model=ParsedReportResponse)
def get_parsed_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific parsed report by ID."""
    report = (
        db.query(ParsedReport).filter(ParsedReport.id == report_id).first()
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parsed report with ID {report_id} not found",
        )
    return report
