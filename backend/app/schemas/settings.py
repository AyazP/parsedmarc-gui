"""Settings schemas for database migration API."""
from typing import Optional, Dict, Literal
from pydantic import BaseModel, Field


def build_database_url(db_type: str, host: str, port: int, database: str,
                       username: str, password: str) -> str:
    """Build a SQLAlchemy database URL from connection parameters."""
    if db_type == "postgresql":
        return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
    elif db_type == "mysql":
        return f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
    raise ValueError(f"Unsupported database type: {db_type}")


def mask_database_url(url: str) -> str:
    """Mask the password in a database URL for display."""
    if "://" not in url:
        return url
    # sqlite:///path — nothing to mask
    if url.startswith("sqlite"):
        return url
    # postgresql+psycopg2://user:pass@host:port/db
    try:
        prefix, rest = url.split("://", 1)
        if "@" in rest:
            creds, host_part = rest.rsplit("@", 1)
            if ":" in creds:
                user, _ = creds.split(":", 1)
                return f"{prefix}://{user}:****@{host_part}"
        return f"{prefix}://****@{rest}"
    except Exception:
        return "****"


class DatabaseTestRequest(BaseModel):
    """Request schema for testing a database connection."""
    db_type: Literal["postgresql", "mysql"] = Field(..., description="Target database type")
    host: str = Field(..., min_length=1, description="Database host")
    port: int = Field(..., ge=1, le=65535, description="Database port")
    database: str = Field(..., min_length=1, description="Database name")
    username: str = Field(..., min_length=1, description="Database username")
    password: str = Field(default="", description="Database password")


class DatabaseMigrateRequest(DatabaseTestRequest):
    """Request schema for migrating to a new database."""
    migrate_data: bool = Field(default=True, description="Whether to copy existing data")


class DatabaseInfoResponse(BaseModel):
    """Response schema for current database information."""
    db_type: str
    connection_string: str
    table_counts: Dict[str, int]


class DatabaseTestResponse(BaseModel):
    """Response schema for database connection test."""
    success: bool
    message: str
    details: Optional[Dict[str, str]] = None


class DatabaseMigrateResponse(BaseModel):
    """Response schema for database migration."""
    success: bool
    message: str
    tables_migrated: int = 0
    row_counts: Optional[Dict[str, int]] = None
    restart_required: bool = True


class DatabasePurgeResponse(BaseModel):
    """Response schema for database purge."""
    success: bool
    message: str
    rows_deleted: Optional[Dict[str, int]] = None
