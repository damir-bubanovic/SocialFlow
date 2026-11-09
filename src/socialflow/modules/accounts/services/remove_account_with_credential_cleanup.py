from uuid import UUID

from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.repositories.account_repository import (
    AccountRepository,
)
from socialflow.modules.accounts.repositories.json_pending_credential_cleanup_repository import (
    JsonPendingCredentialCleanupRepository,
)
from socialflow.modules.accounts.services.credential_errors import (
    CredentialStorageError,
)
from socialflow.modules.accounts.services.errors import (
    AccountCredentialCleanupIncompleteError,
)
from socialflow.modules.accounts.services.facebook_credential_keys import (
    FacebookCredentialKeys,
)
from socialflow.modules.accounts.services.remove_account import (
    RemoveAccount,
)
from socialflow.modules.accounts.services.wordpress_credential_keys import (
    WordPressCredentialKeys,
)


class RemoveAccountWithCredentialCleanup:
    """Remove accounts while retaining recoverable credential cleanup intent."""

    def __init__(
        self,
        remove_account: RemoveAccount,
        account_repository: AccountRepository,
        cleanup_repository: JsonPendingCredentialCleanupRepository,
        credential_store: CredentialStore,
    ) -> None:
        self._remove_account = remove_account
        self._account_repository = account_repository
        self._cleanup_repository = cleanup_repository
        self._credential_store = credential_store

    def execute(self, account: Account) -> None:
        """Remove an account and clean up its stored credentials."""
        key = self._credential_key(account)

        if key is None:
            self._remove_account.execute(account)
            return

        # Verify account existence before recording cleanup intent.
        if account not in self._account_repository.all():
            self._remove_account.execute(account)
            return

        self._cleanup_repository.add(key)
        self._remove_account.execute(account)

        try:
            self._delete_credential(key)
            self._cleanup_repository.remove(key)
        except Exception as exc:
            raise AccountCredentialCleanupIncompleteError(
                "Account removed, but credential cleanup is incomplete."
            ) from exc

    def recover_pending(self) -> None:
        pending = self._cleanup_repository.all()

        for key in pending:
            # Recheck the repository before every deletion.
            accounts = self._account_repository.all()

            account_id = UUID(key.split(":")[1])

            if any(
                    account.id.value == account_id
                    for account in accounts
            ):
                # Account removal did not complete.
                # Preserve credentials and clear stale cleanup intent.
                self._cleanup_repository.remove(key)
                continue

            self._delete_credential(key)
            self._cleanup_repository.remove(key)

    def _delete_credential(self, key: str) -> None:
        try:
            self._credential_store.delete(key)
        except Exception as exc:
            raise CredentialStorageError(
                "Could not securely delete account credentials."
            ) from exc

    @staticmethod
    def _credential_key(account: Account) -> str | None:
        if account.destination == PublishingDestination.FACEBOOK:
            return FacebookCredentialKeys.page_access_token(account)

        if account.destination == PublishingDestination.WORDPRESS:
            return WordPressCredentialKeys.application_password(account)

        return None