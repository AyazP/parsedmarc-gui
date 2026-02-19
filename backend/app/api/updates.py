"""Update checker API endpoints."""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)

# ---------- Schemas ----------


class UpdateStatusResponse(BaseModel):
    """Response for current update status."""
    update_available: bool
    current_version: str
    latest_version: str
    release_url: str
    release_notes: str
    published_at: Optional[str] = None
    checked_at: Optional[datetime] = None
    is_docker: bool
    error: Optional[str] = None


class UpdateSettingsResponse(BaseModel):
    """Response for update check settings."""
    enabled: bool
    interval_hours: int
    is_docker: bool


# ---------- Router ----------

router = APIRouter(prefix="/api/updates", tags=["Updates"])


def _get_update_service():
    """Get the global update service instance from main."""
    from app.main import update_service
    if update_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Update service is not initialized",
        )
    return update_service


@router.get("/status", response_model=UpdateStatusResponse)
async def get_update_status(_user: str = Depends(get_current_user)):
    """Get current update status (returns cached result or checks now)."""
    svc = _get_update_service()
    result = svc.get_cached_result()
    if result is None:
        result = await svc.check_now()
    return UpdateStatusResponse(
        update_available=result.update_available,
        current_version=result.current_version,
        latest_version=result.latest_version,
        release_url=result.release_url,
        release_notes=result.release_notes,
        published_at=result.published_at,
        checked_at=result.checked_at,
        is_docker=result.is_docker,
        error=result.error,
    )


@router.post("/check", response_model=UpdateStatusResponse)
async def check_for_updates(_user: str = Depends(get_current_user)):
    """Force an immediate update check (bypasses cache)."""
    svc = _get_update_service()
    result = await svc.check_now()
    return UpdateStatusResponse(
        update_available=result.update_available,
        current_version=result.current_version,
        latest_version=result.latest_version,
        release_url=result.release_url,
        release_notes=result.release_notes,
        published_at=result.published_at,
        checked_at=result.checked_at,
        is_docker=result.is_docker,
        error=result.error,
    )


@router.get("/settings", response_model=UpdateSettingsResponse)
async def get_update_settings(_user: str = Depends(get_current_user)):
    """Get update checker settings."""
    from app.config import settings
    svc = _get_update_service()
    return UpdateSettingsResponse(
        enabled=settings.update_check_enabled,
        interval_hours=settings.update_check_interval_hours,
        is_docker=svc._is_docker,
    )
