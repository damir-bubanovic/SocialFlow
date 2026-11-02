
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.facebook_page_config import (
    FacebookPageConfig,
)


def test_facebook_page_config_normalizes_values() -> None:
    config = FacebookPageConfig(
        page_id=" 123456789 ",
        page_name=" My Facebook Page ",
    )

    assert config.normalized() == FacebookPageConfig(
        page_id="123456789",
        page_name="My Facebook Page",
    )


def test_facebook_page_config_requires_page_id() -> None:
    assert not FacebookPageConfig(
        page_id="   ",
        page_name="My Page",
    ).is_complete()


def test_facebook_page_config_accepts_page_id() -> None:
    assert FacebookPageConfig(
        page_id="123456789",
        page_name="",
    ).is_complete()


def test_account_normalization_preserves_facebook_config() -> None:
    account = Account(
        name=" My Facebook ",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id=" 12345 ",
            page_name=" My Page ",
        ),
    )

    normalized = account.normalized()

    assert normalized.id == account.id
    assert normalized.name == "My Facebook"
    assert normalized.facebook_config == FacebookPageConfig(
        page_id="12345",
        page_name="My Page",
    )
    assert normalized.wordpress_config is None


def test_existing_account_without_facebook_config() -> None:
    account = Account(
        name="Existing WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    assert account.facebook_config is None
    assert account.normalized().facebook_config is None
