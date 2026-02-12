"""Parsing service for DMARC report processing."""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from parsedmarc import (
    get_dmarc_reports_from_mailbox,
    parse_report_file,
)

from app.models.mailbox_config import MailboxConfig
from app.models.parse_job import ParseJob
from app.models.parsed_report import ParsedReport
from app.models.activity_log import ActivityLog
from app.services.mailbox_service import mailbox_service

logger = logging.getLogger(__name__)


class ParsingService:
    """Service for orchestrating DMARC report parsing."""

    def parse_from_mailbox(
        self,
        db: Session,
        config: MailboxConfig,
        batch_size: Optional[int] = None,
        since: Optional[str] = None,
        test_mode: bool = False,
    ) -> ParseJob:
        """
        Fetch and parse DMARC reports from a mailbox configuration.

        Creates a ParseJob, connects to the mailbox, calls
        get_dmarc_reports_from_mailbox(), stores parsed reports,
        and updates the ParseJob with results.
        """
        job = self._create_parse_job(db, "mailbox_fetch", config.name)
        job.status = "running"
        db.commit()

        try:
            connection = mailbox_service.create_connection(config)

            effective_batch_size = batch_size or config.batch_size or 10
            reports_folder = config.reports_folder or "INBOX"
            archive_folder = config.archive_folder or "Archive"

            logger.info(
                f"Fetching reports from '{config.name}' "
                f"(folder={reports_folder}, batch={effective_batch_size})"
            )

            results = get_dmarc_reports_from_mailbox(
                connection,
                reports_folder=reports_folder,
                archive_folder=archive_folder,
                delete=config.delete_after_processing,
                test=test_mode,
                batch_size=effective_batch_size,
                since=since,
                create_folders=not test_mode,
            )

            self._store_parsing_results(db, job, results)

            agg_count = len(results["aggregate_reports"])
            forensic_count = len(results["forensic_reports"])
            tls_count = len(results["smtp_tls_reports"])

            self._complete_parse_job(db, job, agg_count, forensic_count, tls_count)

            total = agg_count + forensic_count + tls_count
            self._log_activity(
                db,
                "info",
                "mailbox_monitor",
                f"Parsed {total} report(s) from '{config.name}'",
                details={
                    "config_id": config.id,
                    "job_id": job.id,
                    "aggregate": agg_count,
                    "forensic": forensic_count,
                    "smtp_tls": tls_count,
                },
            )
            logger.info(
                f"Mailbox parse complete for '{config.name}': "
                f"{agg_count} aggregate, {forensic_count} forensic, {tls_count} TLS"
            )

        except Exception as e:
            self._fail_parse_job(db, job, str(e))
            self._log_activity(
                db,
                "error",
                "mailbox_monitor",
                f"Failed to parse from '{config.name}': {e}",
            )
            logger.error(
                f"Parsing from mailbox '{config.name}' (id={config.id}) failed: {e}",
                exc_info=True,
            )

        return job

    def parse_from_file(
        self,
        db: Session,
        file_path: str,
        original_filename: str,
    ) -> ParseJob:
        """
        Parse DMARC reports from an uploaded file.

        Supports .xml, .gz, .zip, .eml, and .msg files via parsedmarc's
        parse_report_file() function.
        """
        job = self._create_parse_job(
            db, "file_upload", original_filename, file_path=file_path
        )
        job.status = "running"
        db.commit()

        try:
            logger.info(f"Parsing uploaded file: {original_filename}")
            parsed = parse_report_file(file_path)

            self._store_single_parsed_report(db, job, parsed)

            report_type = parsed.get("report_type", "unknown")
            counts: Dict[str, int] = {"aggregate": 0, "forensic": 0, "smtp_tls": 0}
            if report_type in counts:
                counts[report_type] = 1

            self._complete_parse_job(
                db, job, counts["aggregate"], counts["forensic"], counts["smtp_tls"]
            )

            self._log_activity(
                db,
                "info",
                "file_upload",
                f"Parsed {report_type} report from '{original_filename}'",
                details={"job_id": job.id, "report_type": report_type},
            )
            logger.info(f"File parse complete: {original_filename} ({report_type})")

        except Exception as e:
            self._fail_parse_job(db, job, str(e))
            self._log_activity(
                db,
                "error",
                "file_upload",
                f"Failed to parse '{original_filename}': {e}",
            )
            logger.error(
                f"File parsing failed for {file_path}: {e}", exc_info=True
            )

        return job

    def _store_parsing_results(
        self,
        db: Session,
        job: ParseJob,
        results: dict,
    ) -> None:
        """Store parsed reports from a ParsingResults dict into ParsedReport rows."""
        for report in results.get("aggregate_reports", []):
            metadata = report.get("report_metadata", {})
            policy = report.get("policy_published", {})
            db_report = ParsedReport(
                parse_job_id=job.id,
                report_type="aggregate",
                org_name=metadata.get("org_name"),
                report_id=metadata.get("report_id"),
                domain=policy.get("domain"),
                date_begin=self._parse_date(metadata.get("begin_date")),
                date_end=self._parse_date(metadata.get("end_date")),
                report_json=json.dumps(report, default=str),
            )
            db.add(db_report)

        for report in results.get("forensic_reports", []):
            db_report = ParsedReport(
                parse_job_id=job.id,
                report_type="forensic",
                org_name=None,
                report_id=None,
                domain=report.get("reported_domain"),
                date_begin=self._parse_date(report.get("arrival_date_utc")),
                date_end=None,
                report_json=json.dumps(report, default=str),
            )
            db.add(db_report)

        for report in results.get("smtp_tls_reports", []):
            policies = report.get("policies", [])
            domain = policies[0].get("policy_domain") if policies else None
            db_report = ParsedReport(
                parse_job_id=job.id,
                report_type="smtp_tls",
                org_name=report.get("organization_name"),
                report_id=report.get("report_id"),
                domain=domain,
                date_begin=self._parse_date(report.get("begin_date")),
                date_end=self._parse_date(report.get("end_date")),
                report_json=json.dumps(report, default=str),
            )
            db.add(db_report)

        db.flush()

    def _store_single_parsed_report(
        self,
        db: Session,
        job: ParseJob,
        parsed: dict,
    ) -> None:
        """Store a single ParsedReport from parse_report_file() result."""
        report_type = parsed.get("report_type", "unknown")
        report = parsed.get("report", {})

        if report_type == "aggregate":
            metadata = report.get("report_metadata", {})
            policy = report.get("policy_published", {})
            db_report = ParsedReport(
                parse_job_id=job.id,
                report_type="aggregate",
                org_name=metadata.get("org_name"),
                report_id=metadata.get("report_id"),
                domain=policy.get("domain"),
                date_begin=self._parse_date(metadata.get("begin_date")),
                date_end=self._parse_date(metadata.get("end_date")),
                report_json=json.dumps(report, default=str),
            )
        elif report_type == "forensic":
            db_report = ParsedReport(
                parse_job_id=job.id,
                report_type="forensic",
                domain=report.get("reported_domain"),
                date_begin=self._parse_date(report.get("arrival_date_utc")),
                report_json=json.dumps(report, default=str),
            )
        elif report_type == "smtp_tls":
            policies = report.get("policies", [])
            domain = policies[0].get("policy_domain") if policies else None
            db_report = ParsedReport(
                parse_job_id=job.id,
                report_type="smtp_tls",
                org_name=report.get("organization_name"),
                report_id=report.get("report_id"),
                domain=domain,
                date_begin=self._parse_date(report.get("begin_date")),
                date_end=self._parse_date(report.get("end_date")),
                report_json=json.dumps(report, default=str),
            )
        else:
            logger.warning(f"Unknown report type: {report_type}")
            db_report = ParsedReport(
                parse_job_id=job.id,
                report_type=report_type,
                report_json=json.dumps(report, default=str),
            )

        db.add(db_report)
        db.flush()

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Attempt to parse a date string into a datetime object."""
        if not date_str:
            return None
        try:
            # parsedmarc typically returns ISO-ish or human-readable dates
            from dateparser import parse as dateparse

            result = dateparse(str(date_str))
            return result
        except Exception:
            logger.debug(f"Could not parse date: {date_str}")
            return None

    def _create_parse_job(
        self,
        db: Session,
        job_type: str,
        input_source: str,
        file_path: Optional[str] = None,
    ) -> ParseJob:
        """Create a new ParseJob with status 'pending'."""
        job = ParseJob(
            job_type=job_type,
            status="pending",
            input_source=input_source,
            file_path=file_path,
        )
        db.add(job)
        db.flush()
        logger.info(f"Created parse job {job.id} ({job_type}: {input_source})")
        return job

    def _complete_parse_job(
        self,
        db: Session,
        job: ParseJob,
        aggregate_count: int,
        forensic_count: int,
        smtp_tls_count: int,
    ) -> None:
        """Mark a ParseJob as 'completed' with report counts."""
        job.status = "completed"
        job.aggregate_reports_count = aggregate_count
        job.forensic_reports_count = forensic_count
        job.smtp_tls_reports_count = smtp_tls_count
        job.completed_at = datetime.utcnow()
        db.commit()

    def _fail_parse_job(
        self,
        db: Session,
        job: ParseJob,
        error_message: str,
    ) -> None:
        """Mark a ParseJob as 'failed' with an error message."""
        job.status = "failed"
        job.error_message = error_message
        job.completed_at = datetime.utcnow()
        db.commit()

    def _log_activity(
        self,
        db: Session,
        level: str,
        source: str,
        message: str,
        details: Optional[dict] = None,
    ) -> None:
        """Create an ActivityLog entry."""
        log_entry = ActivityLog(
            level=level,
            source=source,
            message=message,
            details=json.dumps(details, default=str) if details else None,
        )
        db.add(log_entry)
        db.commit()


# Module-level singleton
parsing_service = ParsingService()
