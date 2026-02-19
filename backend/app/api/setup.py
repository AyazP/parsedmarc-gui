"""Setup wizard API endpoints."""
import os
import secrets
from pathlib import Path
from typing import Optional, Union
from datetime import datetime
from urllib.parse import quote_plus
from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, File, status
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet
from slowapi import Limiter
from slowapi.util import get_remote_address

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
    CertificateInfo,
    CertificateValidationResult,
)
from app.services.certificate_service import CertificateService
from app.services import auth_service
from app.services.auth_service import hash_password
from app.dependencies.auth import get_current_user
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/setup", tags=["Setup Wizard"])
limiter = Limiter(key_func=get_remote_address)


def _validate_db_path(db_path: str) -> Path:
    """Validate a SQLite database path is safe (no path traversal)."""
    path = Path(db_path).resolve()
    # Must be within data_dir or current working directory
    allowed_roots = [settings.data_dir.resolve(), Path.cwd().resolve()]
    for root in allowed_roots:
        try:
            path.relative_to(root)
            return path
        except ValueError:
            continue
    raise ValueError(
        f"Database path must be within the data directory ({settings.data_dir})"
    )

# Initialize certificate service
cert_service = CertificateService(cert_dir=settings.data_dir / "certificates")

# Maximum upload size for certificate files (1 MB)
_MAX_CERT_UPLOAD_BYTES = 1 * 1024 * 1024


def _require_setup_incomplete(db: Session) -> None:
    """Guard: reject requests if setup is already complete."""
    setup = db.query(SetupStatus).first()
    if setup and setup.is_complete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Setup is already complete. Use the settings API to make changes.",
        )


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
@limiter.limit("5/minute")
def setup_encryption_key(
    request: Request,
    key_data: EncryptionKeySetup,
    db: Session = Depends(get_db)
):
    """Set up encryption key.

    Validates and saves the encryption key to environment.
    If no key is provided, a new one will be auto-generated.
    """
    _require_setup_incomplete(db)
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
        _secure_write_env(env_path, "\n".join(lines))

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
            detail="Failed to setup encryption key. Check the key format and try again."
        )


@router.post("/admin-credentials", response_model=SetupStepResponse)
@limiter.limit("5/minute")
def setup_admin_credentials(
    request: Request,
    credentials: AdminCredentialsSetup,
    db: Session = Depends(get_db)
):
    """Set up admin credentials.

    Validates and saves admin username and password.
    """
    _require_setup_incomplete(db)
    try:
        # Update .env file
        env_path = Path(__file__).parent.parent.parent.parent / ".env"

        # Read existing .env
        env_content = ""
        if env_path.exists():
            with open(env_path, "r") as f:
                env_content = f.read()

        # Hash the password with bcrypt before storing
        password_hash = hash_password(credentials.password)

        # Update credentials
        lines = env_content.split("\n")
        username_updated = False
        password_updated = False

        for i, line in enumerate(lines):
            if line.startswith("PARSEDMARC_GUI_USERNAME="):
                lines[i] = f"PARSEDMARC_GUI_USERNAME={credentials.username}"
                username_updated = True
            elif line.startswith("PARSEDMARC_GUI_PASSWORD_HASH="):
                lines[i] = f"PARSEDMARC_GUI_PASSWORD_HASH={password_hash}"
                password_updated = True

        # Remove any legacy plaintext password line
        lines = [l for l in lines if not l.startswith("PARSEDMARC_GUI_PASSWORD=")]

        if not username_updated:
            lines.append(f"PARSEDMARC_GUI_USERNAME={credentials.username}")
        if not password_updated:
            lines.append(f"PARSEDMARC_GUI_PASSWORD_HASH={password_hash}")

        # Write back to .env
        _secure_write_env(env_path, "\n".join(lines))

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
            detail="Failed to setup admin credentials. Please try again."
        )


@router.post("/ssl", response_model=SetupStepResponse)
def setup_ssl(
    ssl_config: Union[SSLSetupSelfSigned, SSLSetupLetsEncrypt, SSLSetupCustom],
    db: Session = Depends(get_db)
):
    """Set up SSL/TLS certificate.

    Supports self-signed, Let's Encrypt, or custom certificates.
    """
    _require_setup_incomplete(db)
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
            # Dispatch between HTTP-01 and DNS-01 challenge
            if ssl_config.challenge_type == "dns-01":
                result = cert_service.request_letsencrypt_certificate_dns(
                    domain=ssl_config.domain,
                    email=ssl_config.email,
                    provider=ssl_config.dns_provider,
                    credentials=ssl_config.dns_credentials or {},
                    staging=ssl_config.staging,
                )
            else:
                webroot = Path(ssl_config.webroot_path) if ssl_config.webroot_path else None
                result = cert_service.request_letsencrypt_certificate(
                    domain=ssl_config.domain,
                    email=ssl_config.email,
                    webroot_path=webroot,
                    staging=ssl_config.staging,
                )

            if result.get("success"):
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

        # Enable SSL in .env so uvicorn uses HTTPS on next restart
        env_path = Path(__file__).parent.parent.parent.parent / ".env"
        env_content = ""
        if env_path.exists():
            with open(env_path, "r") as f:
                env_content = f.read()
        lines = env_content.split("\n")
        ssl_updated = False
        for i, line in enumerate(lines):
            if line.startswith("PARSEDMARC_SSL_ENABLED="):
                lines[i] = "PARSEDMARC_SSL_ENABLED=true"
                ssl_updated = True
                break
        if not ssl_updated:
            lines.append("PARSEDMARC_SSL_ENABLED=true")
        _secure_write_env(env_path, "\n".join(lines))

        logger.info(f"SSL configured successfully: {ssl_config.type}")

        return SetupStepResponse(
            success=True,
            message=f"SSL certificate configured successfully ({ssl_config.type}). Restart the application to enable HTTPS.",
            data=result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to setup SSL: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to setup SSL. Check certificate settings and try again."
        )


@router.post("/server", response_model=SetupStepResponse)
def setup_server(
    server_config: ServerSetup,
    db: Session = Depends(get_db)
):
    """Set up server configuration."""
    _require_setup_incomplete(db)
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
        _secure_write_env(env_path, "\n".join(lines))

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
            detail="Failed to setup server configuration. Please try again."
        )


def _build_database_url(db_type: str, db_host: str, db_port: int,
                        db_name: str, db_user: str, db_password: str) -> str:
    """Build a SQLAlchemy database URL from setup fields."""
    user = quote_plus(db_user)
    password = quote_plus(db_password)
    if db_type == "postgresql":
        return f"postgresql+psycopg2://{user}:{password}@{db_host}:{db_port}/{db_name}"
    elif db_type == "mysql":
        return f"mysql+pymysql://{user}:{password}@{db_host}:{db_port}/{db_name}"
    raise ValueError(f"Unsupported database type: {db_type}")


@router.post("/database", response_model=SetupStepResponse)
def setup_database(
    db_config: DatabaseSetup,
    db: Session = Depends(get_db)
):
    """Set up database configuration."""
    _require_setup_incomplete(db)
    try:
        env_path = Path(__file__).parent.parent.parent.parent / ".env"
        env_content = ""
        if env_path.exists():
            with open(env_path, "r") as f:
                env_content = f.read()

        lines = env_content.split("\n")

        if db_config.db_type == "sqlite":
            # Validate path before using
            validated_path = _validate_db_path(db_config.db_path)
            # SQLite: set DB_PATH, remove DATABASE_URL if present
            _update_env_lines(lines, "PARSEDMARC_DB_PATH", str(validated_path))
            _remove_env_line(lines, "PARSEDMARC_DATABASE_URL")

            validated_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # PostgreSQL/MySQL: set DATABASE_URL
            database_url = _build_database_url(
                db_config.db_type, db_config.db_host or "localhost",
                db_config.db_port or (5432 if db_config.db_type == "postgresql" else 3306),
                db_config.db_name or "", db_config.db_user or "",
                db_config.db_password or "",
            )
            _update_env_lines(lines, "PARSEDMARC_DATABASE_URL", database_url)

        _secure_write_env(env_path, "\n".join(lines))

        setup = get_setup_status(db)
        setup.database_configured = True
        db.commit()

        logger.info(f"Database configuration saved successfully (type={db_config.db_type})")

        return SetupStepResponse(
            success=True,
            message="Database configuration saved successfully"
        )

    except Exception as e:
        logger.error(f"Failed to setup database: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to setup database. Check configuration and try again."
        )


@router.post("/complete", response_model=SetupStepResponse)
@limiter.limit("5/minute")
def complete_setup(
    request: Request,
    response: Response,
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
            if setup_data.ssl_challenge_type == "dns-01":
                ssl_result = cert_service.request_letsencrypt_certificate_dns(
                    domain=setup_data.ssl_domain,
                    email=setup_data.ssl_email,
                    provider=setup_data.ssl_dns_provider,
                    credentials=setup_data.ssl_dns_credentials or {},
                    staging=setup_data.ssl_staging,
                )
            else:
                ssl_result = cert_service.request_letsencrypt_certificate(
                    domain=setup_data.ssl_domain,
                    email=setup_data.ssl_email,
                    staging=setup_data.ssl_staging,
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

        # Hash admin password with bcrypt
        password_hash = hash_password(setup_data.admin_password)

        # Generate JWT secret key
        jwt_secret_key = secrets.token_urlsafe(64)

        # Settings to update (use generated encryption_key, not from setup_data)
        env_updates = {
            "PARSEDMARC_ENCRYPTION_KEY": encryption_key,
            "PARSEDMARC_GUI_USERNAME": setup_data.admin_username,
            "PARSEDMARC_GUI_PASSWORD_HASH": password_hash,
            "PARSEDMARC_SECRET_KEY": jwt_secret_key,
            "PARSEDMARC_HOST": setup_data.host,
            "PARSEDMARC_PORT": str(setup_data.port),
            "PARSEDMARC_CORS_ORIGINS": setup_data.cors_origins,
            "PARSEDMARC_LOG_LEVEL": setup_data.log_level,
            "PARSEDMARC_SSL_ENABLED": "true" if setup_data.ssl_type != "skip" else "false"
        }

        # Database configuration
        db_type = getattr(setup_data, "db_type", "sqlite") or "sqlite"
        if db_type == "sqlite":
            env_updates["PARSEDMARC_DB_PATH"] = setup_data.db_path
        else:
            database_url = _build_database_url(
                db_type,
                setup_data.db_host or "localhost",
                setup_data.db_port or (5432 if db_type == "postgresql" else 3306),
                setup_data.db_name or "",
                setup_data.db_user or "",
                setup_data.db_password or "",
            )
            env_updates["PARSEDMARC_DATABASE_URL"] = database_url

        for key, value in env_updates.items():
            _update_env_lines(lines, key, value)

        # Remove legacy plaintext password (replaced by hash above)
        _remove_env_line(lines, "PARSEDMARC_GUI_PASSWORD")

        # Remove conflicting DB keys
        if db_type == "sqlite":
            _remove_env_line(lines, "PARSEDMARC_DATABASE_URL")
        else:
            _remove_env_line(lines, "PARSEDMARC_DB_PATH")

        # Write back to .env
        _secure_write_env(env_path, "\n".join(lines))

        # 4. Ensure database directory exists (SQLite only)
        if db_type == "sqlite":
            validated_db_path = _validate_db_path(setup_data.db_path)
            validated_db_path.parent.mkdir(parents=True, exist_ok=True)

        # 5. Update in-memory settings so login works without a server restart
        settings.gui_username = setup_data.admin_username
        settings.gui_password_hash = password_hash
        settings.gui_password_plain = None
        settings.secret_key = jwt_secret_key
        settings.ssl_enabled = (setup_data.ssl_type != "skip")
        settings.encryption_key = encryption_key
        settings.host = setup_data.host
        settings.port = setup_data.port

        # 6. Update setup status
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

        # 7. Auto-login: set auth cookies so the user is immediately authenticated
        access_token = auth_service.create_access_token(subject=setup_data.admin_username)
        csrf_token = auth_service.generate_csrf_token()

        # Don't set secure=True yet — the server is still on HTTP at this point
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            path="/",
            max_age=settings.access_token_expire_minutes * 60,
        )
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,
            secure=False,
            samesite="strict",
            path="/",
            max_age=settings.access_token_expire_minutes * 60,
        )

        # Build the redirect URL for the frontend
        scheme = "https" if setup_data.ssl_type != "skip" else "http"
        host_for_url = setup_data.host if setup_data.host != "0.0.0.0" else "localhost"
        default_port = 443 if scheme == "https" else 80
        port_suffix = "" if setup_data.port == default_port else f":{setup_data.port}"
        redirect_url = f"{scheme}://{host_for_url}{port_suffix}"

        response_data = {
            "ssl_configured": setup.ssl_configured,
            "ssl_type": setup.ssl_type,
            "ssl_result": ssl_result,
            "encryption_key_auto_generated": was_key_auto_generated,
            "redirect_url": redirect_url,
            "needs_restart": setup_data.ssl_type != "skip",
        }

        # Include encryption key in response if it was auto-generated (so user can save it)
        if was_key_auto_generated:
            response_data["encryption_key"] = encryption_key
            response_data["warning"] = "IMPORTANT: Save the encryption key securely - it cannot be recovered if lost!"

        return SetupStepResponse(
            success=True,
            message="Setup completed successfully! " +
                   ("SAVE THE ENCRYPTION KEY DISPLAYED BELOW! " if was_key_auto_generated else "") +
                   ("Restart the server to enable HTTPS." if setup_data.ssl_type != "skip" else ""),
            data=response_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete setup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete setup. Check configuration and try again."
        )


@router.get("/certificate", response_model=CertificateInfo)
def get_certificate_info(_user: str = Depends(get_current_user)):
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
def renew_certificate(db: Session = Depends(get_db), _user: str = Depends(get_current_user)):
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
            detail="Failed to renew certificate. Check server logs for details."
        )


# ------------------------------------------------------------------ #
#  Server restart
# ------------------------------------------------------------------ #

@router.post("/restart", response_model=SetupStepResponse)
async def restart_server(
    request: Request,
    db: Session = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    """Restart the server to apply new configuration (e.g. HTTPS).

    This schedules a restart after a short delay so the response can be sent.
    The server re-launches via ``python -m app.main`` which reads the
    updated .env and applies SSL if configured.
    """
    import asyncio
    import subprocess
    import sys
    import os as _os
    import platform

    backend_dir = str(Path(__file__).parent.parent.parent)

    async def _do_restart():
        await asyncio.sleep(1.5)
        if platform.system() == "Windows":
            # On Windows, os.execv behaviour is unreliable for long-running
            # server processes.  Spawn a detached child and exit instead.
            subprocess.Popen(
                [sys.executable, "-m", "app.main"],
                cwd=backend_dir,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            )
            _os._exit(0)
        else:
            _os.chdir(backend_dir)
            _os.execv(sys.executable, [sys.executable, "-m", "app.main"])

    asyncio.get_running_loop().create_task(_do_restart())

    scheme = "https" if settings.ssl_enabled else "http"
    host = settings.host if settings.host != "0.0.0.0" else "localhost"
    default_port = 443 if scheme == "https" else 80
    port_suffix = "" if settings.port == default_port else f":{settings.port}"

    return SetupStepResponse(
        success=True,
        message="Server is restarting...",
        data={"redirect_url": f"{scheme}://{host}{port_suffix}"},
    )


# ------------------------------------------------------------------ #
#  .env helpers
# ------------------------------------------------------------------ #

def _secure_write_env(env_path: Path, content: str) -> None:
    """Write content to .env file with restrictive permissions."""
    with open(env_path, "w") as f:
        f.write(content)
    try:
        os.chmod(env_path, 0o600)
    except OSError:
        pass  # chmod not supported on Windows


def _update_env_lines(lines: list, key: str, value: str) -> None:
    """Update or append a key=value pair in an env lines list (in-place)."""
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            return
    lines.append(f"{key}={value}")


def _remove_env_line(lines: list, key: str) -> None:
    """Remove a key from an env lines list (in-place)."""
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines.pop(i)
            return


# ------------------------------------------------------------------ #
#  Certificate Upload & Validation
# ------------------------------------------------------------------ #

def _update_env_ssl(cert_path: str, key_path: str) -> None:
    """Write PARSEDMARC_SSL_CERTFILE, PARSEDMARC_SSL_KEYFILE, and
    PARSEDMARC_SSL_ENABLED into .env."""
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    env_content = ""
    if env_path.exists():
        with open(env_path, "r") as f:
            env_content = f.read()

    lines = env_content.split("\n")
    updates = {
        "PARSEDMARC_SSL_ENABLED": "true",
        "PARSEDMARC_SSL_CERTFILE": cert_path,
        "PARSEDMARC_SSL_KEYFILE": key_path,
    }
    for key, value in updates.items():
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}")

    _secure_write_env(env_path, "\n".join(lines))


@router.post("/ssl/upload", response_model=SetupStepResponse)
async def upload_ssl_certificate(
    certificate: UploadFile = File(..., description="PEM certificate file"),
    private_key: UploadFile = File(..., description="PEM private key file"),
    chain: Optional[UploadFile] = File(None, description="PEM chain file (optional)"),
    db: Session = Depends(get_db),
    _user: str = Depends(get_current_user),
):
    """Upload and apply a custom SSL certificate.

    Validates the certificate/key pair before saving.
    """
    try:
        cert_data = await certificate.read(_MAX_CERT_UPLOAD_BYTES + 1)
        key_data = await private_key.read(_MAX_CERT_UPLOAD_BYTES + 1)
        chain_data = await chain.read(_MAX_CERT_UPLOAD_BYTES + 1) if chain else None

        for name, data in [("Certificate", cert_data), ("Private key", key_data), ("Chain", chain_data)]:
            if data and len(data) > _MAX_CERT_UPLOAD_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"{name} file exceeds maximum size of 1 MB",
                )

        result = cert_service.save_uploaded_certificate(
            cert_data, key_data, chain_data
        )

        # Update setup status
        setup = get_setup_status(db)
        setup.ssl_configured = True
        setup.ssl_type = "custom"
        db.commit()

        # Update .env to point to the saved files
        _update_env_ssl(result["certificate"], result["private_key"])

        return SetupStepResponse(
            success=True,
            message=(
                "Custom certificate uploaded and validated successfully. "
                "Restart the application to apply."
            ),
            data=result,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate validation failed: {e}",
        )
    except Exception as e:
        logger.error(f"Failed to upload certificate: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload certificate. Check server logs for details.",
        )


@router.post("/ssl/validate", response_model=CertificateValidationResult)
async def validate_ssl_certificate(
    certificate: UploadFile = File(..., description="PEM certificate file"),
    private_key: UploadFile = File(..., description="PEM private key file"),
    chain: Optional[UploadFile] = File(None, description="PEM chain file (optional)"),
    _user: str = Depends(get_current_user),
):
    """Validate a certificate/key pair without saving.

    Use this to check files before uploading.
    """
    try:
        cert_data = await certificate.read(_MAX_CERT_UPLOAD_BYTES + 1)
        key_data = await private_key.read(_MAX_CERT_UPLOAD_BYTES + 1)
        chain_data = await chain.read(_MAX_CERT_UPLOAD_BYTES + 1) if chain else None

        for name, data in [("Certificate", cert_data), ("Private key", key_data), ("Chain", chain_data)]:
            if data and len(data) > _MAX_CERT_UPLOAD_BYTES:
                return CertificateValidationResult(valid=False, error=f"{name} file exceeds maximum size of 1 MB")

        result = cert_service.validate_certificate_pair(
            cert_data, key_data, chain_data
        )
        return CertificateValidationResult(**result)

    except ValueError as e:
        return CertificateValidationResult(valid=False, error=str(e))
