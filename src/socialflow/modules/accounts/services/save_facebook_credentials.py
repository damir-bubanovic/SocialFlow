
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


class SaveFacebookCredentials:
    """Save Facebook Page access tokens in secure storage."""

    def __init__(self, credential_store: CredentialStore) -> None:
        self._credential_store = credential_store

    def execute(self, account: Account, access_token: str) -> bool:
        if account.destination != PublishingDestination.FACEBOOK:
            raise ValueError("Account must be a Facebook account.")

        if not access_token.strip():
            return False

        key = FacebookCredentialKeys.page_access_token(account)

        try:
            self._credential_store.save(
                key=key,
                secret=access_token.strip(),
            )
        except Exception as exc:
            raise CredentialStorageError(
                "Could not securely save Facebook credentials."
            ) from exc

        return True
