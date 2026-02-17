"""Application configuration."""
import os
from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Database
    db_path: str = Field(default="./data/parsedmarc.db", validation_alias="PARSEDMARC_DB_PATH")

    # Security
    encryption_key: str = Field(..., validation_alias="PARSEDMARC_ENCRYPTION_KEY")
    gui_username: str = Field(default="admin", validation_alias="PARSEDMARC_GUI_USERNAME")
    gui_password: str = Field(default="changeme", validation_alias="PARSEDMARC_GUI_PASSWORD")
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        validation_alias="PARSEDMARC_SECRET_KEY"
    )

    # Server
    host: str = Field(default="0.0.0.0", validation_alias="PARSEDMARC_HOST")
    port: int = Field(default=8000, validation_alias="PARSEDMARC_PORT")

    # CORS - will be parsed from comma-separated string
    cors_origins_raw: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://localhost:8000",
        validation_alias="PARSEDMARC_CORS_ORIGINS"
    )

    # Logging
    log_level: str = Field(default="INFO", validation_alias="PARSEDMARC_LOG_LEVEL")

    # Token expiration (in minutes)
    access_token_expire_minutes: int = Field(default=60 * 24, validation_alias="PARSEDMARC_TOKEN_EXPIRE")

    # Data directory for tokens, uploads, etc.
    data_dir: Path = Field(default=Path("./data"), validation_alias="PARSEDMARC_DATA_DIR")

    # Update checker
    update_check_enabled: bool = Field(default=True, validation_alias="PARSEDMARC_UPDATE_CHECK_ENABLED")
    update_check_interval_hours: int = Field(default=24, ge=1, le=168, validation_alias="PARSEDMARC_UPDATE_CHECK_INTERVAL")
    docker_mode: bool = Field(default=False, validation_alias="PARSEDMARC_DOCKER")

    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.cors_origins_raw, str):
            return [origin.strip() for origin in self.cors_origins_raw.split(",")]
        return self.cors_origins_raw

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        # Ensure database directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
