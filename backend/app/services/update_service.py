"""Update checker service for checking GitHub releases."""
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass, field

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com/repos/AyazP/parsedmarc-gui/releases/latest"
GITHUB_RELEASES_URL = "https://github.com/AyazP/parsedmarc-gui/releases"
CACHE_TTL_SECONDS = 3600  # 1 hour


@dataclass
class UpdateInfo:
    """Cached update check result."""
    update_available: bool
    current_version: str
    latest_version: str
    release_url: str
    release_notes: str
    published_at: Optional[str]
    checked_at: datetime
    is_docker: bool
    error: Optional[str] = None


def parse_semver(version: str) -> Tuple[int, int, int]:
    """Parse a semver string like 'v1.2.3' or '1.2.3' into a tuple."""
    cleaned = version.lstrip("v").strip()
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", cleaned)
    if not match:
        raise ValueError(f"Invalid semver: {version}")
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def is_newer(latest: str, current: str) -> bool:
    """Return True if latest version is newer than current."""
    try:
        return parse_semver(latest) > parse_semver(current)
    except ValueError:
        return False


def detect_docker() -> bool:
    """Detect if running inside Docker."""
    if settings.docker_mode:
        return True
    return Path("/.dockerenv").exists()


class UpdateService:
    """Service for checking GitHub releases for updates."""

    def __init__(self, current_version: str):
        self.current_version = current_version
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._is_running = False
        self._cached_result: Optional[UpdateInfo] = None
        self._cache_expires_at: Optional[datetime] = None
        self._is_docker = detect_docker()
        logger.info(
            "UpdateService initialized (version=%s, docker=%s)",
            current_version, self._is_docker,
        )

    async def start(self):
        """Start the update check scheduler."""
        if not settings.update_check_enabled:
            logger.info("Update checking is disabled")
            return
        if self._is_running:
            return

        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(
            func=self._check_for_updates,
            trigger=IntervalTrigger(hours=settings.update_check_interval_hours),
            id="update_check",
            replace_existing=True,
        )
        self.scheduler.start()
        self._is_running = True
        logger.info(
            "UpdateService started (interval=%dh)",
            settings.update_check_interval_hours,
        )

        # Run initial check
        await self._check_for_updates()

    async def stop(self):
        """Stop the update check scheduler."""
        if self.scheduler and self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("UpdateService stopped")

    def is_running(self) -> bool:
        return self._is_running

    def get_cached_result(self) -> Optional[UpdateInfo]:
        """Return cached result (stale or fresh)."""
        return self._cached_result

    async def check_now(self) -> UpdateInfo:
        """Force an immediate update check, bypassing cache."""
        return await self._check_for_updates()

    async def _check_for_updates(self) -> UpdateInfo:
        """Query GitHub API for the latest release."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    GITHUB_API_URL,
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                response.raise_for_status()
                data = response.json()

            latest_version = data.get("tag_name", "")
            release_notes = data.get("body", "") or ""
            release_url = data.get("html_url", GITHUB_RELEASES_URL)
            published_at = data.get("published_at")

            result = UpdateInfo(
                update_available=is_newer(latest_version, self.current_version),
                current_version=self.current_version,
                latest_version=latest_version.lstrip("v"),
                release_url=release_url,
                release_notes=release_notes,
                published_at=published_at,
                checked_at=datetime.utcnow(),
                is_docker=self._is_docker,
            )

        except httpx.HTTPStatusError as e:
            logger.warning("GitHub API error: %s", e.response.status_code)
            result = UpdateInfo(
                update_available=False,
                current_version=self.current_version,
                latest_version=self.current_version,
                release_url=GITHUB_RELEASES_URL,
                release_notes="",
                published_at=None,
                checked_at=datetime.utcnow(),
                is_docker=self._is_docker,
                error=f"GitHub API returned {e.response.status_code}",
            )
        except (httpx.RequestError, Exception) as e:
            logger.warning("Update check failed: %s", str(e))
            result = UpdateInfo(
                update_available=False,
                current_version=self.current_version,
                latest_version=self.current_version,
                release_url=GITHUB_RELEASES_URL,
                release_notes="",
                published_at=None,
                checked_at=datetime.utcnow(),
                is_docker=self._is_docker,
                error=f"Network error: {str(e)}",
            )

        self._cached_result = result
        self._cache_expires_at = datetime.utcnow() + timedelta(seconds=CACHE_TTL_SECONDS)
        return result
