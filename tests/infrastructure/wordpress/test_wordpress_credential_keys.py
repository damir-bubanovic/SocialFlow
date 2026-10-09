from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)


def test_application_password_key_uses_account_id() -> None:
    account = Account(
        name="My WordPress Site",
        destination=PublishingDestination.WORDPRESS,
    )

    key = WordPressCredentialKeys.application_password(account)

    assert key == f"wordpress:{account.id}:application_password"


def test_application_password_key_survives_account_rename() -> None:
    account = Account(
        name="Original WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    renamed_account = Account(
        name="Renamed WordPress",
        destination=PublishingDestination.WORDPRESS,
        id=account.id,
    )

    assert WordPressCredentialKeys.application_password(
        account
    ) == WordPressCredentialKeys.application_password(
        renamed_account
    )