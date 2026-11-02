
from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.services.credential_errors import (
    CredentialStorageError,
)
from socialflow.modules.accounts.services.facebook_credential_keys import (
    FacebookCredentialKeys,
)


class DeleteFacebookCredentials:
    """Delete a Facebook Page access token from secure storage."""

    def __init__(self, credential_store: CredentialStore) -> None:
        self._credential_store = credential_store

    def execute(self, account: Account) -> None:
        if account.destination != PublishingDestination.FACEBOOK:
            raise ValueError("Account must be a Facebook account.")

        key = FacebookCredentialKeys.page_access_token(account)

        try:
            self._credential_store.delete(key)
        except Exception as exc:
            raise CredentialStorageError(
                "Could not securely delete Facebook credentials."
            ) from exc
