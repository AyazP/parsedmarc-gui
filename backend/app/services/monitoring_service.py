"""Monitoring service for managing background mailbox monitoring jobs."""
import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class MonitoringService:
    """Service for managing background mailbox monitoring jobs using APScheduler."""

    def __init__(self):
        """Initialize the monitoring service."""
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._is_running = False
        logger.info("MonitoringService initialized")

    async def start(self):
        """Start the monitoring service and scheduler."""
        if self._is_running:
            logger.warning("MonitoringService is already running")
            return

        logger.info("Starting MonitoringService...")
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        self._is_running = True
        logger.info("MonitoringService started successfully")

        # TODO: Load existing monitoring jobs from database and resume them

    async def stop(self):
        """Stop the monitoring service and all scheduled jobs."""
        if not self._is_running:
            logger.warning("MonitoringService is not running")
            return

        logger.info("Stopping MonitoringService...")
        if self.scheduler:
            self.scheduler.shutdown(wait=True)
        self._is_running = False
        logger.info("MonitoringService stopped successfully")

    def is_running(self) -> bool:
        """Check if the monitoring service is running."""
        return self._is_running

    async def add_monitoring_job(self, mailbox_config_id: int, watch_interval: int = 60):
        """
        Add a monitoring job for a mailbox configuration.

        Args:
            mailbox_config_id: ID of the mailbox configuration
            watch_interval: Interval in seconds between mailbox checks
        """
        if not self._is_running:
            raise RuntimeError("MonitoringService is not running")

        job_id = f"monitor_mailbox_{mailbox_config_id}"
        logger.info(f"Adding monitoring job: {job_id} (interval: {watch_interval}s)")

        self.scheduler.add_job(
            func=self._check_mailbox,
            args=[mailbox_config_id],
            trigger=IntervalTrigger(seconds=watch_interval),
            id=job_id,
            replace_existing=True,
        )

    async def remove_monitoring_job(self, mailbox_config_id: int):
        """
        Remove a monitoring job for a mailbox configuration.

        Args:
            mailbox_config_id: ID of the mailbox configuration
        """
        if not self._is_running:
            raise RuntimeError("MonitoringService is not running")

        job_id = f"monitor_mailbox_{mailbox_config_id}"
        logger.info(f"Removing monitoring job: {job_id}")

        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        else:
            logger.warning(f"Monitoring job {job_id} not found")

    async def _check_mailbox(self, mailbox_config_id: int):
        """
        Background task to check a mailbox for new DMARC reports.

        Args:
            mailbox_config_id: ID of the mailbox configuration
        """
        from app.db.session import SessionLocal
        from app.models.mailbox_config import MailboxConfig
        from app.models.monitoring_job import MonitoringJob
        from app.services.parsing_service import parsing_service

        db = SessionLocal()
        mon_job = None
        try:
            config = (
                db.query(MailboxConfig)
                .filter(MailboxConfig.id == mailbox_config_id)
                .first()
            )
            if not config or not config.enabled:
                logger.warning(
                    f"Mailbox config {mailbox_config_id} not found or disabled, skipping"
                )
                return

            # Update monitoring job status
            mon_job = (
                db.query(MonitoringJob)
                .filter(MonitoringJob.mailbox_config_id == mailbox_config_id)
                .first()
            )
            if mon_job:
                mon_job.last_run_at = datetime.utcnow()
                mon_job.status = "running"
                db.commit()

            # Run the parsing
            logger.info(f"Background check: parsing from mailbox '{config.name}'")
            parse_job = parsing_service.parse_from_mailbox(db=db, config=config)

            # Update monitoring job with results
            if mon_job:
                if parse_job.status == "completed":
                    mon_job.status = "running"  # Still active for next cycle
                    mon_job.last_success_at = datetime.utcnow()
                    mon_job.last_error = None
                    mon_job.reports_processed += (
                        parse_job.aggregate_reports_count
                        + parse_job.forensic_reports_count
                        + parse_job.smtp_tls_reports_count
                    )
                else:
                    mon_job.status = "error"
                    mon_job.last_error = parse_job.error_message
                db.commit()

        except Exception as e:
            logger.error(
                f"Error checking mailbox {mailbox_config_id}: {e}", exc_info=True
            )
            if mon_job:
                mon_job.status = "error"
                mon_job.last_error = str(e)
                try:
                    db.commit()
                except Exception:
                    db.rollback()
        finally:
            db.close()
