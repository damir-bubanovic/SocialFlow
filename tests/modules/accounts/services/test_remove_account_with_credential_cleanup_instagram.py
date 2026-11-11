
import pytest

from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.repositories.in_memory_account_repository import (
    InMemoryAccountRepository,
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
from socialflow.modules.accounts.services.instagram_credential_keys import (
    InstagramCredentialKeys,
)
from socialflow.modules.accounts.services.remove_account import RemoveAccount
from socialflow.modules.accounts.services.remove_account_with_credential_cleanup import (
    RemoveAccountWithCredentialCleanup,
)


class FakeCredentialStore(CredentialStore):
    def __init__(self) -> None:
        self.secrets: dict[str, str] = {}
        self.fail_delete = False

    def save(self, key: str, secret: str) -> None:
        self.secrets[key] = secret

    def get(self, key: str) -> str | None:
        return self.secrets.get(key)

    def delete(self, key: str) -> None:
        if self.fail_delete:
            raise OSError("Simulated credential deletion failure")
        self.secrets.pop(key, None)


def setup_cleanup(tmp_path, *, account_exists=True):
    repository = InMemoryAccountRepository()
    account = Account(
        name="Instagram Account",
        destination=PublishingDestination.INSTAGRAM,
    )

    if account_exists:
        repository.add(account)

    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )
    store = FakeCredentialStore()

    key = InstagramCredentialKeys.access_token(account)
    store.save(key, "secret-instagram-token")

    coordinator = RemoveAccountWithCredentialCleanup(
        remove_account=RemoveAccount(repository),
        account_repository=repository,
        cleanup_repository=journal,
        credential_store=store,
    )

    return coordinator, repository, journal, store, account, key


def test_instagram_removal_deletes_token_and_clears_journal(
    tmp_path,
) -> None:
    coordinator, repository, journal, store, account, key = (
        setup_cleanup(tmp_path)
    )

    coordinator.execute(account)

    assert repository.all() == ()
    assert key not in store.secrets
    assert journal.all() == ()


def test_instagram_deletion_failure_retains_recovery_intent(
    tmp_path,
) -> None:
    coordinator, repository, journal, store, account, key = (
        setup_cleanup(tmp_path)
    )
    store.fail_delete = True

    with pytest.raises(
        AccountCredentialCleanupIncompleteError
    ) as exc_info:
        coordinator.execute(account)

    assert isinstance(exc_info.value.__cause__, CredentialStorageError)
    assert repository.all() == ()
    assert store.secrets[key] == "secret-instagram-token"
    assert journal.all() == (key,)


def test_instagram_recovery_deletes_orphaned_token(
    tmp_path,
) -> None:
    coordinator, repository, journal, store, account, key = (
        setup_cleanup(tmp_path, account_exists=False)
    )
    journal.add(key)

    coordinator.recover_pending()

    assert repository.all() == ()
    assert key not in store.secrets
    assert journal.all() == ()

    coordinator.recover_pending()
    assert journal.all() == ()


def test_instagram_recovery_preserves_token_for_existing_account(
    tmp_path,
) -> None:
    coordinator, repository, journal, store, account, key = (
        setup_cleanup(tmp_path)
    )
    journal.add(key)

    coordinator.recover_pending()

    assert repository.all() == (account,)
    assert store.secrets[key] == "secret-instagram-token"
    assert journal.all() == ()


def test_instagram_failed_recovery_can_be_retried(
    tmp_path,
) -> None:
    coordinator, repository, journal, store, account, key = (
        setup_cleanup(tmp_path, account_exists=False)
    )
    journal.add(key)
    store.fail_delete = True

    with pytest.raises(CredentialStorageError):
        coordinator.recover_pending()

    assert store.secrets[key] == "secret-instagram-token"
    assert journal.all() == (key,)

    store.fail_delete = False
    coordinator.recover_pending()

    assert key not in store.secrets
    assert journal.all() == ()


def test_recovery_deletes_instagram_token_after_platform_conversion(
    tmp_path,
) -> None:
    repository = InMemoryAccountRepository()

    account = Account(
        name="Converted Account",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(account)

    key = f"instagram:{account.id}:access_token"

    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json",
    )
    journal.add(key)

    store = FakeCredentialStore()
    store.save(key, "old-instagram-token")

    coordinator = RemoveAccountWithCredentialCleanup(
        remove_account=RemoveAccount(repository),
        account_repository=repository,
        cleanup_repository=journal,
        credential_store=store,
    )

    coordinator.recover_pending()

    assert repository.all() == (account,)
    assert key not in store.secrets
    assert journal.all() == ()


def test_recovery_preserves_instagram_token_if_conversion_never_completed(
    tmp_path,
) -> None:
    repository = InMemoryAccountRepository()

    account = Account(
        name="Existing Instagram Account",
        destination=PublishingDestination.INSTAGRAM,
    )
    repository.add(account)

    key = f"instagram:{account.id}:access_token"

    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json",
    )
    journal.add(key)

    store = FakeCredentialStore()
    store.save(key, "existing-instagram-token")

    coordinator = RemoveAccountWithCredentialCleanup(
        remove_account=RemoveAccount(repository),
        account_repository=repository,
        cleanup_repository=journal,
        credential_store=store,
    )

    coordinator.recover_pending()

    assert repository.all() == (account,)
    assert store.secrets[key] == "existing-instagram-token"
    assert journal.all() == ()
