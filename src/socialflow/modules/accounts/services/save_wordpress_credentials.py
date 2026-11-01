
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
from socialflow.modules.accounts.services.wordpress_credential_keys import (
    WordPressCredentialKeys,
)


class SaveWordPressCredentials:
    """Save WordPress application passwords in secure storage."""

    def __init__(self, credential_store: CredentialStore) -> None:
        self._credential_store = credential_store

    def execute(
        self,
        account: Account,
        application_password: str,
    ) -> bool:
        if account.destination != PublishingDestination.WORDPRESS:
            raise ValueError("Account must be a WordPress account.")

        if not application_password.strip():
            return False

        key = WordPressCredentialKeys.application_password(account)

        try:
            self._credential_store.save(
                key=key,
                secret=application_password,
            )
        except Exception as exc:
            raise CredentialStorageError(
                "Could not securely save WordPress credentials."
            ) from exc

        return True
