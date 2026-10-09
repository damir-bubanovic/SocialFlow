
import pytest

from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.application.credentials.save_wordpress_credentials import (
    SaveWordPressCredentials,
)
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)


class FakeCredentialStore(CredentialStore):
    """In-memory credential storage for tests."""

    def __init__(self) -> None:
        self.secrets: dict[str, str] = {}

    def save(self, key: str, secret: str) -> None:
        self.secrets[key] = secret

    def get(self, key: str) -> str | None:
        return self.secrets.get(key)

    def delete(self, key: str) -> None:
        self.secrets.pop(key, None)


def test_saves_wordpress_application_password() -> None:
    account = Account(
        name="My WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )
    store = FakeCredentialStore()
    service = SaveWordPressCredentials(store)

    saved = service.execute(account, "test-password")

    assert saved is True
    assert store.get(
        WordPressCredentialKeys.application_password(account)
    ) == "test-password"


def test_blank_password_preserves_existing_credential() -> None:
    account = Account(
        name="My WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )
    store = FakeCredentialStore()
    service = SaveWordPressCredentials(store)

    service.execute(account, "original-password")

    saved = service.execute(account, "   ")

    assert saved is False
    assert store.get(
        WordPressCredentialKeys.application_password(account)
    ) == "original-password"


def test_rejects_non_wordpress_account() -> None:
    account = Account(
        name="Facebook Page",
        destination=PublishingDestination.FACEBOOK,
    )
    store = FakeCredentialStore()
    service = SaveWordPressCredentials(store)

    with pytest.raises(ValueError):
        service.execute(account, "test-password")

    assert store.secrets == {}


def test_password_is_associated_with_account_uuid() -> None:
    first_account = Account(
        name="First Site",
        destination=PublishingDestination.WORDPRESS,
    )
    second_account = Account(
        name="Second Site",
        destination=PublishingDestination.WORDPRESS,
    )

    store = FakeCredentialStore()
    service = SaveWordPressCredentials(store)

    service.execute(first_account, "first-password")
    service.execute(second_account, "second-password")

    assert store.get(
        WordPressCredentialKeys.application_password(first_account)
    ) == "first-password"

    assert store.get(
        WordPressCredentialKeys.application_password(second_account)
    ) == "second-password"

    assert len(store.secrets) == 2


def test_blank_password_does_not_overwrite_existing_credential() -> None:
    """An empty password must preserve the existing stored credential."""
    store = FakeCredentialStore()
    service = SaveWordPressCredentials(store)

    account = Account(
        name="My WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    key = WordPressCredentialKeys.application_password(account)
    store.save(key=key, secret="existing-password")

    result = service.execute(account, "")

    assert result is False
    assert store.get(key) == "existing-password"
