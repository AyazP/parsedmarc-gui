"""SSL/TLS certificate management service."""
import os
import re
import ssl
import shutil
import subprocess
import tempfile
import ipaddress
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)

# Validation patterns for user-supplied inputs used in subprocesses/paths
_DOMAIN_RE = re.compile(r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$")
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def _validate_domain(domain: str) -> str:
    """Validate and return a safe domain name."""
    domain = domain.strip().lower()
    if not domain or len(domain) > 253 or not _DOMAIN_RE.match(domain):
        raise ValueError(f"Invalid domain name")
    return domain


def _validate_email(email: str) -> str:
    """Validate and return a safe email address."""
    email = email.strip().lower()
    if not email or len(email) > 254 or not _EMAIL_RE.match(email):
        raise ValueError(f"Invalid email address")
    return email


class CertificateService:
    """Service for managing SSL/TLS certificates."""

    def __init__(self, cert_dir: Path):
        self.cert_dir = cert_dir
        self.cert_dir.mkdir(parents=True, exist_ok=True)

        # Certificate file paths
        self.self_signed_key = self.cert_dir / "selfsigned.key"
        self.self_signed_cert = self.cert_dir / "selfsigned.crt"
        self.letsencrypt_key = self.cert_dir / "letsencrypt.key"
        self.letsencrypt_cert = self.cert_dir / "letsencrypt.crt"
        self.letsencrypt_chain = self.cert_dir / "letsencrypt-chain.crt"
        self.letsencrypt_fullchain = self.cert_dir / "letsencrypt-fullchain.crt"
        self.custom_cert = self.cert_dir / "custom.crt"
        self.custom_key = self.cert_dir / "custom.key"
        self.custom_chain = self.cert_dir / "custom-chain.crt"
        self.dns_credentials_dir = self.cert_dir / "dns_credentials"

    # ------------------------------------------------------------------ #
    #  Certificate Validation
    # ------------------------------------------------------------------ #

    def validate_certificate_pair(
        self,
        cert_pem: bytes,
        key_pem: bytes,
        chain_pem: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Validate a certificate/key pair before applying.

        Performs:
        1. PEM parsing of cert and key
        2. Public key matching (cert ↔ key)
        3. Expiry check
        4. Chain validation (if provided)
        5. SSL context load test

        Returns dict with valid, subject, issuer, expires, etc.
        Raises ValueError on hard failures.
        """
        # 1. Parse certificate
        try:
            cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
        except Exception as e:
            raise ValueError(f"Invalid certificate PEM: {e}")

        # 2. Parse private key
        try:
            key = serialization.load_pem_private_key(
                key_pem, password=None, backend=default_backend()
            )
        except Exception as e:
            raise ValueError(f"Invalid private key PEM: {e}")

        # 3. Compare public keys
        cert_pub_bytes = cert.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        key_pub_bytes = key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        if cert_pub_bytes != key_pub_bytes:
            raise ValueError("Certificate and private key do not match")

        # 4. Expiry check
        now = datetime.utcnow()
        is_expired = cert.not_valid_after < now
        days_until_expiry = (cert.not_valid_after - now).days

        if is_expired:
            raise ValueError(
                f"Certificate has expired (expired {abs(days_until_expiry)} days ago)"
            )

        warning = None
        if days_until_expiry < 7:
            warning = f"Certificate expires in {days_until_expiry} days"

        # 5. Chain validation
        if chain_pem:
            try:
                x509.load_pem_x509_certificate(chain_pem, default_backend())
            except Exception as e:
                raise ValueError(f"Invalid chain certificate PEM: {e}")

        # 6. SSL context test — definitive check that Python can use this pair
        try:
            self._test_ssl_context(cert_pem, key_pem)
        except Exception as e:
            raise ValueError(f"SSL context test failed: {e}")

        result: Dict[str, Any] = {
            "valid": True,
            "subject": cert.subject.rfc4514_string(),
            "issuer": cert.issuer.rfc4514_string(),
            "expires": cert.not_valid_after.isoformat(),
            "days_until_expiry": days_until_expiry,
            "is_self_signed": cert.issuer == cert.subject,
        }
        if warning:
            result["warning"] = warning
        return result

    def validate_certificate_files(
        self,
        cert_path: Path,
        key_path: Path,
        chain_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Convenience wrapper — reads files then validates."""
        cert_pem = cert_path.read_bytes()
        key_pem = key_path.read_bytes()
        chain_pem = chain_path.read_bytes() if chain_path and chain_path.exists() else None
        return self.validate_certificate_pair(cert_pem, key_pem, chain_pem)

    def _test_ssl_context(self, cert_pem: bytes, key_pem: bytes) -> None:
        """Create a test SSL context to verify cert/key work together."""
        cert_tmp = None
        key_tmp = None
        try:
            cert_tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix=".crt"
            )
            cert_tmp.write(cert_pem)
            cert_tmp.close()

            key_tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix=".key"
            )
            key_tmp.write(key_pem)
            key_tmp.close()

            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ctx.load_cert_chain(certfile=cert_tmp.name, keyfile=key_tmp.name)
        finally:
            if cert_tmp:
                os.unlink(cert_tmp.name)
            if key_tmp:
                os.unlink(key_tmp.name)

    # ------------------------------------------------------------------ #
    #  Custom Certificate Upload
    # ------------------------------------------------------------------ #

    def save_uploaded_certificate(
        self,
        cert_data: bytes,
        key_data: bytes,
        chain_data: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Validate and save an uploaded certificate.

        Saves to staging files first, validates, then atomically renames
        to the final paths.
        """
        # Validate before touching the filesystem
        validation = self.validate_certificate_pair(cert_data, key_data, chain_data)

        # Write to staging paths
        staging_cert = self.cert_dir / "custom.crt.tmp"
        staging_key = self.cert_dir / "custom.key.tmp"
        staging_chain = self.cert_dir / "custom-chain.crt.tmp"

        try:
            staging_cert.write_bytes(cert_data)
            staging_key.write_bytes(key_data)
            if chain_data:
                staging_chain.write_bytes(chain_data)

            # Validate staged files (belt and suspenders)
            chain_arg = staging_chain if chain_data else None
            self.validate_certificate_files(staging_cert, staging_key, chain_arg)

            # Atomic rename to final paths
            staging_cert.replace(self.custom_cert)
            staging_key.replace(self.custom_key)
            if chain_data:
                staging_chain.replace(self.custom_chain)
            elif self.custom_chain.exists():
                self.custom_chain.unlink()

            # Set permissions
            try:
                os.chmod(self.custom_key, 0o600)
                os.chmod(self.custom_cert, 0o644)
                if chain_data:
                    os.chmod(self.custom_chain, 0o644)
            except OSError:
                pass  # chmod not supported on Windows

            logger.info("Custom certificate saved and validated successfully")

            validation["certificate"] = str(self.custom_cert)
            validation["private_key"] = str(self.custom_key)
            validation["type"] = "custom"
            return validation

        except Exception:
            # Clean up staging files on failure
            for f in (staging_cert, staging_key, staging_chain):
                if f.exists():
                    f.unlink()
            raise

    # ------------------------------------------------------------------ #
    #  DNS-01 Challenge Support
    # ------------------------------------------------------------------ #

    DNS_PROVIDER_PLUGINS = {
        "cloudflare": "dns-cloudflare",
        "route53": "dns-route53",
        "digitalocean": "dns-digitalocean",
        "google": "dns-google",
    }

    def save_dns_credentials(
        self, provider: str, credentials: Dict[str, str]
    ) -> Path:
        """Write DNS provider credentials to a secure file.

        Returns the path to the credentials file.
        """
        self.dns_credentials_dir.mkdir(parents=True, exist_ok=True)

        if provider == "cloudflare":
            creds_path = self.dns_credentials_dir / "cloudflare.ini"
            content = f"dns_cloudflare_api_token = {credentials.get('api_token', '')}\n"
            creds_path.write_text(content)

        elif provider == "route53":
            creds_path = self.dns_credentials_dir / "route53.ini"
            content = (
                "[default]\n"
                f"aws_access_key_id = {credentials.get('access_key_id', '')}\n"
                f"aws_secret_access_key = {credentials.get('secret_access_key', '')}\n"
            )
            creds_path.write_text(content)

        elif provider == "digitalocean":
            creds_path = self.dns_credentials_dir / "digitalocean.ini"
            content = f"dns_digitalocean_token = {credentials.get('api_token', '')}\n"
            creds_path.write_text(content)

        elif provider == "google":
            creds_path = self.dns_credentials_dir / "google.json"
            # credentials should have 'service_account_json' key with raw JSON
            raw_json = credentials.get("service_account_json", "{}")
            # Validate it's actual JSON
            try:
                parsed = json.loads(raw_json)
                creds_path.write_text(json.dumps(parsed, indent=2))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid Google service account JSON: {e}")
        else:
            raise ValueError(f"Unsupported DNS provider: {provider}")

        try:
            os.chmod(creds_path, 0o600)
        except OSError:
            pass

        logger.info(f"DNS credentials for {provider} saved to {creds_path}")
        return creds_path

    def request_letsencrypt_certificate_dns(
        self,
        domain: str,
        email: str,
        provider: str,
        credentials: Dict[str, str],
        staging: bool = False,
    ) -> Dict[str, Any]:
        """Request a Let's Encrypt certificate using DNS-01 challenge.

        Args:
            domain: Domain name for the certificate
            email: Contact email for Let's Encrypt
            provider: DNS provider (cloudflare, route53, digitalocean, google)
            credentials: Provider-specific credentials dict
            staging: Use Let's Encrypt staging server for testing
        """
        # Validate inputs before using in subprocess/paths
        try:
            domain = _validate_domain(domain)
            email = _validate_email(email)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        logger.info(
            f"Requesting Let's Encrypt certificate for {domain} via DNS-01 ({provider})"
        )

        plugin = self.DNS_PROVIDER_PLUGINS.get(provider)
        if not plugin:
            return {"success": False, "error": f"Unsupported DNS provider: {provider}"}

        # Save credentials
        try:
            creds_path = self.save_dns_credentials(provider, credentials)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        # Build certbot command — domain/email already validated above
        cmd = [
            "certbot", "certonly",
            "--non-interactive",
            "--agree-tos",
            "--email", email,
            "-d", domain,
            f"--{plugin}",
            f"--{plugin}-credentials", str(creds_path),
            f"--{plugin}-propagation-seconds", "60",
        ]

        if staging:
            cmd.append("--staging")

        cert_base = Path("/etc/letsencrypt/live") / domain

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            logger.info(f"Certbot DNS output: {result.stdout}")

            if cert_base.exists():
                self._copy_letsencrypt_certs(cert_base)

                # Validate the obtained certificate
                try:
                    self.validate_certificate_files(
                        self.letsencrypt_fullchain, self.letsencrypt_key
                    )
                except ValueError as e:
                    logger.warning(f"Post-issuance validation warning: {e}")

                cert_info = self.get_certificate_info(self.letsencrypt_cert)
                return {
                    "success": True,
                    "certificate": str(self.letsencrypt_fullchain),
                    "private_key": str(self.letsencrypt_key),
                    "type": "letsencrypt",
                    "domain": domain,
                    "expires": cert_info.get("expires"),
                    "staging": staging,
                }
            else:
                raise FileNotFoundError(
                    f"Certificate files not found at {cert_base}"
                )

        except subprocess.CalledProcessError as e:
            logger.error(f"Certbot DNS failed: {e.stderr}")
            return {"success": False, "error": e.stderr, "type": "letsencrypt"}
        except Exception as e:
            logger.error(f"Failed to obtain Let's Encrypt certificate via DNS: {e}")
            return {"success": False, "error": str(e), "type": "letsencrypt"}

    # ------------------------------------------------------------------ #
    #  Self-Signed Certificate
    # ------------------------------------------------------------------ #

    def generate_self_signed_certificate(
        self,
        common_name: str = "localhost",
        organization: str = "ParseDMARC",
        validity_days: int = 365,
        force_regenerate: bool = True,
    ) -> Dict[str, str]:
        """Generate a self-signed certificate.

        IMPORTANT: Each installation should have its own unique certificate.
        Never copy or reuse certificates between installations.
        """
        if self.self_signed_cert.exists() and force_regenerate:
            logger.warning(
                f"Overwriting existing self-signed certificate at {self.self_signed_cert}"
            )

        logger.info(
            f"Generating NEW self-signed certificate for {common_name} "
            "(unique to this installation)"
        )

        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.utcnow())
            .not_valid_after(datetime.utcnow() + timedelta(days=validity_days))
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(common_name),
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]),
                critical=False,
            )
            .sign(private_key, hashes.SHA256(), default_backend())
        )

        with open(self.self_signed_key, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        with open(self.self_signed_cert, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        try:
            os.chmod(self.self_signed_key, 0o600)
            os.chmod(self.self_signed_cert, 0o644)
        except OSError:
            pass

        serial_number = cert.serial_number
        logger.info(
            f"Self-signed certificate generated successfully (serial: {serial_number})"
        )

        # Post-generation validation
        try:
            self.validate_certificate_files(self.self_signed_cert, self.self_signed_key)
        except ValueError as e:
            logger.warning(f"Post-generation validation warning: {e}")

        return {
            "certificate": str(self.self_signed_cert),
            "private_key": str(self.self_signed_key),
            "type": "self-signed",
            "expires": (datetime.utcnow() + timedelta(days=validity_days)).isoformat(),
            "serial_number": serial_number,
            "regenerated": True,
            "warning": (
                "This certificate is unique to this installation. "
                "Never reuse across different systems."
            ),
        }

    # ------------------------------------------------------------------ #
    #  Let's Encrypt HTTP-01
    # ------------------------------------------------------------------ #

    def request_letsencrypt_certificate(
        self,
        domain: str,
        email: str,
        webroot_path: Optional[Path] = None,
        staging: bool = False,
    ) -> Dict[str, Any]:
        """Request a Let's Encrypt certificate using HTTP-01 challenge."""
        # Validate inputs before using in subprocess/paths
        try:
            domain = _validate_domain(domain)
            email = _validate_email(email)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        logger.info(f"Requesting Let's Encrypt certificate for {domain}")

        # Build certbot command — domain/email already validated above
        cmd = [
            "certbot", "certonly",
            "--non-interactive",
            "--agree-tos",
            "--email", email,
            "-d", domain,
        ]

        if staging:
            cmd.append("--staging")

        if webroot_path:
            cmd.extend(["--webroot", "-w", str(webroot_path)])
        else:
            cmd.append("--standalone")

        cert_base = Path("/etc/letsencrypt/live") / domain

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            logger.info(f"Certbot output: {result.stdout}")

            if cert_base.exists():
                self._copy_letsencrypt_certs(cert_base)

                # Post-issuance validation
                try:
                    self.validate_certificate_files(
                        self.letsencrypt_fullchain, self.letsencrypt_key
                    )
                except ValueError as e:
                    logger.warning(f"Post-issuance validation warning: {e}")

                cert_info = self.get_certificate_info(self.letsencrypt_cert)
                logger.info(
                    "Let's Encrypt certificate obtained and copied successfully"
                )
                return {
                    "success": True,
                    "certificate": str(self.letsencrypt_fullchain),
                    "private_key": str(self.letsencrypt_key),
                    "type": "letsencrypt",
                    "domain": domain,
                    "expires": cert_info.get("expires"),
                    "staging": staging,
                }
            else:
                raise FileNotFoundError(
                    f"Certificate files not found at {cert_base}"
                )

        except subprocess.CalledProcessError as e:
            logger.error(f"Certbot failed: {e.stderr}")
            return {"success": False, "error": e.stderr, "type": "letsencrypt"}
        except Exception as e:
            logger.error(f"Failed to obtain Let's Encrypt certificate: {e}")
            return {"success": False, "error": str(e), "type": "letsencrypt"}

    def _copy_letsencrypt_certs(self, cert_base: Path) -> None:
        """Copy certbot output files to the app cert directory."""
        # Verify cert_base is within the expected Let's Encrypt directory
        le_root = Path("/etc/letsencrypt/live")
        resolved_base = cert_base.resolve()
        try:
            resolved_base.relative_to(le_root.resolve())
        except ValueError:
            raise ValueError(
                f"Certificate path {cert_base} is not within {le_root}"
            )

        for src_name, dest in [
            ("privkey.pem", self.letsencrypt_key),
            ("cert.pem", self.letsencrypt_cert),
            ("chain.pem", self.letsencrypt_chain),
            ("fullchain.pem", self.letsencrypt_fullchain),
        ]:
            src = resolved_base / src_name
            if not src.exists():
                raise FileNotFoundError(f"Expected certificate file not found: {src_name}")
            shutil.copy2(src, dest)

        try:
            os.chmod(self.letsencrypt_key, 0o600)
        except OSError:
            pass

    # ------------------------------------------------------------------ #
    #  Renewal (with bug fix — re-copies files after certbot renew)
    # ------------------------------------------------------------------ #

    def renew_letsencrypt_certificate(
        self, domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """Renew Let's Encrypt certificate(s).

        After certbot renew, re-copies the renewed files to the app cert
        directory and validates.
        """
        logger.info(
            f"Renewing Let's Encrypt certificate"
            f"{f' for {domain}' if domain else 's'}"
        )

        # Validate domain before using in subprocess/paths
        if domain:
            domain = _validate_domain(domain)

        cmd = ["certbot", "renew", "--non-interactive"]
        if domain:
            cmd.extend(["--cert-name", domain])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            logger.info(f"Certbot renewal output: {result.stdout}")

            # Re-copy renewed files to app cert directory
            if domain:
                cert_base = Path("/etc/letsencrypt/live") / domain
                if cert_base.exists():
                    self._copy_letsencrypt_certs(cert_base)
                    logger.info(
                        f"Renewed certificate files copied from {cert_base}"
                    )

                    # Validate renewed cert
                    try:
                        self.validate_certificate_files(
                            self.letsencrypt_fullchain, self.letsencrypt_key
                        )
                    except ValueError as e:
                        logger.warning(f"Post-renewal validation warning: {e}")

            return {"success": True, "output": result.stdout}

        except subprocess.CalledProcessError as e:
            logger.error(f"Certbot renewal failed: {e.stderr}")
            return {"success": False, "error": e.stderr}

    # ------------------------------------------------------------------ #
    #  Certificate Info
    # ------------------------------------------------------------------ #

    def get_certificate_info(self, cert_path: Path) -> Dict[str, Any]:
        """Get information about a certificate file."""
        try:
            with open(cert_path, "rb") as f:
                cert_data = f.read()

            cert = x509.load_pem_x509_certificate(cert_data, default_backend())

            return {
                "subject": cert.subject.rfc4514_string(),
                "issuer": cert.issuer.rfc4514_string(),
                "serial_number": cert.serial_number,
                "not_before": cert.not_valid_before.isoformat(),
                "expires": cert.not_valid_after.isoformat(),
                "is_expired": cert.not_valid_after < datetime.utcnow(),
                "days_until_expiry": (
                    cert.not_valid_after - datetime.utcnow()
                ).days,
                "is_self_signed": cert.issuer == cert.subject,
            }
        except Exception as e:
            logger.error(f"Failed to read certificate info: {e}")
            return {"error": str(e)}

    def get_active_certificate(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently active certificate.

        Priority: Let's Encrypt > Custom > Self-signed
        """
        if self.letsencrypt_fullchain.exists():
            info = self.get_certificate_info(self.letsencrypt_cert)
            info["type"] = "letsencrypt"
            info["certificate"] = str(self.letsencrypt_fullchain)
            info["private_key"] = str(self.letsencrypt_key)
            return info
        elif self.custom_cert.exists() and self.custom_key.exists():
            info = self.get_certificate_info(self.custom_cert)
            info["type"] = "custom"
            info["certificate"] = str(self.custom_cert)
            info["private_key"] = str(self.custom_key)
            return info
        elif self.self_signed_cert.exists():
            info = self.get_certificate_info(self.self_signed_cert)
            info["type"] = "self-signed"
            info["certificate"] = str(self.self_signed_cert)
            info["private_key"] = str(self.self_signed_key)
            return info
        else:
            return None

    def setup_auto_renewal(self) -> Dict[str, Any]:
        """Check if automatic certificate renewal is configured."""
        logger.info("Checking automatic certificate renewal setup")

        try:
            result = subprocess.run(
                ["systemctl", "is-enabled", "certbot.timer"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                return {
                    "success": True,
                    "method": "systemd",
                    "message": "Certbot systemd timer is active",
                }
        except FileNotFoundError:
            pass

        try:
            result = subprocess.run(
                ["crontab", "-l"], capture_output=True, text=True
            )
            if "certbot" in result.stdout:
                return {
                    "success": True,
                    "method": "cron",
                    "message": "Certbot cron job found",
                }
        except Exception:
            pass

        return {
            "success": False,
            "message": (
                "No automatic renewal configured. "
                "Please run: sudo certbot renew --dry-run"
            ),
        }
