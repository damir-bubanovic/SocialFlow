from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.accounts.account_serializer import (
    AccountSerializer,
)


def test_account_serializer_converts_account_to_dict() -> None:
    account = Account(
        name="Glavna Facebook stranica",
        destination=PublishingDestination.FACEBOOK,
    )

    assert AccountSerializer.to_dict(account) == {
        "name": "Glavna Facebook stranica",
        "destination": "facebook",
    }


def test_account_serializer_creates_account_from_dict() -> None:
    account = AccountSerializer.from_dict(
        {
            "name": "SocialFlow WordPress",
            "destination": "wordpress",
        }
    )

    assert account == Account(
        name="SocialFlow WordPress",
        destination=PublishingDestination.WORDPRESS,
    )


def test_account_serializer_preserves_croatian_characters() -> None:
    account = Account(
        name="Društvena mreža čćžšđ",
        destination=PublishingDestination.INSTAGRAM,
    )

    serialized = AccountSerializer.to_dict(account)
    restored = AccountSerializer.from_dict(serialized)

    assert restored == account