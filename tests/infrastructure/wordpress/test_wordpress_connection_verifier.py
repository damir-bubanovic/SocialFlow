from urllib.error import URLError

import pytest

from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.domain.account.account import Account
from socialflow.domain.connections.connection_status import (
    ConnectionStatus,
)
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.infrastructure.wordpress.wordpress_connection_verifier import (
    WordPressConnectionVerifier,
)
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)
from socialflow.infrastructure.wordpress.wordpress_http_client import (
    WordPressHttpClient,
    WordPressHttpResponse,
)


class FakeCredentialStore(CredentialStore):
    """In-memory credential store for tests."""

    def __init__(self) -> None:
        self._secrets: dict[str, str] = {}

    def save(self, key: str, secret: str) -> None:
        self._secrets[key] = secret

    def get(self, key: str) -> str | None:
        return self._secrets.get(key)

    def delete(self, key: str) -> None:
        self._secrets.pop(key, None)


class FakeWordPressHttpClient(WordPressHttpClient):
    """Simulate WordPress HTTP responses without network requests."""

    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code

    def get_authenticated_user(
        self,
        site_url: str,
        username: str,
        application_password: str,
    ) -> WordPressHttpResponse:
        return WordPressHttpResponse(
            status_code=self.status_code,
        )


def test_wordpress_verifier_reports_missing_credentials() -> None:
    account = Account(
        name="My WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )

    verifier = WordPressConnectionVerifier(
        credential_store=FakeCredentialStore(),
        http_client=FakeWordPressHttpClient(),
    )

    result = verifier.verify(
        account,
        WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    assert result.status == ConnectionStatus.INVALID_CREDENTIALS
    assert result.is_connected is False
    assert "password is missing" in result.message


def test_wordpress_verifier_reads_stored_credentials() -> None:
    account = Account(
        name="My WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )

    credential_store = FakeCredentialStore()

    credential_store.save(
        WordPressCredentialKeys.application_password(account),
        "test-application-password",
    )

    verifier = WordPressConnectionVerifier(
        credential_store=credential_store,
        http_client=FakeWordPressHttpClient(status_code=200),
    )

    result = verifier.verify(
        account,
        WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    assert result.status == ConnectionStatus.CONNECTED
    assert result.is_connected is True
    assert "verified successfully" in result.message


def test_wordpress_verifier_rejects_http() -> None:
    account = Account(
        name="My WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )

    verifier = WordPressConnectionVerifier(
        credential_store=FakeCredentialStore(),
        http_client=FakeWordPressHttpClient(),
    )

    result = verifier.verify(
        account,
        WordPressConnectionConfig(
            site_url="http://example.com",
            username="admin",
        ),
    )

    assert result.status == ConnectionStatus.ERROR
    assert result.is_connected is False
    assert "HTTPS" in result.message


def test_wordpress_verifier_rejects_missing_configuration() -> None:
    account = Account(
        name="My WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )

    verifier = WordPressConnectionVerifier(
        credential_store=FakeCredentialStore(),
        http_client=FakeWordPressHttpClient(),
    )

    result = verifier.verify(account)

    assert result.status == ConnectionStatus.ERROR
    assert result.is_connected is False
    assert "incomplete" in result.message


@pytest.mark.parametrize("status_code", [401, 403])
def test_wordpress_verifier_rejects_invalid_credentials(
    status_code: int,
) -> None:
    account = Account(
        name="My WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )

    credential_store = FakeCredentialStore()
    credential_store.save(
        WordPressCredentialKeys.application_password(account),
        "test-application-password",
    )

    verifier = WordPressConnectionVerifier(
        credential_store=credential_store,
        http_client=FakeWordPressHttpClient(status_code=status_code),
    )

    result = verifier.verify(
        account,
        WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    assert result.status == ConnectionStatus.INVALID_CREDENTIALS
    assert result.is_connected is False
    assert "authentication was rejected" in result.message


@pytest.mark.parametrize("status_code", [404, 500, 503])
def test_wordpress_verifier_reports_unexpected_http_status(
    status_code: int,
) -> None:
    account = Account(
        name="My WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )

    credential_store = FakeCredentialStore()
    credential_store.save(
        WordPressCredentialKeys.application_password(account),
        "test-application-password",
    )

    verifier = WordPressConnectionVerifier(
        credential_store=credential_store,
        http_client=FakeWordPressHttpClient(status_code=status_code),
    )

    result = verifier.verify(
        account,
        WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    assert result.status == ConnectionStatus.ERROR
    assert result.is_connected is False
    assert str(status_code) in result.message


class FailingWordPressHttpClient(WordPressHttpClient):
    """Simulate a WordPress website that cannot be reached."""

    def get_authenticated_user(
        self,
        site_url: str,
        username: str,
        application_password: str,
    ) -> WordPressHttpResponse:
        raise URLError("Connection refused")


def test_wordpress_verifier_reports_unreachable_site() -> None:
    account = Account(
        name="My WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )

    credential_store = FakeCredentialStore()
    credential_store.save(
        WordPressCredentialKeys.application_password(account),
        "test-application-password",
    )

    verifier = WordPressConnectionVerifier(
        credential_store=credential_store,
        http_client=FailingWordPressHttpClient(),
    )

    result = verifier.verify(
        account,
        WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    assert result.status == ConnectionStatus.UNREACHABLE
    assert result.is_connected is False
    assert "Unable to reach" in result.message


def test_wordpress_verifier_uses_saved_account_configuration() -> None:
    """Verify WordPress using configuration stored in the account."""
    account = Account(
        name="My WordPress Site",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    credential_store = FakeCredentialStore()
    credential_store.save(
        WordPressCredentialKeys.application_password(account),
        "test-application-password",
    )

    from unittest.mock import Mock

    http_client = Mock(spec=WordPressHttpClient)
    http_client.get_authenticated_user.return_value = WordPressHttpResponse(
        status_code=200,
    )

    verifier = WordPressConnectionVerifier(
        credential_store=credential_store,
        http_client=http_client,
    )

    # No separate WordPressConnectionConfig argument.
    result = verifier.verify(account)

    assert result.status == ConnectionStatus.CONNECTED
    assert result.is_connected is True

    http_client.get_authenticated_user.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="test-application-password",
    )
