"""Output configuration API endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.output_config import OutputConfig
from app.schemas.output_config import (
    OutputConfigCreate,
    OutputConfigUpdate,
    OutputConfigResponse
)
from app.services.encryption_service import EncryptionService

router = APIRouter(prefix="/api/configs/outputs", tags=["Output Configurations"])
encryption_service = EncryptionService()


def _mask_sensitive_fields(settings: dict, output_type: str) -> dict:
    """Mask sensitive fields in output settings."""
    masked = settings.copy()

    # Common sensitive fields
    if "password" in masked and masked["password"]:
        masked["password"] = "***ENCRYPTED***"
    if "token" in masked and masked["token"]:
        masked["token"] = "***ENCRYPTED***"
    if "secret_access_key" in masked and masked["secret_access_key"]:
        masked["secret_access_key"] = "***ENCRYPTED***"
    if "api_key" in masked and masked["api_key"]:
        masked["api_key"] = "***ENCRYPTED***"

    return masked


def _serialize_config_for_response(config: OutputConfig) -> dict:
    """Serialize output config for API response (decrypt and mask passwords)."""
    response_data = {
        "id": config.id,
        "name": config.name,
        "type": config.type,
        "enabled": config.enabled,
        "save_aggregate": config.save_aggregate,
        "save_forensic": config.save_forensic,
        "save_smtp_tls": config.save_smtp_tls,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
    }

    # Decrypt settings and add to response
    if config.settings:
        settings = encryption_service.decrypt_dict(config.settings)
        masked_settings = _mask_sensitive_fields(settings, config.type)
        response_data[f"{config.type}_settings"] = masked_settings

    return response_data


@router.get("/", response_model=List[OutputConfigResponse])
def list_output_configs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List all output configurations."""
    configs = db.query(OutputConfig).offset(skip).limit(limit).all()
    return [_serialize_config_for_response(config) for config in configs]


@router.get("/{config_id}", response_model=OutputConfigResponse)
def get_output_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific output configuration by ID."""
    config = db.query(OutputConfig).filter(OutputConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Output configuration with ID {config_id} not found"
        )
    return _serialize_config_for_response(config)


@router.post("/", response_model=OutputConfigResponse, status_code=status.HTTP_201_CREATED)
def create_output_config(
    config_data: OutputConfigCreate,
    db: Session = Depends(get_db)
):
    """Create a new output configuration."""

    # Validate that appropriate settings are provided for the output type
    settings_attr = f"{config_data.type}_settings"
    settings_value = getattr(config_data, settings_attr, None)

    if not settings_value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing {settings_attr} for output type '{config_data.type}'"
        )

    # Create database model
    db_config = OutputConfig(
        name=config_data.name,
        type=config_data.type,
        enabled=config_data.enabled,
        save_aggregate=config_data.save_aggregate,
        save_forensic=config_data.save_forensic,
        save_smtp_tls=config_data.save_smtp_tls,
        settings=encryption_service.encrypt_dict(settings_value.model_dump())
    )

    try:
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Output configuration with name '{config_data.name}' already exists"
        )

    return _serialize_config_for_response(db_config)


@router.put("/{config_id}", response_model=OutputConfigResponse)
def update_output_config(
    config_id: int,
    config_data: OutputConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing output configuration."""
    db_config = db.query(OutputConfig).filter(OutputConfig.id == config_id).first()

    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Output configuration with ID {config_id} not found"
        )

    # Update basic fields
    update_data = config_data.model_dump(exclude_unset=True)

    for field in ["name", "enabled", "save_aggregate", "save_forensic", "save_smtp_tls"]:
        if field in update_data:
            setattr(db_config, field, update_data[field])

    # Update encrypted settings if any type-specific settings are provided
    settings_fields = [
        "elasticsearch_settings", "opensearch_settings", "splunk_settings",
        "kafka_settings", "s3_settings", "syslog_settings", "gelf_settings", "webhook_settings"
    ]

    for field in settings_fields:
        if field in update_data and update_data[field] is not None:
            settings_value = update_data[field]
            if isinstance(settings_value, BaseModel):
                settings_value = settings_value.model_dump()
            db_config.settings = encryption_service.encrypt_dict(settings_value)
            break

    try:
        db.commit()
        db.refresh(db_config)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Output configuration with name '{config_data.name}' already exists"
        )

    return _serialize_config_for_response(db_config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_output_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Delete an output configuration."""
    db_config = db.query(OutputConfig).filter(OutputConfig.id == config_id).first()

    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Output configuration with ID {config_id} not found"
        )

    db.delete(db_config)
    db.commit()

    return None
