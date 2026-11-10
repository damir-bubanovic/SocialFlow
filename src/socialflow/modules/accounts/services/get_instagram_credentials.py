from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.services.credential_errors import (
    CredentialStorageError,
)
from socialflow.modules.accounts.services.instagram_credential_keys import (
    InstagramCredentialKeys,
)


class GetInstagramCredentials:
    """Retrieve an Instagram access token from secure storage."""

    def __init__(self, credential_store: CredentialStore) -> None:
        self._credential_store = credential_store

    def execute(self, account: Account) -> str | None:
        if account.destination != PublishingDestination.INSTAGRAM:
            raise ValueError("Account must be an Instagram account.")

        key = InstagramCredentialKeys.access_token(account)

        try:
            return self._credential_store.get(key)
        except Exception as exc:
            raise CredentialStorageError(
                "Could not securely retrieve Instagram credentials."
            ) from exc