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
from socialflow.modules.accounts.services.facebook_credential_keys import (
    FacebookCredentialKeys,
)
from socialflow.modules.accounts.services.remove_account import RemoveAccount
from socialflow.modules.accounts.services.remove_account_with_credential_cleanup import (
    RemoveAccountWithCredentialCleanup,
)
from socialflow.modules.accounts.services.credential_errors import (
    CredentialStorageError,
)
from socialflow.modules.accounts.services.errors import (
    AccountCredentialCleanupIncompleteError,
)


class FakeCredentialStore(CredentialStore):
    def __init__(self) -> None:
        self.secrets: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.secrets.get(key)

    def save(self, key: str, secret: str) -> None:
        self.secrets[key] = secret

    def delete(self, key: str) -> None:
        self.secrets.pop(key, None)


def test_successful_facebook_removal_cleans_up_token_and_journal(
    tmp_path,
) -> None:
    repository = InMemoryAccountRepository()
    account = Account(
        name="Facebook Page",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(account)

    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )

    store = FakeCredentialStore()
    key = FacebookCredentialKeys.page_access_token(account)
    store.save(key, "secret-page-token")

    coordinator = RemoveAccountWithCredentialCleanup(
        remove_account=RemoveAccount(repository),
        account_repository=repository,
        cleanup_repository=journal,
        credential_store=store,
    )

    coordinator.execute(account)

    assert repository.all() == ()
    assert key not in store.secrets
    assert journal.all() == ()


def test_failed_account_removal_preserves_credentials(
    tmp_path,
    monkeypatch,
) -> None:
    repository = InMemoryAccountRepository()
    account = Account(
        name="Facebook Page",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(account)

    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )

    store = FakeCredentialStore()
    key = FacebookCredentialKeys.page_access_token(account)
    store.save(key, "secret-page-token")

    coordinator = RemoveAccountWithCredentialCleanup(
        remove_account=RemoveAccount(repository),
        account_repository=repository,
        cleanup_repository=journal,
        credential_store=store,
    )

    def fail_remove(_account: Account) -> None:
        raise OSError("Simulated account persistence failure")

    monkeypatch.setattr(repository, "remove", fail_remove)

    with pytest.raises(
        OSError,
        match="Simulated account persistence failure",
    ):
        coordinator.execute(account)

    assert repository.all() == (account,)
    assert store.secrets[key] == "secret-page-token"

    # A pending entry is safe while the account still exists.
    # Recovery must check account existence before deleting.
    assert journal.all() in ((), (key,))

def test_failed_credential_deletion_retains_pending_cleanup(
    tmp_path,
    monkeypatch,
) -> None:
    repository = InMemoryAccountRepository()
    account = Account(
        name="Facebook Page",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(account)

    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )

    store = FakeCredentialStore()
    key = FacebookCredentialKeys.page_access_token(account)
    store.save(key, "secret-page-token")

    coordinator = RemoveAccountWithCredentialCleanup(
        remove_account=RemoveAccount(repository),
        account_repository=repository,
        cleanup_repository=journal,
        credential_store=store,
    )

    def fail_delete(_key: str) -> None:
        raise OSError("Simulated keyring failure")

    monkeypatch.setattr(store, "delete", fail_delete)

    with pytest.raises(
            AccountCredentialCleanupIncompleteError,
    ) as exc_info:
        coordinator.execute(account)

    assert isinstance(exc_info.value.__cause__, CredentialStorageError)

    assert repository.all() == ()
    assert store.secrets[key] == "secret-page-token"
    assert journal.all() == (key,)

def test_recovery_preserves_credentials_when_account_still_exists(
    tmp_path,
) -> None:
    repository = InMemoryAccountRepository()
    account = Account(
        name="Facebook Page",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(account)

    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )

    store = FakeCredentialStore()
    key = FacebookCredentialKeys.page_access_token(account)
    store.save(key, "secret-page-token")

    # Simulate a crash after recording cleanup intent,
    # but before removing the account.
    journal.add(key)

    coordinator = RemoveAccountWithCredentialCleanup(
        remove_account=RemoveAccount(repository),
        account_repository=repository,
        cleanup_repository=journal,
        credential_store=store,
    )

    coordinator.recover_pending()

    assert repository.all() == (account,)
    assert store.secrets[key] == "secret-page-token"
    assert journal.all() == ()

def test_recovery_deletes_credentials_for_removed_account(
    tmp_path,
) -> None:
    repository = InMemoryAccountRepository()
    account = Account(
        name="Facebook Page",
        destination=PublishingDestination.FACEBOOK,
    )

    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )

    store = FakeCredentialStore()
    key = FacebookCredentialKeys.page_access_token(account)
    store.save(key, "secret-page-token")

    # Simulate an interrupted removal:
    # the account is absent, but its credential remains.
    journal.add(key)

    coordinator = RemoveAccountWithCredentialCleanup(
        remove_account=RemoveAccount(repository),
        account_repository=repository,
        cleanup_repository=journal,
        credential_store=store,
    )

    coordinator.recover_pending()

    assert repository.all() == ()
    assert key not in store.secrets
    assert journal.all() == ()

    # Recovery must be safe to repeat.
    coordinator.recover_pending()

    assert repository.all() == ()
    assert key not in store.secrets
    assert journal.all() == ()

def test_recovery_preserves_credentials_when_account_read_fails(
    tmp_path,
    monkeypatch,
) -> None:
    repository = InMemoryAccountRepository()
    account = Account(
        name="Facebook Page",
        destination=PublishingDestination.FACEBOOK,
    )

    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )

    store = FakeCredentialStore()
    key = FacebookCredentialKeys.page_access_token(account)
    store.save(key, "secret-page-token")

    journal.add(key)

    coordinator = RemoveAccountWithCredentialCleanup(
        remove_account=RemoveAccount(repository),
        account_repository=repository,
        cleanup_repository=journal,
        credential_store=store,
    )

    def fail_read() -> tuple[Account, ...]:
        raise OSError("Simulated account repository read failure")

    monkeypatch.setattr(repository, "all", fail_read)

    with pytest.raises(
        OSError,
        match="Simulated account repository read failure",
    ):
        coordinator.recover_pending()

    assert store.secrets[key] == "secret-page-token"
    assert journal.all() == (key,)

def test_failed_journal_write_prevents_account_removal(
    tmp_path,
    monkeypatch,
) -> None:
    repository = InMemoryAccountRepository()
    account = Account(
        name="Facebook Page",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(account)

    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )

    store = FakeCredentialStore()
    key = FacebookCredentialKeys.page_access_token(account)
    store.save(key, "secret-page-token")

    coordinator = RemoveAccountWithCredentialCleanup(
        remove_account=RemoveAccount(repository),
        account_repository=repository,
        cleanup_repository=journal,
        credential_store=store,
    )

    def fail_journal_add(_key: str) -> None:
        raise OSError("Simulated journal write failure")

    monkeypatch.setattr(journal, "add", fail_journal_add)

    with pytest.raises(
        OSError,
        match="Simulated journal write failure",
    ):
        coordinator.execute(account)

    assert repository.all() == (account,)
    assert store.secrets[key] == "secret-page-token"
    assert journal.all() == ()

def test_failed_journal_clear_retains_recoverable_entry(
    tmp_path,
    monkeypatch,
) -> None:
    repository = InMemoryAccountRepository()
    account = Account(
        name="Facebook Page",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(account)

    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )

    store = FakeCredentialStore()
    key = FacebookCredentialKeys.page_access_token(account)
    store.save(key, "secret-page-token")

    coordinator = RemoveAccountWithCredentialCleanup(
        remove_account=RemoveAccount(repository),
        account_repository=repository,
        cleanup_repository=journal,
        credential_store=store,
    )

    original_remove = journal.remove

    def fail_journal_clear(_key: str) -> None:
        raise OSError("Simulated journal clear failure")

    monkeypatch.setattr(journal, "remove", fail_journal_clear)

    with pytest.raises(
            AccountCredentialCleanupIncompleteError,
    ) as exc_info:
        coordinator.execute(account)

    assert isinstance(exc_info.value.__cause__, OSError)
    assert "Simulated journal clear failure" in str(
        exc_info.value.__cause__
    )

    assert repository.all() == ()
    assert key not in store.secrets
    assert journal.all() == (key,)

    # Restore journal writes and simulate a later recovery attempt.
    monkeypatch.setattr(journal, "remove", original_remove)

    coordinator.recover_pending()

    assert repository.all() == ()
    assert key not in store.secrets
    assert journal.all() == ()

def test_failed_recovery_preserves_credential_and_pending_entry(
    tmp_path,
    monkeypatch,
) -> None:
    repository = InMemoryAccountRepository()
    account = Account(
        name="Facebook Page",
        destination=PublishingDestination.FACEBOOK,
    )

    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )

    store = FakeCredentialStore()
    key = FacebookCredentialKeys.page_access_token(account)
    store.save(key, "secret-page-token")
    journal.add(key)

    coordinator = RemoveAccountWithCredentialCleanup(
        remove_account=RemoveAccount(repository),
        account_repository=repository,
        cleanup_repository=journal,
        credential_store=store,
    )

    original_delete = store.delete

    def fail_delete(_key: str) -> None:
        raise OSError("Simulated recovery keyring failure")

    monkeypatch.setattr(store, "delete", fail_delete)

    with pytest.raises(CredentialStorageError):
        coordinator.recover_pending()

    assert repository.all() == ()
    assert store.secrets[key] == "secret-page-token"
    assert journal.all() == (key,)

    # Restore the credential store and retry recovery.
    monkeypatch.setattr(store, "delete", original_delete)

    coordinator.recover_pending()

    assert repository.all() == ()
    assert key not in store.secrets
    assert journal.all() == ()