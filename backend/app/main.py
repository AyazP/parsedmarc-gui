"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.db.session import engine, Base
from app.services.monitoring_service import MonitoringService
from app.services.update_service import UpdateService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

APP_VERSION = "1.0.0"

# Global service instances
monitoring_service: MonitoringService | None = None
update_service: UpdateService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global monitoring_service, update_service

    logger.info("Starting ParseDMARC Web GUI...")

    # Import all models so SQLAlchemy can create their tables
    from app.models.mailbox_config import MailboxConfig
    from app.models.output_config import OutputConfig
    from app.models.setup import SetupStatus
    from app.models.parse_job import ParseJob
    from app.models.parsed_report import ParsedReport
    from app.models.activity_log import ActivityLog
    from app.models.monitoring_job import MonitoringJob

    # Create database tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # Initialize monitoring service
    logger.info("Initializing monitoring service...")
    from app.services.monitoring_service import MonitoringService
    monitoring_service = MonitoringService()
    await monitoring_service.start()

    # Initialize update service
    logger.info("Initializing update service...")
    update_service = UpdateService(current_version=APP_VERSION)
    await update_service.start()

    logger.info("Application started successfully!")

    yield

    # Shutdown
    logger.info("Shutting down...")
    if monitoring_service:
        await monitoring_service.stop()
    if update_service:
        await update_service.stop()
    logger.info("Shutdown complete.")


# Rate limiter — uses client IP; default limits can be overridden per-route
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

# Create FastAPI app
app = FastAPI(
    title="ParseDMARC Web GUI",
    description="Web interface for ParseDMARC - DMARC report parser and analyzer",
    version=APP_VERSION,
    lifespan=lifespan
)

# Wire rate limiter into the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-CSRF-Token"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that adds security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "frame-ancestors 'none'"
        )
        if settings.ssl_enabled:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


app.add_middleware(SecurityHeadersMiddleware)


# Paths exempt from CSRF validation (login, setup during first-run, health check)
_CSRF_EXEMPT_PREFIXES = ("/api/auth/login", "/api/setup/", "/api/health")


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection.

    For state-changing methods (POST, PUT, DELETE) on non-exempt paths,
    the X-CSRF-Token header must match the csrf_token cookie value.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in ("POST", "PUT", "DELETE"):
            path = request.url.path
            if not any(path.startswith(prefix) for prefix in _CSRF_EXEMPT_PREFIXES):
                header_token = request.headers.get("x-csrf-token")
                cookie_token = request.cookies.get("csrf_token")
                if not header_token or not cookie_token or header_token != cookie_token:
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "CSRF validation failed"},
                    )
        return await call_next(request)


app.add_middleware(CSRFMiddleware)

# Import and register routers
# Import each router individually to handle missing modules gracefully

def _register_router(module_name: str):
    """Import and register an API router, logging errors on failure."""
    import importlib
    try:
        module = importlib.import_module(f"app.api.{module_name}")
        app.include_router(module.router)
        logger.info("Registered %s router", module_name)
    except Exception as e:
        logger.error("Failed to register %s router: %s", module_name, e)

for _router_name in [
    "auth", "setup", "mailbox_configs", "output_configs", "testing",
    "parsing", "monitoring", "dashboard", "updates", "settings",
]:
    _register_router(_router_name)

# Health check endpoint (must be before SPA catch-all)
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "monitoring_active": monitoring_service is not None and monitoring_service.is_running()
    }


@app.get("/api/system/info")
async def system_info():
    """Get system information."""
    return {
        "version": APP_VERSION,
        "database_type": settings.database_type,
    }

# Serve static files (frontend) if available
# NOTE: SPA catch-all must be LAST — it captures all unmatched routes
static_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    @app.get("/")
    async def serve_frontend():
        """Serve the frontend application."""
        return FileResponse(str(static_dir / "index.html"))

    @app.get("/{full_path:path}")
    async def serve_frontend_spa(full_path: str):
        """SPA catch-all: serve index.html for client-side routes."""
        # Never intercept API routes — return 404 so unregistered API
        # endpoints don't get a misleading 405 from this GET-only handler.
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        # Serve actual files from dist if they exist, with path traversal protection
        file_path = (static_dir / full_path).resolve()
        if file_path.is_relative_to(static_dir.resolve()) and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(static_dir / "index.html"))


def _resolve_ssl_files():
    """Resolve SSL certificate and key file paths.

    Returns (certfile, keyfile) tuple, or (None, None) if SSL is not enabled
    or certificate files are not found.
    """
    if not settings.ssl_enabled:
        return None, None

    # Use explicit paths if provided
    if settings.ssl_certfile and settings.ssl_keyfile:
        cert = Path(settings.ssl_certfile)
        key = Path(settings.ssl_keyfile)
        if cert.exists() and key.exists():
            return str(cert), str(key)
        logger.warning(f"SSL enabled but explicit cert/key files not found: {cert}, {key}")
        return None, None

    # Auto-detect from data/certificates/
    cert_dir = settings.data_dir / "certificates"

    # Priority: Let's Encrypt > Custom uploaded > Self-signed
    le_cert = cert_dir / "letsencrypt-fullchain.crt"
    le_key = cert_dir / "letsencrypt.key"
    if le_cert.exists() and le_key.exists():
        return str(le_cert), str(le_key)

    custom_cert = cert_dir / "custom.crt"
    custom_key = cert_dir / "custom.key"
    if custom_cert.exists() and custom_key.exists():
        return str(custom_cert), str(custom_key)

    ss_cert = cert_dir / "selfsigned.crt"
    ss_key = cert_dir / "selfsigned.key"
    if ss_cert.exists() and ss_key.exists():
        return str(ss_cert), str(ss_key)

    logger.warning("SSL enabled but no certificate files found in %s", cert_dir)
    return None, None


if __name__ == "__main__":
    import uvicorn

    kwargs = {
        "app": "app.main:app",
        "host": settings.host,
        "port": settings.port,
        "reload": settings.log_level.upper() == "DEBUG",
        "log_level": settings.log_level.lower(),
    }

    ssl_cert, ssl_key = _resolve_ssl_files()
    if ssl_cert and ssl_key:
        kwargs["ssl_certfile"] = ssl_cert
        kwargs["ssl_keyfile"] = ssl_key
        logger.info("HTTPS enabled (cert=%s)", ssl_cert)
    else:
        if settings.ssl_enabled:
            logger.warning("SSL enabled in config but no valid certificates found — falling back to HTTP")
        logger.info("HTTP mode (no SSL)")

    uvicorn.run(**kwargs)
