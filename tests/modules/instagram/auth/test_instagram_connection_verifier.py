from unittest.mock import Mock

import pytest

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.connection_status import (
    ConnectionStatus,
)
from socialflow.modules.accounts.models.instagram_account_config import (
    InstagramAccountConfig,
)
from socialflow.modules.accounts.services.instagram_credential_keys import (
    InstagramCredentialKeys,
)
from socialflow.modules.instagram.api.instagram_api_error import (
    InstagramApiError,
)
from socialflow.modules.instagram.auth.instagram_connection_verifier import (
    InstagramConnectionVerifier,
)


def make_account(
    instagram_user_id: str = "123456789",
    username: str = "test_account",
) -> Account:
    return Account(
        name="Test Instagram Account",
        destination=PublishingDestination.INSTAGRAM,
        instagram_config=InstagramAccountConfig(
            instagram_user_id=instagram_user_id,
            username=username,
        ),
    )


def make_verifier():
    credentials = Mock()
    credentials.get.return_value = "test-instagram-token"

    client = Mock()
    client.get.return_value = {
        "id": "123456789",
        "username": "test_account",
    }

    return (
        InstagramConnectionVerifier(credentials, client),
        credentials,
        client,
    )


def test_valid_instagram_connection() -> None:
    verifier, credentials, client = make_verifier()
    account = make_account()

    result = verifier.verify(account)

    assert result.status == ConnectionStatus.CONNECTED
    assert result.is_connected

    credentials.get.assert_called_once_with(
        InstagramCredentialKeys.access_token(account)
    )

    client.get.assert_called_once_with(
        path="123456789",
        access_token="test-instagram-token",
        params={"fields": "id,username"},
    )


def test_missing_token() -> None:
    verifier, credentials, client = make_verifier()
    credentials.get.return_value = None

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.INVALID_CREDENTIALS
    client.get.assert_not_called()


def test_credential_storage_failure() -> None:
    verifier, credentials, client = make_verifier()
    credentials.get.side_effect = RuntimeError(
        "Sensitive credential storage error"
    )

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.ERROR
    assert "Sensitive credential storage error" not in result.message
    client.get.assert_not_called()


def test_expired_token() -> None:
    verifier, _, client = make_verifier()
    client.get.side_effect = InstagramApiError(
        message="Sensitive API error",
        status_code=400,
        code=190,
    )

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.INVALID_CREDENTIALS
    assert "Sensitive API error" not in result.message


def test_missing_permissions() -> None:
    verifier, _, client = make_verifier()
    client.get.side_effect = InstagramApiError(
        message="Permission denied",
        status_code=403,
        code=200,
    )

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.INVALID_CREDENTIALS


def test_temporary_network_failure() -> None:
    verifier, _, client = make_verifier()
    client.get.side_effect = InstagramApiError(
        message="Network failure",
        is_transient=True,
    )

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.UNREACHABLE


def test_unexpected_instagram_account_id() -> None:
    verifier, _, client = make_verifier()
    client.get.return_value = {
        "id": "999999999",
        "username": "other_account",
    }

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.ERROR


def test_invalid_instagram_configuration() -> None:
    verifier, credentials, client = make_verifier()

    result = verifier.verify(
        make_account(instagram_user_id=" ")
    )

    assert result.status == ConnectionStatus.ERROR
    credentials.get.assert_not_called()
    client.get.assert_not_called()


def test_missing_instagram_configuration() -> None:
    verifier, credentials, client = make_verifier()

    account = Account(
        name="Instagram",
        destination=PublishingDestination.INSTAGRAM,
    )

    result = verifier.verify(account)

    assert result.status == ConnectionStatus.ERROR
    credentials.get.assert_not_called()
    client.get.assert_not_called()


def test_wrong_destination_is_rejected() -> None:
    verifier, credentials, client = make_verifier()

    account = Account(
        name="Facebook",
        destination=PublishingDestination.FACEBOOK,
        instagram_config=InstagramAccountConfig(
            instagram_user_id="123456789",
            username="test_account",
        ),
    )

    result = verifier.verify(account)

    assert result.status == ConnectionStatus.ERROR
    credentials.get.assert_not_called()
    client.get.assert_not_called()


def test_unexpected_api_error_is_sanitized() -> None:
    verifier, _, client = make_verifier()
    client.get.side_effect = InstagramApiError(
        message="Sensitive server details",
        status_code=400,
        code=100,
    )

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.ERROR
    assert "Sensitive server details" not in result.message


@pytest.mark.parametrize(
    "response",
    [
        None,
        [],
        "unexpected response",
        {},
        {"id": None},
        {"id": 123456789},
        {"id": ""},
        {"id": " 123456789 "},
    ],
)
def test_malformed_graph_response_is_rejected(response) -> None:
    verifier, _, client = make_verifier()
    client.get.return_value = response

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.ERROR
    assert not result.is_connected


@pytest.mark.parametrize(
    "token",
    [None, "", "   ", 12345],
)
def test_invalid_token_never_reaches_graph_api(token) -> None:
    verifier, credentials, client = make_verifier()
    credentials.get.return_value = token

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.INVALID_CREDENTIALS
    client.get.assert_not_called()


def test_username_change_does_not_invalidate_account() -> None:
    verifier, _, client = make_verifier()
    client.get.return_value = {
        "id": "123456789",
        "username": "renamed_account",
    }

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.CONNECTED


def test_response_does_not_require_username() -> None:
    verifier, _, client = make_verifier()
    client.get.return_value = {"id": "123456789"}

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.CONNECTED


def test_token_is_trimmed_before_api_request() -> None:
    verifier, credentials, client = make_verifier()
    credentials.get.return_value = "  secret-token  "

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.CONNECTED
    assert client.get.call_args.kwargs["access_token"] == "secret-token"


def test_configured_id_is_trimmed_before_api_request() -> None:
    verifier, _, client = make_verifier()

    result = verifier.verify(
        make_account(instagram_user_id=" 123456789 ")
    )

    assert result.status == ConnectionStatus.CONNECTED
    assert client.get.call_args.kwargs["path"] == "123456789"