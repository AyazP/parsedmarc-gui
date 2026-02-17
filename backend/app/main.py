"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

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


# Create FastAPI app
app = FastAPI(
    title="ParseDMARC Web GUI",
    description="Web interface for ParseDMARC - DMARC report parser and analyzer",
    version=APP_VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers
# Import each router individually to handle missing modules gracefully

# Setup wizard router (should always be available)
try:
    from app.api import setup
    app.include_router(setup.router)
    logger.info("Registered setup router")
except ImportError as e:
    logger.warning(f"setup router not available: {e}")

try:
    from app.api import mailbox_configs
    app.include_router(mailbox_configs.router)
    logger.info("Registered mailbox_configs router")
except ImportError as e:
    logger.warning(f"mailbox_configs router not available: {e}")

try:
    from app.api import output_configs
    app.include_router(output_configs.router)
    logger.info("Registered output_configs router")
except ImportError as e:
    logger.warning(f"output_configs router not available: {e}")

try:
    from app.api import testing
    app.include_router(testing.router)
    logger.info("Registered testing router")
except ImportError as e:
    logger.warning(f"testing router not available: {e}")

try:
    from app.api import parsing
    app.include_router(parsing.router)
    logger.info("Registered parsing router")
except ImportError as e:
    logger.warning(f"parsing router not available: {e}")

try:
    from app.api import monitoring
    app.include_router(monitoring.router)
    logger.info("Registered monitoring router")
except ImportError as e:
    logger.warning(f"monitoring router not available: {e}")

try:
    from app.api import dashboard
    app.include_router(dashboard.router)
    logger.info("Registered dashboard router")
except ImportError as e:
    logger.warning(f"dashboard router not available: {e}")

try:
    from app.api import updates
    app.include_router(updates.router)
    logger.info("Registered updates router")
except ImportError as e:
    logger.warning(f"updates router not available: {e}")

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
        "database": str(settings.db_path),
        "data_directory": str(settings.data_dir),
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
        # Serve actual files from assets if they exist
        file_path = static_dir / full_path
        if file_path.exists() and file_path.is_file():
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

    # Prefer Let's Encrypt over self-signed
    le_cert = cert_dir / "letsencrypt-fullchain.crt"
    le_key = cert_dir / "letsencrypt.key"
    if le_cert.exists() and le_key.exists():
        return str(le_cert), str(le_key)

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
        "reload": True,
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
