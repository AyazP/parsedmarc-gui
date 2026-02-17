"""Mailbox connection factory service."""
import logging
from pathlib import Path
from typing import Dict, Any

from app.models.mailbox_config import MailboxConfig
from app.services.encryption_service import encryption_service
from app.config import settings

logger = logging.getLogger(__name__)


class MailboxService:
    """Factory for creating parsedmarc MailboxConnection instances from DB configs."""

    def create_connection(self, config: MailboxConfig) -> "MailboxConnection":
        """
        Create a MailboxConnection from a MailboxConfig database record.

        Decrypts stored encrypted settings and maps GUI schema fields
        to parsedmarc constructor parameters.

        Args:
            config: A MailboxConfig SQLAlchemy model instance.

        Returns:
            A MailboxConnection subclass instance.

        Raises:
            ValueError: If config type is unsupported or settings are missing.
        """
        type_to_method = {
            "imap": self._create_imap_connection,
            "msgraph": self._create_msgraph_connection,
            "gmail": self._create_gmail_connection,
            "maildir": self._create_maildir_connection,
        }

        if config.type not in type_to_method:
            raise ValueError(f"Unsupported mailbox type: {config.type}")

        # Get the encrypted settings column for this type
        encrypted_settings = getattr(config, f"{config.type}_settings", None)
        if not encrypted_settings:
            raise ValueError(
                f"No {config.type} settings found for config '{config.name}' (id={config.id})"
            )

        # Decrypt settings
        settings_dict = encryption_service.decrypt_dict(encrypted_settings)
        logger.info(f"Creating {config.type} connection for '{config.name}' (id={config.id})")

        if config.type == "gmail":
            return self._create_gmail_connection(settings_dict, config)
        else:
            return type_to_method[config.type](settings_dict)

    def _create_imap_connection(self, settings_dict: Dict[str, Any]):
        """Decrypt IMAP settings and create IMAPConnection."""
        from parsedmarc.mail import IMAPConnection
        return IMAPConnection(
            host=settings_dict["host"],
            user=settings_dict["username"],
            password=settings_dict["password"],
            port=settings_dict.get("port", 993),
            ssl=settings_dict.get("ssl", True),
            verify=not settings_dict.get("skip_certificate_verification", False),
        )

    def _create_msgraph_connection(
        self, settings_dict: Dict[str, Any]
    ):
        """Decrypt MSGraph settings and create MSGraphConnection."""
        from parsedmarc.mail import MSGraphConnection
        token_file = settings_dict.get("token_file")
        if not token_file:
            token_file = self._resolve_token_path(
                "msgraph", settings_dict.get("mailbox", "default"), "token.json"
            )

        if settings_dict.get("auth_method") == "DeviceCode":
            logger.warning(
                "MSGraph DeviceCode auth requires interactive login. "
                "For web GUI, ClientSecret is recommended. "
                "DeviceCode will work only if a cached token exists."
            )

        return MSGraphConnection(
            auth_method=settings_dict.get("auth_method", "ClientSecret"),
            mailbox=settings_dict["mailbox"],
            graph_url=settings_dict.get("graph_url", "https://graph.microsoft.com"),
            client_id=settings_dict["client_id"],
            client_secret=settings_dict.get("client_secret", ""),
            username=settings_dict.get("username", ""),
            password=settings_dict.get("password", ""),
            tenant_id=settings_dict["tenant_id"],
            token_file=token_file,
            allow_unencrypted_storage=True,
        )

    def _create_gmail_connection(
        self, settings_dict: Dict[str, Any], config: MailboxConfig
    ):
        """Decrypt Gmail settings and create GmailConnection."""
        from parsedmarc.mail import GmailConnection
        token_file = settings_dict.get("token_file")
        if not token_file:
            token_file = self._resolve_token_path(
                "gmail", str(config.id), "token.json"
            )

        return GmailConnection(
            token_file=token_file,
            credentials_file=settings_dict["credentials_file"],
            scopes=settings_dict.get(
                "scopes", ["https://www.googleapis.com/auth/gmail.modify"]
            ),
            include_spam_trash=settings_dict.get("include_spam_trash", False),
            reports_folder=config.reports_folder or "INBOX",
            oauth2_port=8080,
            paginate_messages=True,
        )

    def _create_maildir_connection(
        self, settings_dict: Dict[str, Any]
    ):
        """Decrypt Maildir settings and create MaildirConnection."""
        from parsedmarc.mail import MaildirConnection
        return MaildirConnection(
            maildir_path=settings_dict["path"],
            maildir_create=False,
        )

    def test_connection(self, config: MailboxConfig) -> dict:
        """
        Test that a mailbox connection can be established and the
        reports folder is accessible.

        Returns:
            dict with keys: success (bool), message (str), details (optional dict)
        """
        try:
            connection = self.create_connection(config)
            reports_folder = config.reports_folder or "INBOX"
            messages = connection.fetch_messages(reports_folder, batch_size=1)
            msg_count = len(messages) if messages else 0
            logger.info(
                f"Connection test succeeded for '{config.name}': "
                f"{msg_count} message(s) in '{reports_folder}'"
            )
            return {
                "success": True,
                "message": (
                    f"Connected successfully. "
                    f"Found {msg_count} message(s) in '{reports_folder}'."
                ),
                "details": {"message_count": msg_count, "folder": reports_folder},
            }
        except Exception as e:
            logger.error(
                f"Connection test failed for '{config.name}' (id={config.id}): {e}"
            )
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "details": {"error_type": type(e).__name__},
            }

    def _resolve_token_path(
        self, config_type: str, config_id: str, filename: str
    ) -> str:
        """
        Resolve a token file path under data_dir/tokens/{config_type}_{config_id}/.
        Creates the directory if it does not exist.
        """
        token_dir = Path(settings.data_dir) / "tokens" / f"{config_type}_{config_id}"
        token_dir.mkdir(parents=True, exist_ok=True)
        return str(token_dir / filename)


# Module-level singleton
mailbox_service = MailboxService()
