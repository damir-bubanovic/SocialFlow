import pytest

from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.services.credential_errors import (
    CredentialStorageError,
)
from socialflow.modules.accounts.services.instagram_credential_keys import (
    InstagramCredentialKeys,
)
from socialflow.modules.accounts.services.save_instagram_credentials import (
    SaveInstagramCredentials,
)
from socialflow.modules.accounts.services.get_instagram_credentials import (
    GetInstagramCredentials,
)
from socialflow.modules.accounts.services.delete_instagram_credentials import (
    DeleteInstagramCredentials,
)
from socialflow.modules.accounts.services.facebook_credential_keys import (
    FacebookCredentialKeys,
)
from socialflow.modules.accounts.services.wordpress_credential_keys import (
    WordPressCredentialKeys,
)


class FakeCredentialStore(CredentialStore):
    def __init__(self) -> None:
        self.secrets: dict[str, str] = {}
        self.fail_operation: str | None = None

    def save(self, key: str, secret: str) -> None:
        if self.fail_operation == "save":
            raise RuntimeError("Simulated storage failure")
        self.secrets[key] = secret

    def get(self, key: str) -> str | None:
        if self.fail_operation == "get":
            raise RuntimeError("Simulated retrieval failure")
        return self.secrets.get(key)

    def delete(self, key: str) -> None:
        if self.fail_operation == "delete":
            raise RuntimeError("Simulated deletion failure")
        self.secrets.pop(key, None)


@pytest.fixture
def instagram_account() -> Account:
    return Account(
        name="Instagram Test Account",
        destination=PublishingDestination.INSTAGRAM,
    )


@pytest.fixture
def store() -> FakeCredentialStore:
    return FakeCredentialStore()


def test_instagram_credential_key_uses_account_uuid(
    instagram_account: Account,
) -> None:
    assert InstagramCredentialKeys.access_token(
        instagram_account
    ) == f"instagram:{instagram_account.id}:access_token"


def test_instagram_keys_are_stable_and_unique() -> None:
    first = Account(
        name="First Instagram",
        destination=PublishingDestination.INSTAGRAM,
    )
    second = Account(
        name="Second Instagram",
        destination=PublishingDestination.INSTAGRAM,
    )

    assert InstagramCredentialKeys.access_token(
        first
    ) == InstagramCredentialKeys.access_token(first)

    assert InstagramCredentialKeys.access_token(
        first
    ) != InstagramCredentialKeys.access_token(second)


def test_save_and_retrieve_token(
    instagram_account: Account,
    store: FakeCredentialStore,
) -> None:
    assert SaveInstagramCredentials(store).execute(
        instagram_account, "test-token"
    ) is True

    assert GetInstagramCredentials(store).execute(
        instagram_account
    ) == "test-token"


def test_token_is_trimmed_before_storage(
    instagram_account: Account,
    store: FakeCredentialStore,
) -> None:
    SaveInstagramCredentials(store).execute(
        instagram_account, "  test-token  "
    )

    assert GetInstagramCredentials(store).execute(
        instagram_account
    ) == "test-token"


def test_blank_token_preserves_existing_token(
    instagram_account: Account,
    store: FakeCredentialStore,
) -> None:
    service = SaveInstagramCredentials(store)
    service.execute(instagram_account, "original-token")

    assert service.execute(instagram_account, "   ") is False

    assert GetInstagramCredentials(store).execute(
        instagram_account
    ) == "original-token"


def test_missing_token_returns_none(
    instagram_account: Account,
    store: FakeCredentialStore,
) -> None:
    assert GetInstagramCredentials(store).execute(
        instagram_account
    ) is None


def test_delete_existing_token(
    instagram_account: Account,
    store: FakeCredentialStore,
) -> None:
    SaveInstagramCredentials(store).execute(
        instagram_account, "test-token"
    )

    DeleteInstagramCredentials(store).execute(instagram_account)

    assert GetInstagramCredentials(store).execute(
        instagram_account
    ) is None


def test_delete_missing_token_is_safe(
    instagram_account: Account,
    store: FakeCredentialStore,
) -> None:
    DeleteInstagramCredentials(store).execute(instagram_account)

    assert store.secrets == {}


@pytest.mark.parametrize(
    "service_name",
    ["save", "get", "delete"],
)
def test_services_reject_non_instagram_accounts(
    service_name: str,
    store: FakeCredentialStore,
) -> None:
    account = Account(
        name="WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )

    with pytest.raises(ValueError):
        if service_name == "save":
            SaveInstagramCredentials(store).execute(
                account, "test-token"
            )
        elif service_name == "get":
            GetInstagramCredentials(store).execute(account)
        else:
            DeleteInstagramCredentials(store).execute(account)

    assert store.secrets == {}


@pytest.mark.parametrize(
    "operation",
    ["save", "get", "delete"],
)
def test_storage_failures_are_wrapped(
    operation: str,
    instagram_account: Account,
    store: FakeCredentialStore,
) -> None:
    store.fail_operation = operation

    with pytest.raises(CredentialStorageError) as exc_info:
        if operation == "save":
            SaveInstagramCredentials(store).execute(
                instagram_account, "test-token"
            )
        elif operation == "get":
            GetInstagramCredentials(store).execute(
                instagram_account
            )
        else:
            DeleteInstagramCredentials(store).execute(
                instagram_account
            )

    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert "test-token" not in str(exc_info.value)


def test_instagram_credentials_are_isolated_from_other_platforms(
    instagram_account: Account,
    store: FakeCredentialStore,
) -> None:
    facebook_account = Account(
        name="Facebook Page",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress_account = Account(
        name="WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )

    facebook_key = FacebookCredentialKeys.page_access_token(
        facebook_account
    )
    wordpress_key = WordPressCredentialKeys.application_password(
        wordpress_account
    )

    store.save(facebook_key, "facebook-token")
    store.save(wordpress_key, "wordpress-password")

    SaveInstagramCredentials(store).execute(
        instagram_account, "instagram-token"
    )

    assert len(store.secrets) == 3

    DeleteInstagramCredentials(store).execute(instagram_account)

    assert store.get(facebook_key) == "facebook-token"
    assert store.get(wordpress_key) == "wordpress-password"
    assert len(store.secrets) == 2


def test_multiple_instagram_accounts_have_independent_tokens(
    store: FakeCredentialStore,
) -> None:
    first = Account(
        name="First Instagram",
        destination=PublishingDestination.INSTAGRAM,
    )
    second = Account(
        name="Second Instagram",
        destination=PublishingDestination.INSTAGRAM,
    )

    save = SaveInstagramCredentials(store)
    get = GetInstagramCredentials(store)

    save.execute(first, "first-token")
    save.execute(second, "second-token")

    assert get.execute(first) == "first-token"
    assert get.execute(second) == "second-token"

    DeleteInstagramCredentials(store).execute(first)

    assert get.execute(first) is None
    assert get.execute(second) == "second-token"