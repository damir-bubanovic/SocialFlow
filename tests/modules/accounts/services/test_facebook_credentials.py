
import pytest

from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.services.credential_errors import (
    CredentialStorageError,
)
from socialflow.modules.accounts.services.facebook_credential_keys import (
    FacebookCredentialKeys,
)
from socialflow.modules.accounts.services.save_facebook_credentials import (
    SaveFacebookCredentials,
)
from socialflow.modules.accounts.services.get_facebook_credentials import (
    GetFacebookCredentials,
)
from socialflow.modules.accounts.services.delete_facebook_credentials import (
    DeleteFacebookCredentials,
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
def facebook_account() -> Account:
    return Account(
        name="Facebook Test Page",
        destination=PublishingDestination.FACEBOOK,
    )


@pytest.fixture
def store() -> FakeCredentialStore:
    return FakeCredentialStore()


def test_facebook_credential_key_uses_account_uuid(
    facebook_account: Account,
) -> None:
    assert FacebookCredentialKeys.page_access_token(
        facebook_account
    ) == f"facebook:{facebook_account.id}:page_access_token"


def test_facebook_keys_are_stable_and_unique() -> None:
    first = Account(
        name="First Page",
        destination=PublishingDestination.FACEBOOK,
    )
    second = Account(
        name="Second Page",
        destination=PublishingDestination.FACEBOOK,
    )

    assert FacebookCredentialKeys.page_access_token(
        first
    ) == FacebookCredentialKeys.page_access_token(first)

    assert FacebookCredentialKeys.page_access_token(
        first
    ) != FacebookCredentialKeys.page_access_token(second)


def test_save_and_retrieve_token(
    facebook_account: Account,
    store: FakeCredentialStore,
) -> None:
    assert SaveFacebookCredentials(store).execute(
        facebook_account, "test-token"
    ) is True

    assert GetFacebookCredentials(store).execute(
        facebook_account
    ) == "test-token"


def test_token_is_trimmed_before_storage(
    facebook_account: Account,
    store: FakeCredentialStore,
) -> None:
    SaveFacebookCredentials(store).execute(
        facebook_account, "  test-token  "
    )

    assert GetFacebookCredentials(store).execute(
        facebook_account
    ) == "test-token"


def test_blank_token_preserves_existing_token(
    facebook_account: Account,
    store: FakeCredentialStore,
) -> None:
    service = SaveFacebookCredentials(store)
    service.execute(facebook_account, "original-token")

    assert service.execute(facebook_account, "   ") is False
    assert GetFacebookCredentials(store).execute(
        facebook_account
    ) == "original-token"


def test_missing_token_returns_none(
    facebook_account: Account,
    store: FakeCredentialStore,
) -> None:
    assert GetFacebookCredentials(store).execute(
        facebook_account
    ) is None


def test_delete_existing_token(
    facebook_account: Account,
    store: FakeCredentialStore,
) -> None:
    SaveFacebookCredentials(store).execute(
        facebook_account, "test-token"
    )

    DeleteFacebookCredentials(store).execute(facebook_account)

    assert GetFacebookCredentials(store).execute(
        facebook_account
    ) is None


def test_delete_missing_token_is_safe(
    facebook_account: Account,
    store: FakeCredentialStore,
) -> None:
    DeleteFacebookCredentials(store).execute(facebook_account)

    assert store.secrets == {}


@pytest.mark.parametrize(
    "service_name",
    ["save", "get", "delete"],
)
def test_services_reject_non_facebook_accounts(
    service_name: str,
    store: FakeCredentialStore,
) -> None:
    account = Account(
        name="WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )

    with pytest.raises(ValueError):
        if service_name == "save":
            SaveFacebookCredentials(store).execute(
                account, "test-token"
            )
        elif service_name == "get":
            GetFacebookCredentials(store).execute(account)
        else:
            DeleteFacebookCredentials(store).execute(account)

    assert store.secrets == {}


@pytest.mark.parametrize(
    "operation",
    ["save", "get", "delete"],
)
def test_storage_failures_are_wrapped(
    operation: str,
    facebook_account: Account,
    store: FakeCredentialStore,
) -> None:
    store.fail_operation = operation

    with pytest.raises(CredentialStorageError) as exc_info:
        if operation == "save":
            SaveFacebookCredentials(store).execute(
                facebook_account, "test-token"
            )
        elif operation == "get":
            GetFacebookCredentials(store).execute(
                facebook_account
            )
        else:
            DeleteFacebookCredentials(store).execute(
                facebook_account
            )

    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert "test-token" not in str(exc_info.value)


def test_facebook_and_wordpress_credentials_are_isolated(
    facebook_account: Account,
    store: FakeCredentialStore,
) -> None:
    wordpress_account = Account(
        name="WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )

    wordpress_key = WordPressCredentialKeys.application_password(
        wordpress_account
    )
    store.save(wordpress_key, "wordpress-password")

    SaveFacebookCredentials(store).execute(
        facebook_account, "facebook-token"
    )

    assert len(store.secrets) == 2

    DeleteFacebookCredentials(store).execute(facebook_account)

    assert store.get(wordpress_key) == "wordpress-password"
    assert len(store.secrets) == 1


def test_multiple_facebook_accounts_have_independent_tokens(
    store: FakeCredentialStore,
) -> None:
    first = Account(
        name="First Page",
        destination=PublishingDestination.FACEBOOK,
    )
    second = Account(
        name="Second Page",
        destination=PublishingDestination.FACEBOOK,
    )

    save = SaveFacebookCredentials(store)
    get = GetFacebookCredentials(store)

    save.execute(first, "first-token")
    save.execute(second, "second-token")

    assert get.execute(first) == "first-token"
    assert get.execute(second) == "second-token"

    DeleteFacebookCredentials(store).execute(first)

    assert get.execute(first) is None
    assert get.execute(second) == "second-token"
