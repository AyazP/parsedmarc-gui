"""Settings API endpoints (database management)."""
import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.schemas.settings import (
    DatabaseTestRequest,
    DatabaseTestResponse,
    DatabaseMigrateRequest,
    DatabaseMigrateResponse,
    DatabaseInfoResponse,
    DatabasePurgeResponse,
    build_database_url,
    mask_database_url,
)
from app.services.database_migration_service import migration_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["Settings"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/database", response_model=DatabaseInfoResponse)
def get_database_info():
    """Get information about the current database."""
    current_url = settings.effective_database_url
    try:
        table_counts = migration_service.get_table_counts(current_url)
    except Exception as e:
        logger.error(f"Failed to get table counts: {e}")
        table_counts = {}

    return DatabaseInfoResponse(
        db_type=settings.database_type,
        connection_string=mask_database_url(current_url),
        table_counts=table_counts,
    )


@router.post("/database/test", response_model=DatabaseTestResponse)
@limiter.limit("10/minute")
def test_database_connection(request: Request, test_request: DatabaseTestRequest):
    """Test connectivity to a target database."""
    try:
        target_url = build_database_url(
            test_request.db_type, test_request.host, test_request.port,
            test_request.database, test_request.username, test_request.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    result = migration_service.test_connection(target_url)
    return DatabaseTestResponse(**result)


@router.post("/database/migrate", response_model=DatabaseMigrateResponse)
@limiter.limit("3/minute")
def migrate_database(request: Request, migrate_request: DatabaseMigrateRequest):
    """Migrate data from the current database to a new target database.

    After a successful migration the .env file is updated with the new
    PARSEDMARC_DATABASE_URL so the application uses it on the next restart.
    """
    try:
        target_url = build_database_url(
            migrate_request.db_type, migrate_request.host, migrate_request.port,
            migrate_request.database, migrate_request.username, migrate_request.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Verify target is reachable first
    test_result = migration_service.test_connection(target_url)
    if not test_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot connect to target database: {test_result['message']}",
        )

    source_url = settings.effective_database_url

    if migrate_request.migrate_data:
        result = migration_service.migrate(source_url, target_url)
    else:
        # Just create empty tables in the target
        from sqlalchemy import create_engine
        from app.db.session import Base
        target_engine = create_engine(target_url, pool_pre_ping=True)
        try:
            Base.metadata.create_all(target_engine)
            result = {
                "success": True,
                "message": "Tables created in target database (no data migrated).",
                "tables_migrated": 0,
                "row_counts": {},
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create tables in target database.",
            )
        finally:
            target_engine.dispose()

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"],
        )

    # Update .env with the new database URL
    _update_env("PARSEDMARC_DATABASE_URL", target_url)
    logger.info(f"Database migrated to {migrate_request.db_type}. Restart required.")

    return DatabaseMigrateResponse(
        success=True,
        message=f"Migration to {migrate_request.db_type} completed. Restart the application to use the new database.",
        tables_migrated=result.get("tables_migrated", 0),
        row_counts=result.get("row_counts"),
        restart_required=True,
    )


@router.post("/database/purge", response_model=DatabasePurgeResponse)
@limiter.limit("3/minute")
def purge_database(
    request: Request,
    confirm: bool = Query(False, description="Must be true to confirm purge"),
):
    """Delete all data from the SQLite database.

    Only available when the current database is SQLite.
    Requires confirm=true as a safety guard.
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pass ?confirm=true to confirm data purge. This action is irreversible.",
        )
    if settings.database_type != "sqlite":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purge is only available for SQLite databases. "
                   "Use your database management tool for PostgreSQL/MySQL.",
        )

    current_url = settings.effective_database_url
    result = migration_service.purge_all_data(current_url)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"],
        )

    return DatabasePurgeResponse(
        success=True,
        message=result["message"],
        rows_deleted=result.get("rows_deleted"),
    )


def _update_env(key: str, value: str):
    """Update or add a key=value pair in the .env file."""
    env_path = Path(__file__).parent.parent.parent.parent / ".env"

    env_content = ""
    if env_path.exists():
        with open(env_path, "r") as f:
            env_content = f.read()

    lines = env_content.split("\n")
    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break

    if not updated:
        lines.append(f"{key}={value}")

    with open(env_path, "w") as f:
        f.write("\n".join(lines))
    try:
        os.chmod(env_path, 0o600)
    except OSError:
        pass  # chmod not supported on Windows
