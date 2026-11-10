
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
from socialflow.modules.accounts.services.facebook_credential_keys import (
    FacebookCredentialKeys,
)
from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)
from socialflow.modules.facebook.api.facebook_graph_client import (
    FacebookGraphClient,
)



class FacebookConnectionVerifier(ConnectionVerifier):
    """Verify access to a configured Facebook Page."""

    def __init__(
        self,
        credential_store: CredentialStore,
        graph_client: FacebookGraphClient,
    ) -> None:
        self._credential_store = credential_store
        self._graph_client = graph_client

    def verify(self, account: Account) -> ConnectionResult:
        if (
            account.destination != PublishingDestination.FACEBOOK
            or account.facebook_config is None
            or not account.facebook_config.is_complete()
        ):
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="Facebook Page configuration is incomplete.",
            )

        page_id = account.facebook_config.page_id.strip()

        try:
            token = self._credential_store.get(
                FacebookCredentialKeys.page_access_token(account)
            )
        except (KeyringError, OSError, RuntimeError):
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="Unable to retrieve Facebook credentials.",
            )

        if not isinstance(token, str) or not token.strip():
            return ConnectionResult(
                status=ConnectionStatus.INVALID_CREDENTIALS,
                message="Facebook Page access token is missing.",
            )

        try:
            response = self._graph_client.get(
                path=page_id,
                access_token=token,
                params={"fields": "id,name"},
            )
        except FacebookApiError as error:
            if error.is_transient:
                return ConnectionResult(
                    status=ConnectionStatus.UNREACHABLE,
                    message="Facebook is temporarily unavailable.",
                )

            if error.status_code in (401, 403) or error.code in (
                10, 190, 200,
            ):
                return ConnectionResult(
                    status=ConnectionStatus.INVALID_CREDENTIALS,
                    message=(
                        "Facebook rejected the Page access "
                        "token or required permissions."
                    ),
                )

            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="Facebook Page verification failed.",
            )
        except ValueError:
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="Invalid Facebook Page configuration.",
            )

        if not isinstance(response, dict):
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="Invalid Facebook Page response.",
            )

        returned_id = response.get("id")

        if not isinstance(returned_id, str) or returned_id != page_id:
            return ConnectionResult(
                status=ConnectionStatus.ERROR,
                message="Facebook returned an unexpected Page ID.",
            )

        return ConnectionResult(
            status=ConnectionStatus.CONNECTED,
            message="Facebook Page connection verified successfully.",
        )
