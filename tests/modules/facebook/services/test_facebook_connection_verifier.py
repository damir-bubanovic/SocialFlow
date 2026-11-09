import pytest
from unittest.mock import Mock

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.connection_status import (
    ConnectionStatus,
)
from socialflow.modules.accounts.models.facebook_page_config import (
    FacebookPageConfig,
)
from socialflow.modules.accounts.services.facebook_credential_keys import (
    FacebookCredentialKeys,
)
from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)
from socialflow.modules.facebook.services.facebook_connection_verifier import (
    FacebookConnectionVerifier,
)


def make_account() -> Account:
    return Account(
        name="Test Facebook Page",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="123456789",
            page_name="Test Facebook Page",
        ),
    )


def make_verifier():
    credentials = Mock()
    credentials.get.return_value = "test-page-token"

    client = Mock()
    client.get.return_value = {
        "id": "123456789",
        "name": "Test Facebook Page",
    }

    return FacebookConnectionVerifier(credentials, client), credentials, client


def test_valid_page_connection() -> None:
    verifier, credentials, client = make_verifier()
    account = make_account()

    result = verifier.verify(account)

    assert result.status == ConnectionStatus.CONNECTED
    assert result.is_connected
    credentials.get.assert_called_once_with(
        FacebookCredentialKeys.page_access_token(account)
    )
    client.get.assert_called_once_with(
        path="123456789",
        access_token="test-page-token",
        params={"fields": "id,name"},
    )


def test_missing_token() -> None:
    verifier, credentials, client = make_verifier()
    credentials.get.return_value = None

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.INVALID_CREDENTIALS
    client.get.assert_not_called()


def test_credential_storage_failure() -> None:
    verifier, credentials, client = make_verifier()
    credentials.get.side_effect = RuntimeError("Sensitive storage error")

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.ERROR
    assert "Sensitive storage error" not in result.message
    client.get.assert_not_called()


def test_expired_token() -> None:
    verifier, _, client = make_verifier()
    client.get.side_effect = FacebookApiError(
        message="Sensitive API error",
        status_code=400,
        code=190,
    )

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.INVALID_CREDENTIALS
    assert "Sensitive API error" not in result.message


def test_missing_permissions() -> None:
    verifier, _, client = make_verifier()
    client.get.side_effect = FacebookApiError(
        message="Permission denied",
        status_code=403,
        code=200,
    )

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.INVALID_CREDENTIALS


def test_temporary_network_failure() -> None:
    verifier, _, client = make_verifier()
    client.get.side_effect = FacebookApiError(
        message="Network failure",
        is_transient=True,
    )

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.UNREACHABLE


def test_unexpected_page_id() -> None:
    verifier, _, client = make_verifier()
    client.get.return_value = {
        "id": "999999999",
        "name": "Other Page",
    }

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.ERROR


def test_invalid_page_configuration() -> None:
    verifier, credentials, client = make_verifier()
    account = Account(
        name="Invalid Facebook Page",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="",
            page_name="",
        ),
    )

    result = verifier.verify(account)

    assert result.status == ConnectionStatus.ERROR
    credentials.get.assert_not_called()
    client.get.assert_not_called()


def test_unexpected_api_error_is_sanitized() -> None:
    verifier, _, client = make_verifier()
    client.get.side_effect = FacebookApiError(
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
    [
        None,
        "",
        "   ",
        12345,
    ],
)
def test_missing_or_invalid_token_never_reaches_graph_api(
    token,
) -> None:
    verifier, credentials, client = make_verifier()
    credentials.get.return_value = token

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.INVALID_CREDENTIALS
    client.get.assert_not_called()


@pytest.mark.parametrize(
    "error",
    [
        FacebookApiError(
            message="SECRET_ACCESS_TOKEN",
            status_code=401,
            code=190,
        ),
        FacebookApiError(
            message="SECRET_ACCESS_TOKEN",
            status_code=403,
            code=200,
        ),
        FacebookApiError(
            message="SECRET_ACCESS_TOKEN",
            status_code=503,
            is_transient=True,
        ),
        FacebookApiError(
            message="SECRET_ACCESS_TOKEN",
            status_code=400,
            code=100,
        ),
    ],
)
def test_api_error_details_are_not_exposed(error) -> None:
    verifier, _, client = make_verifier()
    client.get.side_effect = error

    result = verifier.verify(make_account())

    assert not result.is_connected
    assert "SECRET_ACCESS_TOKEN" not in result.message
    assert "SECRET_ACCESS_TOKEN" not in str(result)


def test_valid_response_does_not_require_page_name() -> None:
    verifier, _, client = make_verifier()
    client.get.return_value = {"id": "123456789"}

    result = verifier.verify(make_account())

    assert result.status == ConnectionStatus.CONNECTED
