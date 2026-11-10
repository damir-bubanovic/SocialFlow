from socialflow.modules.accounts.models.account import Account
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.repositories.account_serializer import (
    AccountSerializer,
)
from socialflow.modules.accounts.models.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.modules.accounts.models.facebook_page_config import (
    FacebookPageConfig,
)
from socialflow.modules.accounts.models.instagram_account_config import (
    InstagramAccountConfig,
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

    from socialflow.modules.accounts.models.account_id import AccountId

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



def test_account_serializer_preserves_facebook_config() -> None:
    config = FacebookPageConfig(
        page_id="123456789",
        page_name="SocialFlow Test Page",
    )
    account = Account(
        name="Facebook Account",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=config,
    )

    serialized = AccountSerializer.to_dict(account)
    restored = AccountSerializer.from_dict(serialized)

    assert serialized["facebook_config"] == {
        "page_id": "123456789",
        "page_name": "SocialFlow Test Page",
    }
    assert restored == account
    assert restored.id == account.id


def test_account_serializer_omits_missing_facebook_config() -> None:
    account = Account(
        name="WordPress Account",
        destination=PublishingDestination.WORDPRESS,
    )

    serialized = AccountSerializer.to_dict(account)

    assert "facebook_config" not in serialized
    assert AccountSerializer.from_dict(serialized) == account


def test_account_serializer_rejects_incomplete_facebook_data() -> None:
    import pytest

    with pytest.raises(KeyError):
        AccountSerializer.from_dict({
            "name": "Facebook Account",
            "destination": "facebook",
            "facebook_config": {
                "page_name": "Missing Page ID",
            },
        })

def test_account_serializer_preserves_instagram_config() -> None:
    config = InstagramAccountConfig(
        instagram_user_id="17841400000000000",
        username="socialflow_example",
    )

    account = Account(
        name="Instagram Account",
        destination=PublishingDestination.INSTAGRAM,
        instagram_config=config,
    )

    serialized = AccountSerializer.to_dict(account)
    restored = AccountSerializer.from_dict(serialized)

    assert serialized["instagram_config"] == {
        "instagram_user_id": "17841400000000000",
        "username": "socialflow_example",
    }
    assert restored == account
    assert restored.id == account.id


def test_account_serializer_omits_missing_instagram_config() -> None:
    account = Account(
        name="WordPress Account",
        destination=PublishingDestination.WORDPRESS,
    )

    serialized = AccountSerializer.to_dict(account)

    assert "instagram_config" not in serialized
    assert AccountSerializer.from_dict(serialized) == account


def test_account_serializer_rejects_incomplete_instagram_data() -> None:
    import pytest

    with pytest.raises(KeyError):
        AccountSerializer.from_dict(
            {
                "name": "Instagram Account",
                "destination": "instagram",
                "instagram_config": {
                    "username": "missing_user_id",
                },
            }
        )