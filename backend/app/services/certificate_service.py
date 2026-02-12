"""SSL/TLS certificate management service."""
import os
import subprocess
import ipaddress
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


class CertificateService:
    """Service for managing SSL/TLS certificates."""

    def __init__(self, cert_dir: Path):
        """Initialize certificate service.

        Args:
            cert_dir: Directory to store certificates
        """
        self.cert_dir = cert_dir
        self.cert_dir.mkdir(parents=True, exist_ok=True)

        # Certificate file paths
        self.self_signed_key = self.cert_dir / "selfsigned.key"
        self.self_signed_cert = self.cert_dir / "selfsigned.crt"
        self.letsencrypt_key = self.cert_dir / "letsencrypt.key"
        self.letsencrypt_cert = self.cert_dir / "letsencrypt.crt"
        self.letsencrypt_chain = self.cert_dir / "letsencrypt-chain.crt"
        self.letsencrypt_fullchain = self.cert_dir / "letsencrypt-fullchain.crt"

    def generate_self_signed_certificate(
        self,
        common_name: str = "localhost",
        organization: str = "ParseDMARC",
        validity_days: int = 365,
        force_regenerate: bool = True
    ) -> Dict[str, str]:
        """Generate a self-signed certificate.

        IMPORTANT: Each installation should have its own unique certificate.
        Never copy or reuse certificates between installations.

        This method generates a fresh RSA key pair and certificate each time
        it's called, ensuring cryptographic uniqueness.

        Args:
            common_name: Common name for the certificate (usually hostname/domain)
            organization: Organization name
            validity_days: Certificate validity in days
            force_regenerate: Always generate new cert even if one exists (default: True)

        Returns:
            Dictionary with certificate and key file paths
        """
        # Warn if overwriting existing certificate
        if self.self_signed_cert.exists() and force_regenerate:
            logger.warning(f"Overwriting existing self-signed certificate at {self.self_signed_cert}")

        logger.info(f"Generating NEW self-signed certificate for {common_name} (unique to this installation)")

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=validity_days)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(common_name),
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256(), default_backend())

        # Write private key
        with open(self.self_signed_key, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        # Write certificate
        with open(self.self_signed_cert, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        # Set restrictive permissions
        os.chmod(self.self_signed_key, 0o600)
        os.chmod(self.self_signed_cert, 0o644)

        # Get certificate serial number (unique identifier)
        serial_number = cert.serial_number

        logger.info(f"Self-signed certificate generated successfully (serial: {serial_number})")

        return {
            "certificate": str(self.self_signed_cert),
            "private_key": str(self.self_signed_key),
            "type": "self-signed",
            "expires": (datetime.utcnow() + timedelta(days=validity_days)).isoformat(),
            "serial_number": serial_number,
            "regenerated": True,
            "warning": "This certificate is unique to this installation. Never reuse across different systems."
        }

    def request_letsencrypt_certificate(
        self,
        domain: str,
        email: str,
        webroot_path: Optional[Path] = None,
        staging: bool = False
    ) -> Dict[str, Any]:
        """Request a Let's Encrypt certificate using certbot.

        Args:
            domain: Domain name for the certificate
            email: Contact email for Let's Encrypt
            webroot_path: Path for webroot authentication (if None, uses standalone)
            staging: Use Let's Encrypt staging server for testing

        Returns:
            Dictionary with certificate information and status
        """
        logger.info(f"Requesting Let's Encrypt certificate for {domain}")

        # Build certbot command
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

        # Certbot will store certs in /etc/letsencrypt/live/{domain}/
        # We'll need to copy them to our cert directory
        cert_base = Path(f"/etc/letsencrypt/live/{domain}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"Certbot output: {result.stdout}")

            # Copy certificates to our directory
            if cert_base.exists():
                import shutil

                # Copy private key
                shutil.copy2(
                    cert_base / "privkey.pem",
                    self.letsencrypt_key
                )
                os.chmod(self.letsencrypt_key, 0o600)

                # Copy certificate
                shutil.copy2(
                    cert_base / "cert.pem",
                    self.letsencrypt_cert
                )

                # Copy chain
                shutil.copy2(
                    cert_base / "chain.pem",
                    self.letsencrypt_chain
                )

                # Copy fullchain
                shutil.copy2(
                    cert_base / "fullchain.pem",
                    self.letsencrypt_fullchain
                )

                # Get certificate expiry
                cert_info = self.get_certificate_info(self.letsencrypt_cert)

                logger.info("Let's Encrypt certificate obtained and copied successfully")

                return {
                    "success": True,
                    "certificate": str(self.letsencrypt_fullchain),
                    "private_key": str(self.letsencrypt_key),
                    "type": "letsencrypt",
                    "domain": domain,
                    "expires": cert_info.get("expires"),
                    "staging": staging
                }
            else:
                raise FileNotFoundError(f"Certificate files not found at {cert_base}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Certbot failed: {e.stderr}")
            return {
                "success": False,
                "error": e.stderr,
                "type": "letsencrypt"
            }
        except Exception as e:
            logger.error(f"Failed to obtain Let's Encrypt certificate: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "letsencrypt"
            }

    def renew_letsencrypt_certificate(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Renew Let's Encrypt certificate(s).

        Args:
            domain: Specific domain to renew (if None, renews all)

        Returns:
            Dictionary with renewal status
        """
        logger.info(f"Renewing Let's Encrypt certificate{f' for {domain}' if domain else 's'}")

        cmd = ["certbot", "renew", "--non-interactive"]

        if domain:
            cmd.extend(["--cert-name", domain])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"Certbot renewal output: {result.stdout}")

            return {
                "success": True,
                "output": result.stdout
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"Certbot renewal failed: {e.stderr}")
            return {
                "success": False,
                "error": e.stderr
            }

    def get_certificate_info(self, cert_path: Path) -> Dict[str, Any]:
        """Get information about a certificate.

        Args:
            cert_path: Path to certificate file

        Returns:
            Dictionary with certificate information
        """
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
                "days_until_expiry": (cert.not_valid_after - datetime.utcnow()).days,
                "is_self_signed": cert.issuer == cert.subject
            }

        except Exception as e:
            logger.error(f"Failed to read certificate info: {e}")
            return {"error": str(e)}

    def get_active_certificate(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently active certificate.

        Returns:
            Dictionary with active certificate info, or None if no certificate exists
        """
        # Prefer Let's Encrypt over self-signed
        if self.letsencrypt_fullchain.exists():
            info = self.get_certificate_info(self.letsencrypt_cert)
            info["type"] = "letsencrypt"
            info["certificate"] = str(self.letsencrypt_fullchain)
            info["private_key"] = str(self.letsencrypt_key)
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
        """Setup automatic certificate renewal via cron/systemd timer.

        Returns:
            Dictionary with setup status
        """
        logger.info("Setting up automatic certificate renewal")

        # Certbot typically installs its own renewal timer/cron job
        # We just need to verify it's set up

        try:
            # Check if certbot timer is active (systemd)
            result = subprocess.run(
                ["systemctl", "is-enabled", "certbot.timer"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "method": "systemd",
                    "message": "Certbot systemd timer is active"
                }

        except FileNotFoundError:
            pass  # systemctl not available

        # Check for cron job
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True
            )

            if "certbot" in result.stdout:
                return {
                    "success": True,
                    "method": "cron",
                    "message": "Certbot cron job found"
                }

        except Exception:
            pass

        # If no auto-renewal found, suggest manual setup
        return {
            "success": False,
            "message": "No automatic renewal configured. Please run: sudo certbot renew --dry-run"
        }
