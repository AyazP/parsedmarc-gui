"""Setup wizard API endpoints."""
import os
from pathlib import Path
from typing import Union
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet

from app.db.session import get_db
from app.models.setup import SetupStatus
from app.schemas.setup import (
    EncryptionKeySetup,
    AdminCredentialsSetup,
    SSLSetupSelfSigned,
    SSLSetupLetsEncrypt,
    SSLSetupCustom,
    ServerSetup,
    DatabaseSetup,
    CompleteSetup,
    SetupStatusResponse,
    SetupStepResponse,
    CertificateInfo
)
from app.services.certificate_service import CertificateService
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/setup", tags=["Setup Wizard"])

# Initialize certificate service
cert_service = CertificateService(cert_dir=settings.data_dir / "certificates")


def generate_encryption_key() -> str:
    """Generate a new cryptographically secure encryption key.

    Returns:
        A new Fernet encryption key (base64 encoded)
    """
    return Fernet.generate_key().decode()


def get_setup_status(db: Session) -> SetupStatus:
    """Get or create setup status record."""
    setup = db.query(SetupStatus).first()
    if not setup:
        setup = SetupStatus()
        db.add(setup)
        db.commit()
        db.refresh(setup)
    return setup


@router.get("/status", response_model=SetupStatusResponse)
def check_setup_status(db: Session = Depends(get_db)):
    """Check if initial setup is needed.

    Returns setup status including which steps are complete.
    """
    setup = get_setup_status(db)

    return SetupStatusResponse(
        is_complete=setup.is_complete,
        setup_version=setup.setup_version,
        encryption_key_set=setup.encryption_key_set,
        admin_credentials_set=setup.admin_credentials_set,
        ssl_configured=setup.ssl_configured,
        database_configured=setup.database_configured,
        server_configured=setup.server_configured,
        ssl_type=setup.ssl_type,
        ssl_domain=setup.ssl_domain,
        completed_at=setup.completed_at,
        needs_setup=not setup.is_complete
    )


@router.get("/encryption-key/generate")
def generate_new_encryption_key():
    """Generate a new cryptographically secure encryption key.

    This endpoint generates a fresh, unique Fernet encryption key.
    Each installation should use its own unique key - never reuse keys
    between different installations.

    Returns:
        A newly generated encryption key (base64 encoded)
    """
    new_key = generate_encryption_key()

    logger.info("Generated new encryption key")

    return {
        "success": True,
        "encryption_key": new_key,
        "message": "New encryption key generated. Store this securely - it cannot be recovered if lost."
    }


@router.post("/encryption-key", response_model=SetupStepResponse)
def setup_encryption_key(
    key_data: EncryptionKeySetup,
    db: Session = Depends(get_db)
):
    """Set up encryption key.

    Validates and saves the encryption key to environment.
    If no key is provided, a new one will be auto-generated.
    """
    try:
        # Auto-generate key if not provided
        encryption_key = key_data.encryption_key or generate_encryption_key()

        # Validate the key
        Fernet(encryption_key.encode())

        # Update .env file
        env_path = Path(__file__).parent.parent.parent.parent / ".env"

        # Read existing .env
        env_content = ""
        if env_path.exists():
            with open(env_path, "r") as f:
                env_content = f.read()

        # Update or add encryption key
        lines = env_content.split("\n")
        key_updated = False
        for i, line in enumerate(lines):
            if line.startswith("PARSEDMARC_ENCRYPTION_KEY="):
                lines[i] = f"PARSEDMARC_ENCRYPTION_KEY={encryption_key}"
                key_updated = True
                break

        if not key_updated:
            lines.append(f"PARSEDMARC_ENCRYPTION_KEY={encryption_key}")

        # Write back to .env
        with open(env_path, "w") as f:
            f.write("\n".join(lines))

        # Update setup status
        setup = get_setup_status(db)
        setup.encryption_key_set = True
        db.commit()

        was_auto_generated = not key_data.encryption_key
        logger.info(f"Encryption key configured successfully (auto-generated: {was_auto_generated})")

        return SetupStepResponse(
            success=True,
            message="Encryption key configured successfully" +
                   (" (auto-generated - store securely!)" if was_auto_generated else ""),
            data={
                "encryption_key": encryption_key if was_auto_generated else "***HIDDEN***",
                "auto_generated": was_auto_generated
            }
        )

    except Exception as e:
        logger.error(f"Failed to setup encryption key: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to setup encryption key: {str(e)}"
        )


@router.post("/admin-credentials", response_model=SetupStepResponse)
def setup_admin_credentials(
    credentials: AdminCredentialsSetup,
    db: Session = Depends(get_db)
):
    """Set up admin credentials.

    Validates and saves admin username and password.
    """
    try:
        # Update .env file
        env_path = Path(__file__).parent.parent.parent.parent / ".env"

        # Read existing .env
        env_content = ""
        if env_path.exists():
            with open(env_path, "r") as f:
                env_content = f.read()

        # Update credentials
        lines = env_content.split("\n")
        username_updated = False
        password_updated = False

        for i, line in enumerate(lines):
            if line.startswith("PARSEDMARC_GUI_USERNAME="):
                lines[i] = f"PARSEDMARC_GUI_USERNAME={credentials.username}"
                username_updated = True
            elif line.startswith("PARSEDMARC_GUI_PASSWORD="):
                lines[i] = f"PARSEDMARC_GUI_PASSWORD={credentials.password}"
                password_updated = True

        if not username_updated:
            lines.append(f"PARSEDMARC_GUI_USERNAME={credentials.username}")
        if not password_updated:
            lines.append(f"PARSEDMARC_GUI_PASSWORD={credentials.password}")

        # Write back to .env
        with open(env_path, "w") as f:
            f.write("\n".join(lines))

        # Update setup status
        setup = get_setup_status(db)
        setup.admin_credentials_set = True
        db.commit()

        logger.info("Admin credentials configured successfully")

        return SetupStepResponse(
            success=True,
            message="Admin credentials configured successfully"
        )

    except Exception as e:
        logger.error(f"Failed to setup admin credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to setup admin credentials: {str(e)}"
        )


@router.post("/ssl", response_model=SetupStepResponse)
def setup_ssl(
    ssl_config: Union[SSLSetupSelfSigned, SSLSetupLetsEncrypt, SSLSetupCustom],
    db: Session = Depends(get_db)
):
    """Set up SSL/TLS certificate.

    Supports self-signed, Let's Encrypt, or custom certificates.
    """
    try:
        result = None

        if isinstance(ssl_config, SSLSetupSelfSigned):
            # Generate self-signed certificate (always creates a new unique certificate)
            logger.info(f"Generating unique self-signed certificate for {ssl_config.common_name}")
            result = cert_service.generate_self_signed_certificate(
                common_name=ssl_config.common_name,
                organization=ssl_config.organization,
                validity_days=ssl_config.validity_days,
                force_regenerate=True  # Always generate fresh certificate
            )

            # Update setup status
            setup = get_setup_status(db)
            setup.ssl_configured = True
            setup.ssl_type = "self-signed"
            setup.ssl_domain = ssl_config.common_name

            # Store certificate metadata in setup_metadata
            if not setup.setup_metadata:
                setup.setup_metadata = {}
            setup.setup_metadata["ssl_certificate_serial"] = result.get("serial_number")
            setup.setup_metadata["ssl_certificate_generated_at"] = datetime.utcnow().isoformat()

            db.commit()

            logger.info(f"Self-signed certificate configured with serial: {result.get('serial_number')}")

        elif isinstance(ssl_config, SSLSetupLetsEncrypt):
            # Request Let's Encrypt certificate
            webroot = Path(ssl_config.webroot_path) if ssl_config.webroot_path else None
            result = cert_service.request_letsencrypt_certificate(
                domain=ssl_config.domain,
                email=ssl_config.email,
                webroot_path=webroot,
                staging=ssl_config.staging
            )

            if result.get("success"):
                # Update setup status
                setup = get_setup_status(db)
                setup.ssl_configured = True
                setup.ssl_type = "letsencrypt"
                setup.ssl_domain = ssl_config.domain
                setup.ssl_email = ssl_config.email
                setup.letsencrypt_staging = ssl_config.staging
                db.commit()
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Let's Encrypt certificate request failed: {result.get('error')}"
                )

        elif isinstance(ssl_config, SSLSetupCustom):
            # Validate custom certificate paths
            cert_path = Path(ssl_config.certificate_path)
            key_path = Path(ssl_config.private_key_path)

            if not cert_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Certificate file not found: {ssl_config.certificate_path}"
                )

            if not key_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Private key file not found: {ssl_config.private_key_path}"
                )

            # Get certificate info
            cert_info = cert_service.get_certificate_info(cert_path)

            result = {
                "certificate": str(cert_path),
                "private_key": str(key_path),
                "type": "custom",
                "expires": cert_info.get("expires")
            }

            # Update setup status
            setup = get_setup_status(db)
            setup.ssl_configured = True
            setup.ssl_type = "custom"
            db.commit()

        logger.info(f"SSL configured successfully: {ssl_config.type}")

        return SetupStepResponse(
            success=True,
            message=f"SSL certificate configured successfully ({ssl_config.type})",
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to setup SSL: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to setup SSL: {str(e)}"
        )


@router.post("/server", response_model=SetupStepResponse)
def setup_server(
    server_config: ServerSetup,
    db: Session = Depends(get_db)
):
    """Set up server configuration."""
    try:
        # Update .env file
        env_path = Path(__file__).parent.parent.parent.parent / ".env"

        # Read existing .env
        env_content = ""
        if env_path.exists():
            with open(env_path, "r") as f:
                env_content = f.read()

        # Update server settings
        lines = env_content.split("\n")
        settings_to_update = {
            "PARSEDMARC_HOST": server_config.host,
            "PARSEDMARC_PORT": str(server_config.port),
            "PARSEDMARC_CORS_ORIGINS": server_config.cors_origins,
            "PARSEDMARC_LOG_LEVEL": server_config.log_level
        }

        for key, value in settings_to_update.items():
            updated = False
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}"
                    updated = True
                    break
            if not updated:
                lines.append(f"{key}={value}")

        # Write back to .env
        with open(env_path, "w") as f:
            f.write("\n".join(lines))

        # Update setup status
        setup = get_setup_status(db)
        setup.server_configured = True
        db.commit()

        logger.info("Server configuration saved successfully")

        return SetupStepResponse(
            success=True,
            message="Server configuration saved successfully"
        )

    except Exception as e:
        logger.error(f"Failed to setup server: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to setup server: {str(e)}"
        )


@router.post("/database", response_model=SetupStepResponse)
def setup_database(
    db_config: DatabaseSetup,
    db: Session = Depends(get_db)
):
    """Set up database configuration."""
    try:
        # Update .env file
        env_path = Path(__file__).parent.parent.parent.parent / ".env"

        # Read existing .env
        env_content = ""
        if env_path.exists():
            with open(env_path, "r") as f:
                env_content = f.read()

        # Update database path
        lines = env_content.split("\n")
        db_updated = False

        for i, line in enumerate(lines):
            if line.startswith("PARSEDMARC_DB_PATH="):
                lines[i] = f"PARSEDMARC_DB_PATH={db_config.db_path}"
                db_updated = True
                break

        if not db_updated:
            lines.append(f"PARSEDMARC_DB_PATH={db_config.db_path}")

        # Write back to .env
        with open(env_path, "w") as f:
            f.write("\n".join(lines))

        # Ensure database directory exists
        db_path = Path(db_config.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Update setup status
        setup = get_setup_status(db)
        setup.database_configured = True
        db.commit()

        logger.info("Database configuration saved successfully")

        return SetupStepResponse(
            success=True,
            message="Database configuration saved successfully"
        )

    except Exception as e:
        logger.error(f"Failed to setup database: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to setup database: {str(e)}"
        )


@router.post("/complete", response_model=SetupStepResponse)
def complete_setup(
    setup_data: CompleteSetup,
    db: Session = Depends(get_db)
):
    """Complete the entire setup in one request.

    This endpoint performs all setup steps at once.
    """
    try:
        # 1. Setup encryption key - auto-generate if not provided
        encryption_key = setup_data.encryption_key or generate_encryption_key()
        was_key_auto_generated = not setup_data.encryption_key

        try:
            Fernet(encryption_key.encode())
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid encryption key format"
            )

        logger.info(f"Complete setup using {'auto-generated' if was_key_auto_generated else 'provided'} encryption key")

        # 2. Setup SSL if requested
        ssl_result = None
        if setup_data.ssl_type == "self-signed":
            logger.info("Generating unique self-signed certificate for this installation")
            ssl_result = cert_service.generate_self_signed_certificate(
                common_name=setup_data.ssl_common_name or "localhost",
                organization="ParseDMARC",
                validity_days=365,
                force_regenerate=True  # Always create fresh certificate per installation
            )
            logger.info(f"Self-signed certificate generated with serial: {ssl_result.get('serial_number')}")
        elif setup_data.ssl_type == "letsencrypt":
            if not setup_data.ssl_domain or not setup_data.ssl_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Domain and email required for Let's Encrypt"
                )
            ssl_result = cert_service.request_letsencrypt_certificate(
                domain=setup_data.ssl_domain,
                email=setup_data.ssl_email,
                staging=setup_data.ssl_staging
            )
            if not ssl_result.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Let's Encrypt failed: {ssl_result.get('error')}"
                )

        # 3. Update .env file with all settings
        env_path = Path(__file__).parent.parent.parent.parent / ".env"
        env_content = ""
        if env_path.exists():
            with open(env_path, "r") as f:
                env_content = f.read()

        lines = env_content.split("\n") if env_content else []

        # Settings to update (use generated encryption_key, not from setup_data)
        env_updates = {
            "PARSEDMARC_ENCRYPTION_KEY": encryption_key,
            "PARSEDMARC_GUI_USERNAME": setup_data.admin_username,
            "PARSEDMARC_GUI_PASSWORD": setup_data.admin_password,
            "PARSEDMARC_HOST": setup_data.host,
            "PARSEDMARC_PORT": str(setup_data.port),
            "PARSEDMARC_CORS_ORIGINS": setup_data.cors_origins,
            "PARSEDMARC_LOG_LEVEL": setup_data.log_level,
            "PARSEDMARC_DB_PATH": setup_data.db_path
        }

        for key, value in env_updates.items():
            updated = False
            for i, line in enumerate(lines):
                if line.startswith(f"{key}="):
                    lines[i] = f"{key}={value}"
                    updated = True
                    break
            if not updated:
                lines.append(f"{key}={value}")

        # Write back to .env
        with open(env_path, "w") as f:
            f.write("\n".join(lines))

        # 4. Ensure database directory exists
        db_path = Path(setup_data.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # 5. Update setup status
        setup = get_setup_status(db)
        setup.is_complete = True
        setup.encryption_key_set = True
        setup.admin_credentials_set = True
        setup.ssl_configured = (setup_data.ssl_type != "skip")
        setup.database_configured = True
        setup.server_configured = True
        setup.ssl_type = setup_data.ssl_type if setup_data.ssl_type != "skip" else None
        setup.ssl_domain = setup_data.ssl_domain
        setup.ssl_email = setup_data.ssl_email
        setup.letsencrypt_staging = setup_data.ssl_staging
        setup.completed_at = datetime.utcnow()

        # Store certificate metadata if self-signed
        if setup_data.ssl_type == "self-signed" and ssl_result:
            if not setup.setup_metadata:
                setup.setup_metadata = {}
            setup.setup_metadata["ssl_certificate_serial"] = ssl_result.get("serial_number")
            setup.setup_metadata["ssl_certificate_generated_at"] = datetime.utcnow().isoformat()

        db.commit()

        logger.info("Setup completed successfully")

        response_data = {
            "ssl_configured": setup.ssl_configured,
            "ssl_type": setup.ssl_type,
            "ssl_result": ssl_result,
            "encryption_key_auto_generated": was_key_auto_generated
        }

        # Include encryption key in response if it was auto-generated (so user can save it)
        if was_key_auto_generated:
            response_data["encryption_key"] = encryption_key
            response_data["warning"] = "IMPORTANT: Save the encryption key securely - it cannot be recovered if lost!"

        return SetupStepResponse(
            success=True,
            message="Setup completed successfully! " +
                   ("SAVE THE ENCRYPTION KEY DISPLAYED BELOW! " if was_key_auto_generated else "") +
                   "Please restart the application for changes to take effect.",
            data=response_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete setup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete setup: {str(e)}"
        )


@router.get("/certificate", response_model=CertificateInfo)
def get_certificate_info():
    """Get information about the current SSL certificate."""
    cert_info = cert_service.get_active_certificate()

    if cert_info:
        return CertificateInfo(**cert_info)
    else:
        return CertificateInfo(
            type="none",
            error="No SSL certificate configured"
        )


@router.post("/certificate/renew", response_model=SetupStepResponse)
def renew_certificate(db: Session = Depends(get_db)):
    """Renew Let's Encrypt certificate."""
    try:
        setup = get_setup_status(db)

        if setup.ssl_type != "letsencrypt":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Certificate renewal is only available for Let's Encrypt certificates"
            )

        result = cert_service.renew_letsencrypt_certificate(setup.ssl_domain)

        if result.get("success"):
            return SetupStepResponse(
                success=True,
                message="Certificate renewed successfully",
                data=result
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Certificate renewal failed: {result.get('error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to renew certificate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to renew certificate: {str(e)}"
        )
