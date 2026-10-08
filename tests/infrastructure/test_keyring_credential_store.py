from unittest.mock import patch

from socialflow.infrastructure.credentials.keyring_credential_store import (
    KeyringCredentialStore,
)


def test_save_credential():
    store = KeyringCredentialStore()

    with patch("keyring.set_password") as mocked:
        store.save("account-123", "secret-token")

    mocked.assert_called_once_with(
        "SocialFlow",
        "account-123",
        "secret-token",
    )


def test_get_credential():
    store = KeyringCredentialStore()

    with patch(
        "keyring.get_password",
        return_value="secret-token",
    ):
        result = store.get("account-123")

    assert result == "secret-token"


def test_get_missing_credential():
    store = KeyringCredentialStore()

    with patch("keyring.get_password", return_value=None):
        result = store.get("missing-account")

    assert result is None


def test_delete_credential():
    store = KeyringCredentialStore()

    with patch("keyring.delete_password") as mocked:
        store.delete("account-123")

    mocked.assert_called_once_with(
        "SocialFlow",
        "account-123",
    )