import pytest

from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.application.credentials.pending_cleanup_guarded_credential_store import (
    PendingCleanupGuardedCredentialStore,
)
from socialflow.modules.accounts.repositories.json_pending_credential_cleanup_repository import (
    JsonPendingCredentialCleanupRepository,
)


class FakeCredentialStore(CredentialStore):
    def __init__(self) -> None:
        self.secrets: dict[str, str] = {}

    def save(self, key: str, secret: str) -> None:
        self.secrets[key] = secret

    def get(self, key: str) -> str | None:
        return self.secrets.get(key)

    def delete(self, key: str) -> None:
        self.secrets.pop(key, None)


def test_save_allowed_without_pending_cleanup(tmp_path) -> None:
    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )
    store = FakeCredentialStore()
    guarded = PendingCleanupGuardedCredentialStore(store, journal)

    key = "facebook:12345678-1234-5678-1234-567812345678:page_access_token"

    guarded.save(key, "new-token")

    assert store.get(key) == "new-token"
    assert journal.all() == ()


def test_save_rejected_while_cleanup_is_pending(tmp_path) -> None:
    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )
    store = FakeCredentialStore()
    guarded = PendingCleanupGuardedCredentialStore(store, journal)

    key = "facebook:12345678-1234-5678-1234-567812345678:page_access_token"

    store.save(key, "original-token")
    journal.add(key)

    with pytest.raises(
        ValueError,
        match="Credential cannot be saved while cleanup is pending",
    ):
        guarded.save(key, "replacement-token")

    assert store.get(key) == "original-token"
    assert journal.all() == (key,)


def test_get_delegates_to_underlying_store(tmp_path) -> None:
    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )
    store = FakeCredentialStore()
    guarded = PendingCleanupGuardedCredentialStore(store, journal)

    key = "facebook:12345678-1234-5678-1234-567812345678:page_access_token"
    store.save(key, "existing-token")

    assert guarded.get(key) == "existing-token"


def test_delete_delegates_to_underlying_store(tmp_path) -> None:
    journal = JsonPendingCredentialCleanupRepository(
        tmp_path / "pending_credential_cleanup.json"
    )
    store = FakeCredentialStore()
    guarded = PendingCleanupGuardedCredentialStore(store, journal)

    key = "facebook:12345678-1234-5678-1234-567812345678:page_access_token"
    store.save(key, "existing-token")

    guarded.delete(key)

    assert store.get(key) is None