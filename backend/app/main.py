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

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global monitoring service instance
monitoring_service: MonitoringService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global monitoring_service

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

    logger.info("Application started successfully!")

    yield

    # Shutdown
    logger.info("Shutting down...")
    if monitoring_service:
        await monitoring_service.stop()
    logger.info("Shutdown complete.")


# Create FastAPI app
app = FastAPI(
    title="ParseDMARC Web GUI",
    description="Web interface for ParseDMARC - DMARC report parser and analyzer",
    version="1.0.0",
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

# Serve static files (frontend) if available
static_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    @app.get("/")
    async def serve_frontend():
        """Serve the frontend application."""
        return FileResponse(str(static_dir / "index.html"))

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "monitoring_active": monitoring_service is not None and monitoring_service.is_running()
    }


@app.get("/api/system/info")
async def system_info():
    """Get system information."""
    return {
        "version": "1.0.0",
        "database": str(settings.db_path),
        "data_directory": str(settings.data_dir),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
