import pytest
from unittest.mock import Mock

from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.application.credentials.delete_wordpress_credentials import (
    DeleteWordPressCredentials,
)
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)
from socialflow.application.credentials.errors import (
    CredentialStorageError,
)


def test_delete_wordpress_credentials_removes_application_password() -> None:
    """Delete only the credential associated with the given account."""
    credential_store = Mock(spec=CredentialStore)

    account = Account(
        name="My WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    service = DeleteWordPressCredentials(
        credential_store=credential_store,
    )

    service.execute(account)

    expected_key = WordPressCredentialKeys.application_password(account)

    credential_store.delete.assert_called_once_with(expected_key)
    credential_store.save.assert_not_called()


@pytest.mark.parametrize(
    "destination",
    [
        PublishingDestination.FACEBOOK,
        PublishingDestination.INSTAGRAM,
    ],
)
def test_delete_wordpress_credentials_rejects_non_wordpress_accounts(
    destination: PublishingDestination,
) -> None:
    """Non-WordPress accounts must not trigger credential deletion."""
    credential_store = Mock(spec=CredentialStore)

    account = Account(
        name="Non-WordPress Account",
        destination=destination,
    )

    service = DeleteWordPressCredentials(
        credential_store=credential_store,
    )

    with pytest.raises(
        ValueError,
        match="Account must be a WordPress account",
    ):
        service.execute(account)

    credential_store.delete.assert_not_called()
    credential_store.save.assert_not_called()


def test_delete_wordpress_credentials_handles_storage_failure() -> None:
    """Storage failures must raise a credential-specific error."""
    credential_store = Mock(spec=CredentialStore)

    original_error = RuntimeError("Secure storage unavailable")
    credential_store.delete.side_effect = original_error

    account = Account(
        name="My WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    service = DeleteWordPressCredentials(
        credential_store=credential_store,
    )

    with pytest.raises(
        CredentialStorageError,
        match="Could not securely delete WordPress credentials",
    ) as exc_info:
        service.execute(account)

    expected_key = WordPressCredentialKeys.application_password(account)

    credential_store.delete.assert_called_once_with(expected_key)
    credential_store.save.assert_not_called()

    # Preserve the underlying error for debugging.
    assert exc_info.value.__cause__ is original_error
