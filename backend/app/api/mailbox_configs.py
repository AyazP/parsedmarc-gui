"""Mailbox configuration API endpoints."""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.mailbox_config import MailboxConfig
from app.schemas.mailbox_config import (
    MailboxConfigCreate,
    MailboxConfigUpdate,
    MailboxConfigResponse
)
from app.services.encryption_service import EncryptionService
from app.services.mailbox_service import mailbox_service
from app.api.parsing import ConnectionTestResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/configs/mailboxes", tags=["Mailbox Configurations"])
encryption_service = EncryptionService()


def _serialize_config_for_response(config: MailboxConfig) -> dict:
    """Serialize mailbox config for API response (decrypt and mask passwords)."""
    response_data = {
        "id": config.id,
        "name": config.name,
        "type": config.type,
        "enabled": config.enabled,
        "delete_after_processing": config.delete_after_processing,
        "watch_interval": config.watch_interval,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
    }

    # Decrypt and mask sensitive settings
    if config.imap_settings:
        settings = encryption_service.decrypt_dict(config.imap_settings)
        settings["password"] = "***ENCRYPTED***" if settings.get("password") else None
        response_data["imap_settings"] = settings

    if config.msgraph_settings:
        settings = encryption_service.decrypt_dict(config.msgraph_settings)
        if settings.get("client_secret"):
            settings["client_secret"] = "***ENCRYPTED***"
        if settings.get("password"):
            settings["password"] = "***ENCRYPTED***"
        response_data["msgraph_settings"] = settings

    if config.gmail_settings:
        settings = encryption_service.decrypt_dict(config.gmail_settings)
        # Gmail uses OAuth tokens, not passwords
        response_data["gmail_settings"] = settings

    if config.maildir_settings:
        settings = encryption_service.decrypt_dict(config.maildir_settings)
        response_data["maildir_settings"] = settings

    return response_data


@router.get("/", response_model=List[MailboxConfigResponse])
def list_mailbox_configs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all mailbox configurations."""
    configs = db.query(MailboxConfig).offset(skip).limit(limit).all()
    return [_serialize_config_for_response(config) for config in configs]


@router.get("/{config_id}", response_model=MailboxConfigResponse)
def get_mailbox_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific mailbox configuration by ID."""
    config = db.query(MailboxConfig).filter(MailboxConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mailbox configuration with ID {config_id} not found"
        )
    return _serialize_config_for_response(config)


@router.post("/", response_model=MailboxConfigResponse, status_code=status.HTTP_201_CREATED)
def create_mailbox_config(
    config_data: MailboxConfigCreate,
    db: Session = Depends(get_db)
):
    """Create a new mailbox configuration."""

    # Validate that appropriate settings are provided for the mailbox type
    settings_map = {
        "imap": config_data.imap_settings,
        "msgraph": config_data.msgraph_settings,
        "gmail": config_data.gmail_settings,
        "maildir": config_data.maildir_settings
    }

    if not settings_map.get(config_data.type):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing {config_data.type}_settings for mailbox type '{config_data.type}'"
        )

    # Create database model
    db_config = MailboxConfig(
        name=config_data.name,
        type=config_data.type,
        enabled=config_data.enabled,
        delete_after_processing=config_data.delete_after_processing,
        watch_interval=config_data.watch_interval
    )

    # Encrypt and store type-specific settings
    if config_data.imap_settings:
        db_config.imap_settings = encryption_service.encrypt_dict(
            config_data.imap_settings.model_dump()
        )

    if config_data.msgraph_settings:
        db_config.msgraph_settings = encryption_service.encrypt_dict(
            config_data.msgraph_settings.model_dump()
        )

    if config_data.gmail_settings:
        db_config.gmail_settings = encryption_service.encrypt_dict(
            config_data.gmail_settings.model_dump()
        )

    if config_data.maildir_settings:
        db_config.maildir_settings = encryption_service.encrypt_dict(
            config_data.maildir_settings.model_dump()
        )

    try:
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mailbox configuration with name '{config_data.name}' already exists"
        )

    return _serialize_config_for_response(db_config)


@router.put("/{config_id}", response_model=MailboxConfigResponse)
def update_mailbox_config(
    config_id: int,
    config_data: MailboxConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing mailbox configuration."""
    db_config = db.query(MailboxConfig).filter(MailboxConfig.id == config_id).first()

    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mailbox configuration with ID {config_id} not found"
        )

    # Update basic fields
    update_data = config_data.model_dump(exclude_unset=True)

    for field in ["name", "enabled", "delete_after_processing", "watch_interval"]:
        if field in update_data:
            setattr(db_config, field, update_data[field])

    # Update encrypted settings if provided
    if config_data.imap_settings is not None:
        db_config.imap_settings = encryption_service.encrypt_dict(
            config_data.imap_settings.model_dump()
        )

    if config_data.msgraph_settings is not None:
        db_config.msgraph_settings = encryption_service.encrypt_dict(
            config_data.msgraph_settings.model_dump()
        )

    if config_data.gmail_settings is not None:
        db_config.gmail_settings = encryption_service.encrypt_dict(
            config_data.gmail_settings.model_dump()
        )

    if config_data.maildir_settings is not None:
        db_config.maildir_settings = encryption_service.encrypt_dict(
            config_data.maildir_settings.model_dump()
        )

    try:
        db.commit()
        db.refresh(db_config)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mailbox configuration with name '{config_data.name}' already exists"
        )

    return _serialize_config_for_response(db_config)


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mailbox_config(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Delete a mailbox configuration."""
    db_config = db.query(MailboxConfig).filter(MailboxConfig.id == config_id).first()

    if not db_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mailbox configuration with ID {config_id} not found"
        )

    db.delete(db_config)
    db.commit()

    return None


@router.post("/{config_id}/test", response_model=ConnectionTestResponse)
def test_mailbox_connection(
    config_id: int,
    db: Session = Depends(get_db),
):
    """
    Test connectivity to a mailbox configuration.

    Attempts to connect and list messages in the reports folder.
    """
    config = db.query(MailboxConfig).filter(MailboxConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mailbox configuration with ID {config_id} not found",
        )

    result = mailbox_service.test_connection(config)
    return result
