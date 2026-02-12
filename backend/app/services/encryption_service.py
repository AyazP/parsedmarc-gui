"""Encryption service for securing credentials."""
import json
import logging
from typing import Dict, Any
from cryptography.fernet import Fernet, InvalidToken
from app.config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    def __init__(self):
        """Initialize the encryption service with the encryption key."""
        try:
            # Validate and load encryption key
            key = settings.encryption_key
            if not key or key == "CHANGE_ME_GENERATE_NEW_KEY":
                raise ValueError(
                    "PARSEDMARC_ENCRYPTION_KEY must be set! "
                    "Generate a key with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
                )

            self.cipher = Fernet(key.encode())
            logger.info("Encryption service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {e}")
            raise

    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """
        Encrypt a dictionary to a string.

        Args:
            data: Dictionary to encrypt

        Returns:
            Encrypted string (base64-encoded)
        """
        try:
            json_str = json.dumps(data)
            encrypted_bytes = self.cipher.encrypt(json_str.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt_dict(self, encrypted_str: str) -> Dict[str, Any]:
        """
        Decrypt a string back to a dictionary.

        Args:
            encrypted_str: Encrypted string (base64-encoded)

        Returns:
            Decrypted dictionary

        Raises:
            InvalidToken: If decryption fails
        """
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_str.encode())
            json_str = decrypted_bytes.decode()
            return json.loads(json_str)
        except InvalidToken:
            logger.error("Invalid encryption token - data may be corrupted or key changed")
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def encrypt_string(self, value: str) -> str:
        """
        Encrypt a single string value.

        Args:
            value: String to encrypt

        Returns:
            Encrypted string (base64-encoded)
        """
        try:
            encrypted_bytes = self.cipher.encrypt(value.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"String encryption failed: {e}")
            raise

    def decrypt_string(self, encrypted_value: str) -> str:
        """
        Decrypt a single string value.

        Args:
            encrypted_value: Encrypted string (base64-encoded)

        Returns:
            Decrypted string

        Raises:
            InvalidToken: If decryption fails
        """
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_value.encode())
            return decrypted_bytes.decode()
        except InvalidToken:
            logger.error("Invalid encryption token - data may be corrupted or key changed")
            raise
        except Exception as e:
            logger.error(f"String decryption failed: {e}")
            raise

    def is_encrypted(self, value: str) -> bool:
        """
        Check if a string appears to be encrypted.

        Args:
            value: String to check

        Returns:
            True if the string can be successfully decrypted
        """
        try:
            self.cipher.decrypt(value.encode())
            return True
        except Exception:
            return False


# Global encryption service instance
encryption_service = EncryptionService()
