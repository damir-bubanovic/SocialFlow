
from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.modules.accounts.services.credential_errors import (
    CredentialStorageError,
)
from socialflow.modules.accounts.models.account import Account
from socialflow.core.destination import (
    PublishingDestination,
)
from socialflow.modules.wordpress.auth.wordpress_credential_keys import (
    WordPressCredentialKeys,
)


class DeleteWordPressCredentials:
    """Delete a WordPress application password from secure storage."""

    def __init__(self, credential_store: CredentialStore) -> None:
        self._credential_store = credential_store

    def execute(self, account: Account) -> None:
        if account.destination != PublishingDestination.WORDPRESS:
            raise ValueError("Account must be a WordPress account.")

        key = WordPressCredentialKeys.application_password(account)

        try:
            self._credential_store.delete(key)
        except Exception as exc:
            raise CredentialStorageError(
                "Could not securely delete WordPress credentials."
            ) from exc
