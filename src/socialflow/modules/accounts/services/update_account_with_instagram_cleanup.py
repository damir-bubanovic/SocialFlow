
from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.repositories.account_repository import (
    AccountRepository,
)
from socialflow.modules.accounts.repositories.errors import (
    AccountStorageError,
)
from socialflow.modules.accounts.repositories.json_pending_credential_cleanup_repository import (
    JsonPendingCredentialCleanupRepository,
)
from socialflow.modules.accounts.services.credential_errors import (
    CredentialStorageError,
)
from socialflow.modules.accounts.services.instagram_credential_keys import (
    InstagramCredentialKeys,
)
from socialflow.modules.accounts.services.update_account import (
    UpdateAccount,
)


class InstagramConversionCleanupIncompleteError(CredentialStorageError):
    """Account update succeeded, but old Instagram token cleanup failed."""


class UpdateAccountWithInstagramCleanup:
    """Update accounts with crash-recoverable Instagram token cleanup."""

    def __init__(
        self,
        update_account: UpdateAccount,
        cleanup_repository: JsonPendingCredentialCleanupRepository,
        credential_store: CredentialStore,
        account_repository: AccountRepository,
    ) -> None:
        self._update_account = update_account
        self._cleanup_repository = cleanup_repository
        self._credential_store = credential_store
        self._account_repository = account_repository

    def execute(self, current: Account, updated: Account) -> None:
        converting = (
            current.destination == PublishingDestination.INSTAGRAM
            and updated.destination != PublishingDestination.INSTAGRAM
        )

        if not converting:
            self._update_account.execute(current, updated)
            return

        key = InstagramCredentialKeys.access_token(current)

        # Persist intent before changing account metadata.
        # A failed journal write must prevent the account update.
        self._cleanup_repository.add(key)

        try:
            self._update_account.execute(current, updated)
        except Exception:
            # The update may have failed before or after persisting
            # account metadata. Verify the stored state before deciding
            # whether the cleanup journal is still needed.
            try:
                accounts = self._account_repository.all()

                instagram_account_still_exists = any(
                    account.id == current.id
                    and account.destination == PublishingDestination.INSTAGRAM
                    for account in accounts
                )

                if instagram_account_still_exists:
                    # No obsolete Instagram credential needs deletion.
                    self._cleanup_repository.remove(key)
            except (OSError, AccountStorageError, ValueError):
                # Preserve the original update failure. If account-state
                # verification or journal removal fails, startup recovery
                # can resolve the remaining cleanup intent.
                pass

            # Preserve the original account update failure.
            raise

        # The account now uses another platform. Retain the journal
        # until both credential deletion and journal clearing succeed.
        try:
            self._credential_store.delete(key)
            self._cleanup_repository.remove(key)
        except Exception as exc:
            raise InstagramConversionCleanupIncompleteError(
                "Account updated, but Instagram credential cleanup is incomplete."
            ) from exc
