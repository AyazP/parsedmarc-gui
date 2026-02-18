"""Setup wizard schemas."""
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class EncryptionKeySetup(BaseModel):
    """Schema for encryption key setup.

    If encryption_key is not provided, a new one will be auto-generated.
    Each installation should use a unique encryption key.
    """
    encryption_key: Optional[str] = Field(
        None,
        min_length=32,
        description="Fernet encryption key (base64 encoded). If omitted, a new key will be auto-generated."
    )

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate that the encryption key is valid Fernet key if provided."""
        if v is None:
            return v  # Will be auto-generated

        from cryptography.fernet import Fernet
        try:
            # Test if it's a valid Fernet key
            Fernet(v.encode())
            return v
        except Exception:
            raise ValueError("Invalid encryption key format. Use Fernet.generate_key() to generate a valid key.")


class AdminCredentialsSetup(BaseModel):
    """Schema for admin credentials setup."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate that passwords match."""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class SSLSetupSelfSigned(BaseModel):
    """Schema for self-signed SSL certificate setup."""
    type: Literal["self-signed"] = "self-signed"
    common_name: str = Field(default="localhost", description="Common name (hostname/domain)")
    organization: str = Field(default="ParseDMARC", description="Organization name")
    validity_days: int = Field(default=365, ge=1, le=3650, description="Certificate validity in days")


class SSLSetupLetsEncrypt(BaseModel):
    """Schema for Let's Encrypt SSL certificate setup."""
    type: Literal["letsencrypt"] = "letsencrypt"
    domain: str = Field(..., description="Domain name for the certificate")
    email: str = Field(..., description="Contact email for Let's Encrypt")
    staging: bool = Field(default=False, description="Use staging server for testing")

    # Challenge type
    challenge_type: Literal["http-01", "dns-01"] = Field(
        default="http-01", description="ACME challenge type"
    )
    webroot_path: Optional[str] = Field(None, description="Webroot path for HTTP-01")

    # DNS-01 fields
    dns_provider: Optional[Literal["cloudflare", "route53", "digitalocean", "google"]] = Field(
        None, description="DNS provider for DNS-01 challenge"
    )
    dns_credentials: Optional[Dict[str, str]] = Field(
        None, description="DNS provider API credentials"
    )

    @field_validator("dns_provider")
    @classmethod
    def validate_dns_provider(cls, v, info):
        if info.data.get("challenge_type") == "dns-01" and not v:
            raise ValueError("DNS provider is required for DNS-01 challenge")
        return v

    @field_validator("dns_credentials")
    @classmethod
    def validate_dns_credentials(cls, v, info):
        if info.data.get("challenge_type") == "dns-01" and not v:
            raise ValueError("DNS credentials are required for DNS-01 challenge")
        return v


class SSLSetupCustom(BaseModel):
    """Schema for custom SSL certificate setup."""
    type: Literal["custom"] = "custom"
    certificate_path: str = Field(..., description="Path to certificate file")
    private_key_path: str = Field(..., description="Path to private key file")
    chain_path: Optional[str] = Field(None, description="Path to certificate chain file")


class ServerSetup(BaseModel):
    """Schema for server configuration setup."""
    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Comma-separated list of allowed CORS origins"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level"
    )


class DatabaseSetup(BaseModel):
    """Schema for database configuration setup."""
    db_type: Literal["sqlite", "postgresql", "mysql"] = Field(
        default="sqlite", description="Database engine type"
    )
    db_path: str = Field(default="./data/parsedmarc.db", description="SQLite database file path")
    db_host: Optional[str] = Field(None, description="Database host (PostgreSQL/MySQL)")
    db_port: Optional[int] = Field(None, ge=1, le=65535, description="Database port")
    db_name: Optional[str] = Field(None, description="Database name (PostgreSQL/MySQL)")
    db_user: Optional[str] = Field(None, description="Database username")
    db_password: Optional[str] = Field(None, description="Database password")

    @model_validator(mode="after")
    def validate_connection_fields(self):
        if self.db_type != "sqlite":
            errors = []
            if not self.db_host:
                errors.append("Host is required for PostgreSQL/MySQL")
            if not self.db_name:
                errors.append("Database name is required for PostgreSQL/MySQL")
            if not self.db_user:
                errors.append("Username is required for PostgreSQL/MySQL")
            if errors:
                raise ValueError("; ".join(errors))
        return self


class CompleteSetup(BaseModel):
    """Schema for completing the entire setup."""
    encryption_key: Optional[str] = Field(
        None,
        description="Encryption key for credentials. If omitted, a new unique key will be auto-generated."
    )
    admin_username: str = Field(..., min_length=3)
    admin_password: str = Field(..., min_length=8)
    ssl_type: Literal["self-signed", "letsencrypt", "custom", "skip"] = Field(..., description="SSL certificate type")

    # SSL-specific fields (conditionally required)
    ssl_domain: Optional[str] = Field(None, description="Domain for Let's Encrypt or custom cert")
    ssl_email: Optional[str] = Field(None, description="Email for Let's Encrypt")
    ssl_staging: bool = Field(default=False, description="Use Let's Encrypt staging")
    ssl_common_name: Optional[str] = Field(None, description="Common name for self-signed cert")
    ssl_certificate_path: Optional[str] = Field(None, description="Path to custom certificate")
    ssl_private_key_path: Optional[str] = Field(None, description="Path to custom private key")

    # DNS-01 challenge fields
    ssl_challenge_type: Literal["http-01", "dns-01"] = Field(
        default="http-01", description="ACME challenge type"
    )
    ssl_dns_provider: Optional[str] = Field(None, description="DNS provider for DNS-01")
    ssl_dns_credentials: Optional[Dict[str, str]] = Field(None, description="DNS provider credentials")

    # Server configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8000")
    log_level: str = Field(default="INFO")

    # Database configuration
    db_type: Literal["sqlite", "postgresql", "mysql"] = Field(
        default="sqlite", description="Database engine type"
    )
    db_path: str = Field(default="./data/parsedmarc.db")
    db_host: Optional[str] = Field(None, description="Database host")
    db_port: Optional[int] = Field(None, ge=1, le=65535, description="Database port")
    db_name: Optional[str] = Field(None, description="Database name")
    db_user: Optional[str] = Field(None, description="Database username")
    db_password: Optional[str] = Field(None, description="Database password")

    @field_validator("ssl_domain")
    @classmethod
    def validate_letsencrypt_domain(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that domain is provided for Let's Encrypt."""
        if info.data.get("ssl_type") == "letsencrypt" and not v:
            raise ValueError("Domain is required for Let's Encrypt certificates")
        return v

    @field_validator("ssl_email")
    @classmethod
    def validate_letsencrypt_email(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that email is provided for Let's Encrypt."""
        if info.data.get("ssl_type") == "letsencrypt" and not v:
            raise ValueError("Email is required for Let's Encrypt certificates")
        return v


class SetupStatusResponse(BaseModel):
    """Schema for setup status response."""
    is_complete: bool
    setup_version: str
    encryption_key_set: bool
    admin_credentials_set: bool
    ssl_configured: bool
    database_configured: bool
    server_configured: bool
    ssl_type: Optional[str] = None
    ssl_domain: Optional[str] = None
    completed_at: Optional[datetime] = None
    needs_setup: bool

    class Config:
        from_attributes = True


class CertificateInfo(BaseModel):
    """Schema for certificate information."""
    type: str
    certificate: Optional[str] = None
    private_key: Optional[str] = None
    subject: Optional[str] = None
    issuer: Optional[str] = None
    expires: Optional[str] = None
    is_expired: Optional[bool] = None
    days_until_expiry: Optional[int] = None
    is_self_signed: Optional[bool] = None
    error: Optional[str] = None


class CertificateValidationResult(BaseModel):
    """Schema for certificate validation results."""
    valid: bool
    error: Optional[str] = None
    warning: Optional[str] = None
    subject: Optional[str] = None
    issuer: Optional[str] = None
    expires: Optional[str] = None
    days_until_expiry: Optional[int] = None
    is_self_signed: Optional[bool] = None


class SetupStepResponse(BaseModel):
    """Schema for individual setup step response."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[Dict[str, str]] = None
