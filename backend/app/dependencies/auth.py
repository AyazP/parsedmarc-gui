"""Authentication dependency for FastAPI endpoints."""
import logging

from fastapi import HTTPException, Request, status

from app.services import auth_service

logger = logging.getLogger(__name__)


def get_current_user(request: Request) -> str:
    """FastAPI dependency that extracts and validates the JWT from the HttpOnly cookie.

    Returns the username on success.
    Raises HTTPException(401) if the cookie is missing or the token is invalid.
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = auth_service.decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    username: str | None = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return username
