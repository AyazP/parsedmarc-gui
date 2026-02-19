"""Authentication API endpoints."""
import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.dependencies.auth import get_current_user
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
limiter = Limiter(key_func=get_remote_address)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)


class LoginResponse(BaseModel):
    success: bool
    user: dict


class UserResponse(BaseModel):
    username: str


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(request: Request, response: Response, credentials: LoginRequest):
    """Authenticate and set HttpOnly JWT cookie + CSRF cookie."""
    # Verify username
    if credentials.username != settings.gui_username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password — supports both bcrypt hash and plaintext (legacy)
    password_valid = False
    needs_hash_upgrade = False

    if settings.gui_password_hash:
        # Modern: bcrypt hash
        password_valid = auth_service.verify_password(
            credentials.password, settings.gui_password_hash
        )
    elif settings.gui_password_plain:
        # Legacy: plaintext password — verify directly
        password_valid = credentials.password == settings.gui_password_plain
        if password_valid:
            needs_hash_upgrade = True
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No password configured. Run setup first.",
        )

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Auto-upgrade plaintext password to bcrypt hash
    if needs_hash_upgrade:
        _upgrade_password_hash(credentials.password)

    # Create JWT access token
    access_token = auth_service.create_access_token(subject=credentials.username)

    # Create CSRF token
    csrf_token = auth_service.generate_csrf_token()

    # Set HttpOnly cookie for JWT (browser can't read this via JS)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.ssl_enabled,
        samesite="lax",
        path="/",
        max_age=settings.access_token_expire_minutes * 60,
    )

    # Set JS-readable cookie for CSRF token (frontend reads this to send as header)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=False,
        secure=settings.ssl_enabled,
        samesite="strict",
        path="/",
        max_age=settings.access_token_expire_minutes * 60,
    )

    logger.info("User '%s' logged in successfully", credentials.username)

    return LoginResponse(
        success=True,
        user={"username": credentials.username},
    )


@router.post("/logout")
def logout(request: Request, response: Response):
    """Clear authentication cookies."""
    username = None
    try:
        username = get_current_user(request)
    except HTTPException:
        pass  # Allow logout even if token is expired

    response.delete_cookie("access_token", path="/")
    response.delete_cookie("csrf_token", path="/")

    if username:
        logger.info("User '%s' logged out", username)

    return {"success": True}


@router.get("/me", response_model=UserResponse)
def get_me(request: Request):
    """Get the current authenticated user."""
    username = get_current_user(request)
    return UserResponse(username=username)


def _upgrade_password_hash(plaintext_password: str) -> None:
    """Auto-upgrade a plaintext password to bcrypt hash in .env.

    This runs once on first login after upgrading from a legacy installation.
    """
    try:
        hashed = auth_service.hash_password(plaintext_password)
        env_path = Path(__file__).parent.parent.parent.parent / ".env"

        if not env_path.exists():
            return

        with open(env_path, "r") as f:
            content = f.read()

        lines = content.split("\n")
        new_lines = []
        hash_added = False

        for line in lines:
            # Remove the old plaintext password line
            if line.startswith("PARSEDMARC_GUI_PASSWORD="):
                continue
            # Check if hash already exists
            if line.startswith("PARSEDMARC_GUI_PASSWORD_HASH="):
                hash_added = True
            new_lines.append(line)

        if not hash_added:
            new_lines.append(f"PARSEDMARC_GUI_PASSWORD_HASH={hashed}")

        with open(env_path, "w") as f:
            f.write("\n".join(new_lines))

        try:
            os.chmod(env_path, 0o600)
        except OSError:
            pass  # Windows

        logger.info("Auto-upgraded plaintext password to bcrypt hash in .env")
    except Exception as e:
        logger.warning("Failed to auto-upgrade password hash: %s", e)
