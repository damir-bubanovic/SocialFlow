from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.accounts.account_serializer import (
    AccountSerializer,
)
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)


def test_account_serializer_converts_account_to_dict() -> None:
    account = Account(
        name="Glavna Facebook stranica",
        destination=PublishingDestination.FACEBOOK,
    )

    assert AccountSerializer.to_dict(account) == {
        "id": str(account.id),
        "name": "Glavna Facebook stranica",
        "destination": "facebook",
    }


def test_account_serializer_creates_account_from_dict() -> None:
    from uuid import UUID

    from socialflow.domain.account.account_id import AccountId

    account_id = AccountId(
        UUID("12345678-1234-5678-1234-567812345678")
    )

    account = AccountSerializer.from_dict(
        {
            "id": str(account_id),
            "name": "SocialFlow WordPress",
            "destination": "wordpress",
        }
    )

    assert account == Account(
        name="SocialFlow WordPress",
        destination=PublishingDestination.WORDPRESS,
        id=account_id,
    )

def test_account_serializer_preserves_croatian_characters() -> None:
    account = Account(
        name="Društvena mreža čćžšđ",
        destination=PublishingDestination.INSTAGRAM,
    )

    serialized = AccountSerializer.to_dict(account)
    restored = AccountSerializer.from_dict(serialized)

    assert restored == account

def test_account_serializer_preserves_id() -> None:
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    serialized = AccountSerializer.to_dict(account)
    restored = AccountSerializer.from_dict(serialized)

    assert serialized["id"] == str(account.id)
    assert restored.id == account.id
    assert restored == account


def test_account_serializer_preserves_wordpress_config() -> None:
    """WordPress connection settings must survive JSON serialization."""
    config = WordPressConnectionConfig(
        site_url="https://example.com",
        username="admin",
    )

    account = Account(
        name="My WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=config,
    )

    serialized = AccountSerializer.to_dict(account)

    assert serialized["wordpress_config"] == {
        "site_url": "https://example.com",
        "username": "admin",
    }

    restored = AccountSerializer.from_dict(serialized)

    assert restored.id == account.id
    assert restored.name == account.name
    assert restored.destination == PublishingDestination.WORDPRESS
    assert restored.wordpress_config == config
