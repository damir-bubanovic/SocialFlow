from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)


def test_account_contains_name_and_destination() -> None:
    account = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    assert account.name == "SocialFlow Facebook"
    assert account.destination == PublishingDestination.FACEBOOK

def test_account_has_name_when_name_is_present() -> None:
    account = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    assert account.has_name()


def test_account_has_no_name_when_name_is_whitespace() -> None:
    account = Account(
        name="   ",
        destination=PublishingDestination.FACEBOOK,
    )

    assert not account.has_name()

def test_account_can_be_normalized() -> None:
    account = Account(
        name="  SocialFlow Facebook  ",
        destination=PublishingDestination.FACEBOOK,
    )

    normalized = account.normalized()

    assert normalized.name == "SocialFlow Facebook"
    assert normalized.destination == PublishingDestination.FACEBOOK

def test_account_has_display_name() -> None:
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    assert account.display_name() == "Main Facebook (Facebook)"

def test_account_has_unique_id() -> None:
    first = Account(
        name="First",
        destination=PublishingDestination.FACEBOOK,
    )
    second = Account(
        name="Second",
        destination=PublishingDestination.FACEBOOK,
    )

    assert first.id != second.id


def test_account_normalization_preserves_id() -> None:
    account = Account(
        name="  Main Facebook  ",
        destination=PublishingDestination.FACEBOOK,
    )

    normalized = account.normalized()

    assert normalized.id == account.id


def test_account_normalization_preserves_wordpress_config() -> None:
    """Normalization must preserve WordPress connection settings."""
    config = WordPressConnectionConfig(
        site_url="https://example.com",
        username="admin",
    )

    account = Account(
        name="  My WordPress  ",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=config,
    )

    normalized = account.normalized()

    assert normalized.name == "My WordPress"
    assert normalized.destination == PublishingDestination.WORDPRESS
    assert normalized.id == account.id
    assert normalized.wordpress_config == config
