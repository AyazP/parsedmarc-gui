"""Testing API endpoints for verifying connections to output destinations."""
import ipaddress
import logging
import socket
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.db.session import get_db
from app.models.output_config import OutputConfig
from app.services.encryption_service import EncryptionService

logger = logging.getLogger(__name__)

# ---------- SSRF Protection ----------

_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local / cloud metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _validate_target_host(host: str) -> None:
    """Validate that a target host does not resolve to a private/blocked IP."""
    try:
        addr_infos = socket.getaddrinfo(host, None)
        for family, _, _, _, sockaddr in addr_infos:
            ip = ipaddress.ip_address(sockaddr[0])
            for network in _BLOCKED_NETWORKS:
                if ip in network:
                    raise ValueError(f"Connection to private/internal addresses is not allowed")
    except socket.gaierror:
        pass  # DNS resolution failed — let the actual connection handle it


def _validate_url(url: str) -> None:
    """Validate a URL is not targeting internal resources."""
    parsed = urlparse(url)
    if not parsed.scheme or parsed.scheme not in ("http", "https"):
        raise ValueError("Only http and https URLs are allowed")
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")
    _validate_target_host(parsed.hostname)

encryption_service = EncryptionService()

# ---------- Schemas ----------


class ConnectionTestResponse(BaseModel):
    """Response schema for a connection test."""
    success: bool
    message: str
    details: Optional[dict] = None


# ---------- Router ----------

router = APIRouter(prefix="/api/test", tags=["Connection Testing"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/output/{config_id}", response_model=ConnectionTestResponse)
@limiter.limit("10/minute")
def test_output_connection(
    request: Request,
    config_id: int,
    db: Session = Depends(get_db),
):
    """
    Test connectivity to an output destination.

    Performs a basic connection check for the configured output type.
    """
    config = db.query(OutputConfig).filter(OutputConfig.id == config_id).first()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Output configuration with ID {config_id} not found",
        )

    settings = encryption_service.decrypt_dict(config.settings)

    try:
        result = _test_output(config.type, settings)
        return result
    except Exception as e:
        logger.error(f"Output connection test failed for config {config_id}: {e}")
        return ConnectionTestResponse(
            success=False,
            message="Connection test failed. Check output settings and try again.",
        )


def _test_output(output_type: str, settings: dict) -> ConnectionTestResponse:
    """Test connection to an output destination based on type."""

    if output_type == "elasticsearch":
        return _test_elasticsearch(settings)
    elif output_type == "opensearch":
        return _test_opensearch(settings)
    elif output_type == "splunk":
        return _test_splunk(settings)
    elif output_type == "kafka":
        return _test_kafka(settings)
    elif output_type == "s3":
        return _test_s3(settings)
    elif output_type == "syslog":
        return _test_syslog(settings)
    elif output_type == "gelf":
        return _test_gelf(settings)
    elif output_type == "webhook":
        return _test_webhook(settings)
    else:
        return ConnectionTestResponse(
            success=False,
            message=f"Unknown output type: {output_type}",
        )


def _test_elasticsearch(settings: dict) -> ConnectionTestResponse:
    """Test Elasticsearch connection."""
    import httpx

    hosts = settings.get("hosts", [])
    if not hosts:
        return ConnectionTestResponse(success=False, message="No hosts configured")

    url = hosts[0].rstrip("/")
    try:
        _validate_url(url)
    except ValueError as e:
        return ConnectionTestResponse(success=False, message=str(e))

    kwargs: dict = {"timeout": 10.0, "verify": settings.get("ssl", True)}

    auth = None
    if settings.get("username") and settings.get("password"):
        auth = (settings["username"], settings["password"])

    headers = {}
    if settings.get("api_key"):
        headers["Authorization"] = f"ApiKey {settings['api_key']}"

    try:
        resp = httpx.get(url, auth=auth, headers=headers, **kwargs)
        resp.raise_for_status()
        info = resp.json()
        return ConnectionTestResponse(
            success=True,
            message=f"Connected to Elasticsearch cluster '{info.get('cluster_name', 'unknown')}'",
            details={"version": info.get("version", {}).get("number")},
        )
    except httpx.ConnectError:
        return ConnectionTestResponse(success=False, message=f"Cannot connect to {url}")
    except httpx.HTTPStatusError as e:
        return ConnectionTestResponse(success=False, message=f"HTTP error: status {e.response.status_code}")


def _test_opensearch(settings: dict) -> ConnectionTestResponse:
    """Test OpenSearch connection (same protocol as Elasticsearch)."""
    return _test_elasticsearch(settings)


def _test_splunk(settings: dict) -> ConnectionTestResponse:
    """Test Splunk HEC connection."""
    import httpx

    url = settings.get("url", "")
    token = settings.get("token", "")
    if not url or not token:
        return ConnectionTestResponse(success=False, message="URL and token are required")

    try:
        _validate_url(url)
    except ValueError as e:
        return ConnectionTestResponse(success=False, message=str(e))

    verify = not settings.get("skip_certificate_verification", False)
    headers = {"Authorization": f"Splunk {token}"}

    try:
        # HEC health check
        health_url = url.replace("/services/collector", "/services/collector/health/1.0")
        resp = httpx.get(health_url, headers=headers, verify=verify, timeout=10.0)
        if resp.status_code == 200:
            return ConnectionTestResponse(success=True, message="Splunk HEC is healthy")
        return ConnectionTestResponse(
            success=False,
            message=f"Splunk HEC returned status {resp.status_code}",
        )
    except httpx.ConnectError:
        return ConnectionTestResponse(success=False, message=f"Cannot connect to {url}")


def _test_kafka(settings: dict) -> ConnectionTestResponse:
    """Test Kafka connection (basic socket check)."""

    servers = settings.get("servers", [])
    if not servers:
        return ConnectionTestResponse(success=False, message="No servers configured")

    host_port = servers[0]
    parts = host_port.rsplit(":", 1)
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 9092

    try:
        _validate_target_host(host)
    except ValueError as e:
        return ConnectionTestResponse(success=False, message=str(e))

    try:
        sock = socket.create_connection((host, port), timeout=5)
        sock.close()
        return ConnectionTestResponse(
            success=True,
            message=f"TCP connection to {host}:{port} successful",
        )
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        return ConnectionTestResponse(success=False, message=f"Cannot connect to {host}:{port}: {e}")


def _test_s3(settings: dict) -> ConnectionTestResponse:
    """Test S3 bucket access (HEAD bucket)."""
    import httpx

    bucket = settings.get("bucket", "")
    region = settings.get("region", "us-east-1")
    if not bucket:
        return ConnectionTestResponse(success=False, message="Bucket name is required")

    # Basic check: try to reach the bucket endpoint
    url = f"https://{bucket}.s3.{region}.amazonaws.com/"
    try:
        resp = httpx.head(url, timeout=10.0)
        if resp.status_code in (200, 301, 403):
            return ConnectionTestResponse(
                success=True,
                message=f"S3 bucket '{bucket}' exists in region '{region}'",
                details={"status_code": resp.status_code},
            )
        return ConnectionTestResponse(
            success=False,
            message=f"Bucket check returned HTTP {resp.status_code}",
        )
    except httpx.ConnectError:
        return ConnectionTestResponse(success=False, message=f"Cannot reach S3 endpoint for bucket '{bucket}'")


def _test_syslog(settings: dict) -> ConnectionTestResponse:
    """Test Syslog server reachability (UDP or TCP socket)."""

    server = settings.get("server", "")
    port = settings.get("port", 514)
    if not server:
        return ConnectionTestResponse(success=False, message="Server is required")

    try:
        _validate_target_host(server)
    except ValueError as e:
        return ConnectionTestResponse(success=False, message=str(e))

    try:
        sock = socket.create_connection((server, port), timeout=5)
        sock.close()
        return ConnectionTestResponse(success=True, message=f"Syslog server {server}:{port} is reachable")
    except (socket.timeout, ConnectionRefusedError, OSError):
        # Syslog often uses UDP, so TCP failure doesn't mean it's down
        return ConnectionTestResponse(
            success=True,
            message=f"TCP check to {server}:{port} failed (syslog may use UDP, which is connectionless)",
            details={"note": "UDP syslog cannot be verified with a connection test"},
        )


def _test_gelf(settings: dict) -> ConnectionTestResponse:
    """Test GELF server reachability."""

    server = settings.get("server", "")
    port = settings.get("port", 12201)
    if not server:
        return ConnectionTestResponse(success=False, message="Server is required")

    try:
        _validate_target_host(server)
    except ValueError as e:
        return ConnectionTestResponse(success=False, message=str(e))

    try:
        sock = socket.create_connection((server, port), timeout=5)
        sock.close()
        return ConnectionTestResponse(success=True, message=f"GELF server {server}:{port} is reachable")
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        return ConnectionTestResponse(success=False, message=f"Cannot connect to {server}:{port}: {e}")


def _test_webhook(settings: dict) -> ConnectionTestResponse:
    """Test webhook URL accessibility."""
    import httpx

    url = settings.get("url", "")
    timeout = settings.get("timeout", 30)
    if not url:
        return ConnectionTestResponse(success=False, message="URL is required")

    try:
        _validate_url(url)
    except ValueError as e:
        return ConnectionTestResponse(success=False, message=str(e))

    headers = settings.get("headers", {})

    try:
        # Send a HEAD request to verify the endpoint exists
        resp = httpx.head(url, headers=headers, timeout=float(timeout))
        return ConnectionTestResponse(
            success=True,
            message=f"Webhook endpoint responded with HTTP {resp.status_code}",
            details={"status_code": resp.status_code},
        )
    except httpx.ConnectError:
        return ConnectionTestResponse(success=False, message=f"Cannot connect to {url}")
    except httpx.HTTPError as e:
        return ConnectionTestResponse(success=False, message=f"HTTP error: {str(e)[:200]}")
