from urllib.parse import urlsplit
from urllib.error import URLError

from socialflow.infrastructure.wordpress.wordpress_http_client import (
    WordPressHttpClient,
)
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.application.connections.connection_verifier import (
    ConnectionVerifier,
)
from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.domain.account.account import Account
from socialflow.domain.connections.connection_result import (
    ConnectionResult,
)
from socialflow.domain.connections.connection_status import (
    ConnectionStatus,
)
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)


class WordPressConnectionVerifier(ConnectionVerifier):
    """Verify connections to WordPress websites."""

    def __init__(
            self,
            credential_store: CredentialStore,
            http_client: WordPressHttpClient,
    ) -> None:
        self._credential_store = credential_store
        self._http_client = http_client

    def verify(
            self,
            account: Account,
            config: WordPressConnectionConfig | None = None,
    ) -> ConnectionResult:
        """Validate WordPress settings before HTTP verification."""
        if config is None or not config.is_complete():
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="WordPress connection settings are incomplete.",
            )

        config = config.normalized()
        parsed_url = urlsplit(config.site_url)

        if (
                parsed_url.scheme.lower() != "https"
                or not parsed_url.hostname
                or parsed_url.username is not None
                or parsed_url.password is not None
        ):
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="A valid HTTPS WordPress site URL is required.",
            )

        credential_key = WordPressCredentialKeys.application_password(
            account
        )

        application_password = self._credential_store.get(credential_key)

        if not application_password:
            return ConnectionResult(
                status=ConnectionStatus.INVALID_CREDENTIALS,
                message="WordPress application password is missing.",
            )

        try:
            response = self._http_client.get_authenticated_user(
                site_url=config.site_url,
                username=config.username,
                application_password=application_password,
            )
        except (URLError, TimeoutError, OSError):
            return ConnectionResult(
                status=ConnectionStatus.UNREACHABLE,
                message="Unable to reach the WordPress website.",
            )
        except ValueError:
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="Invalid WordPress connection configuration.",
            )

        if response.status_code == 200:
            return ConnectionResult(
                status=ConnectionStatus.CONNECTED,
                message="WordPress connection verified successfully.",
            )

        if response.status_code in (401, 403):
            return ConnectionResult(
                status=ConnectionStatus.INVALID_CREDENTIALS,
                message="WordPress authentication was rejected.",
            )

        return ConnectionResult(
            status=ConnectionStatus.ERROR,
            message=f"WordPress returned HTTP {response.status_code}.",
        )