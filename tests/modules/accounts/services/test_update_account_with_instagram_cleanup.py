
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
from socialflow.modules.accounts.services.remove_account import RemoveAccount
from socialflow.modules.accounts.services.remove_account_with_credential_cleanup import (
    RemoveAccountWithCredentialCleanup,
)
from socialflow.modules.accounts.services.update_account import UpdateAccount
from socialflow.modules.accounts.services.update_account_with_instagram_cleanup import (
    InstagramConversionCleanupIncompleteError,
    UpdateAccountWithInstagramCleanup,
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
            raise OSError("Simulated keyring failure")
        self.secrets.pop(key, None)


def setup_conversion(tmp_path):
    repository = InMemoryAccountRepository()
    current = Account(
        name="Instagram Account",
        destination=PublishingDestination.INSTAGRAM,
    )
    repository.add(current)

    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json",
    )
    store = FakeCredentialStore()
    key = f"instagram:{current.id}:access_token"
    store.save(key, "secret-instagram-token")

    service = UpdateAccountWithInstagramCleanup(
        update_account=UpdateAccount(repository),
        cleanup_repository=journal,
        credential_store=store,
        account_repository=repository,
    )
    recovery = RemoveAccountWithCredentialCleanup(
        remove_account=RemoveAccount(repository),
        account_repository=repository,
        cleanup_repository=journal,
        credential_store=store,
    )
    return repository, current, journal, store, key, service, recovery


def test_successful_conversion_removes_old_token(tmp_path) -> None:
    repository, current, journal, store, key, service, _ = (
        setup_conversion(tmp_path)
    )

    service.execute(
        current,
        Account(
            name="Converted Account",
            destination=PublishingDestination.FACEBOOK,
        ),
    )

    assert repository.all()[0].destination == PublishingDestination.FACEBOOK
    assert key not in store.secrets
    assert journal.all() == ()


def test_failed_account_update_preserves_token(
    tmp_path,
    monkeypatch,
) -> None:
    repository, current, journal, store, key, service, recovery = (
        setup_conversion(tmp_path)
    )

    def fail_update(_current, _updated) -> None:
        raise OSError("Simulated account update failure")

    monkeypatch.setattr(repository, "update", fail_update)

    with pytest.raises(OSError, match="Simulated account update failure"):
        service.execute(
            current,
            Account(
                name="Converted Account",
                destination=PublishingDestination.FACEBOOK,
            ),
        )

    assert repository.all() == (current,)
    assert store.secrets[key] == "secret-instagram-token"

    recovery.recover_pending()

    assert store.secrets[key] == "secret-instagram-token"
    assert journal.all() == ()


def test_failed_update_clears_journal_when_instagram_account_is_unchanged(
    tmp_path,
    monkeypatch,
) -> None:
    repository, current, journal, store, key, service, _recovery = (
        setup_conversion(tmp_path)
    )

    def fail_update(_current, _updated) -> None:
        raise OSError("Simulated account update failure")

    monkeypatch.setattr(repository, "update", fail_update)

    with pytest.raises(
        OSError,
        match="Simulated account update failure",
    ):
        service.execute(
            current,
            Account(
                name="Converted Facebook Account",
                destination=PublishingDestination.FACEBOOK,
            ),
        )

    # The account was not converted.
    assert repository.all() == (current,)

    # The original Instagram token must remain intact.
    assert store.secrets[key] == "secret-instagram-token"

    # No cleanup remains necessary for an unchanged Instagram account.
    assert journal.all() == ()


def test_failed_update_preserves_journal_when_account_state_is_uncertain(
    tmp_path,
    monkeypatch,
) -> None:
    repository, current, journal, store, key, service, _recovery = (
        setup_conversion(tmp_path)
    )

    def fail_update(_current, _updated) -> None:
        raise OSError("Simulated account update failure")

    original_all = repository.all
    read_count = 0

    def fail_second_read():
        nonlocal read_count
        read_count += 1

        if read_count >= 2:
            raise OSError("Simulated account repository read failure")

        return original_all()

    monkeypatch.setattr(repository, "update", fail_update)
    monkeypatch.setattr(repository, "all", fail_second_read)

    with pytest.raises(
        OSError,
        match="Simulated account update failure",
    ):
        service.execute(
            current,
            Account(
                name="Converted Facebook Account",
                destination=PublishingDestination.FACEBOOK,
            ),
        )

    # An uncertain account state must never trigger token deletion.
    assert store.secrets[key] == "secret-instagram-token"

    # Recovery must retain the opportunity to resolve the operation.
    assert journal.all() == (key,)


def test_failed_token_deletion_is_recovered(
    tmp_path,
) -> None:
    repository, current, journal, store, key, service, recovery = (
        setup_conversion(tmp_path)
    )

    store.fail_delete = True

    with pytest.raises(InstagramConversionCleanupIncompleteError):
        service.execute(
            current,
            Account(
                name="Converted Account",
                destination=PublishingDestination.WORDPRESS,
            ),
        )

    assert repository.all()[0].destination == PublishingDestination.WORDPRESS
    assert store.secrets[key] == "secret-instagram-token"
    assert journal.all() == (key,)

    store.fail_delete = False
    recovery.recover_pending()

    assert key not in store.secrets
    assert journal.all() == ()


def test_journal_failure_prevents_conversion(
    tmp_path,
    monkeypatch,
) -> None:
    repository, current, journal, store, key, service, _ = (
        setup_conversion(tmp_path)
    )

    def fail_add(_key: str) -> None:
        raise OSError("Simulated journal failure")

    monkeypatch.setattr(journal, "add", fail_add)

    with pytest.raises(OSError, match="Simulated journal failure"):
        service.execute(
            current,
            Account(
                name="Converted Account",
                destination=PublishingDestination.FACEBOOK,
            ),
        )

    assert repository.all() == (current,)
    assert store.secrets[key] == "secret-instagram-token"
    assert journal.all() == ()


def test_regular_instagram_update_does_not_delete_token(tmp_path) -> None:
    repository, current, journal, store, key, service, _ = (
        setup_conversion(tmp_path)
    )

    service.execute(
        current,
        Account(
            name="Renamed Instagram Account",
            destination=PublishingDestination.INSTAGRAM,
        ),
    )

    assert repository.all()[0].name == "Renamed Instagram Account"
    assert store.secrets[key] == "secret-instagram-token"
    assert journal.all() == ()
