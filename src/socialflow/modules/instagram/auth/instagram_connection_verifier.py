from keyring.errors import KeyringError

from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.connection_result import (
    ConnectionResult,
)
from socialflow.modules.accounts.models.connection_status import (
    ConnectionStatus,
)
from socialflow.modules.accounts.services.connection_verifier import (
    ConnectionVerifier,
)
from socialflow.modules.accounts.services.instagram_credential_keys import (
    InstagramCredentialKeys,
)
from socialflow.modules.instagram.api.instagram_api_error import (
    InstagramApiError,
)
from socialflow.modules.instagram.api.instagram_graph_client import (
    InstagramGraphClient,
)


class InstagramConnectionVerifier(ConnectionVerifier):
    """Verify access to a configured Instagram account."""

    def __init__(
        self,
        credential_store: CredentialStore,
        graph_client: InstagramGraphClient,
    ) -> None:
        self._credential_store = credential_store
        self._graph_client = graph_client

    def verify(self, account: Account) -> ConnectionResult:
        if (
            account.destination != PublishingDestination.INSTAGRAM
            or account.instagram_config is None
            or not account.instagram_config.is_complete()
        ):
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="Instagram account configuration is incomplete.",
            )

        instagram_user_id = (
            account.instagram_config.instagram_user_id.strip()
        )

        try:
            token = self._credential_store.get(
                InstagramCredentialKeys.access_token(account)
            )
        except (KeyringError, OSError, RuntimeError):
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="Unable to retrieve Instagram credentials.",
            )

        if not isinstance(token, str) or not token.strip():
            return ConnectionResult(
                status=ConnectionStatus.INVALID_CREDENTIALS,
                message="Instagram access token is missing.",
            )

        try:
            response = self._graph_client.get(
                path=instagram_user_id,
                access_token=token.strip(),
                params={"fields": "id,username"},
            )
        except InstagramApiError as error:
            if error.is_transient:
                return ConnectionResult(
                    status=ConnectionStatus.UNREACHABLE,
                    message="Instagram is temporarily unavailable.",
                )

            if error.status_code in (401, 403) or error.code in (
                10, 190, 200,
            ):
                return ConnectionResult(
                    status=ConnectionStatus.INVALID_CREDENTIALS,
                    message=(
                        "Instagram rejected the access token "
                        "or required permissions."
                    ),
                )

            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="Instagram account verification failed.",
            )
        except ValueError:
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="Invalid Instagram account configuration.",
            )

        if not isinstance(response, dict):
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="Invalid Instagram account response.",
            )

        returned_id = response.get("id")

        if (
            not isinstance(returned_id, str)
            or returned_id != instagram_user_id
        ):
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="Instagram returned an unexpected account ID.",
            )

        return ConnectionResult(
            status=ConnectionStatus.CONNECTED,
            message="Instagram account connection verified successfully.",
        )