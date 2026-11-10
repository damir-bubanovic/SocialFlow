from socialflow.modules.accounts.models.instagram_account_config import (
    InstagramAccountConfig,
)


def test_instagram_account_config_normalizes_values() -> None:
    config = InstagramAccountConfig(
        instagram_user_id=" 17841400000000000 ",
        username=" example_account ",
    )

    assert config.normalized() == InstagramAccountConfig(
        instagram_user_id="17841400000000000",
        username="example_account",
    )


def test_instagram_account_config_requires_user_id() -> None:
    config = InstagramAccountConfig(
        instagram_user_id="   ",
        username="example_account",
    )

    assert not config.is_complete()


def test_instagram_account_config_accepts_user_id() -> None:
    config = InstagramAccountConfig(
        instagram_user_id="17841400000000000",
        username="",
    )

    assert config.is_complete()


def test_instagram_account_config_is_immutable() -> None:
    from dataclasses import FrozenInstanceError

    import pytest

    config = InstagramAccountConfig(
        instagram_user_id="17841400000000000",
        username="example_account",
    )

    with pytest.raises(FrozenInstanceError):
        setattr(config, "username", "changed")

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account


def test_account_normalization_preserves_instagram_config() -> None:
    account = Account(
        name="  My Instagram  ",
        destination=PublishingDestination.INSTAGRAM,
        instagram_config=InstagramAccountConfig(
            instagram_user_id=" 17841400000000000 ",
            username=" example_account ",
        ),
    )

    normalized = account.normalized()

    assert normalized.id == account.id
    assert normalized.name == "My Instagram"
    assert normalized.destination is PublishingDestination.INSTAGRAM
    assert normalized.instagram_config == InstagramAccountConfig(
        instagram_user_id="17841400000000000",
        username="example_account",
    )
    assert normalized.wordpress_config is None
    assert normalized.facebook_config is None


def test_existing_account_without_instagram_config() -> None:
    account = Account(
        name="Existing Account",
        destination=PublishingDestination.WORDPRESS,
    )

    assert account.instagram_config is None
    assert account.normalized().instagram_config is None


def test_account_normalization_preserves_other_platform_configs() -> None:
    from socialflow.modules.accounts.models.facebook_page_config import (
        FacebookPageConfig,
    )

    account = Account(
        name="Facebook Account",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id=" 123456 ",
            page_name=" Example Page ",
        ),
    )

    normalized = account.normalized()

    assert normalized.facebook_config == FacebookPageConfig(
        page_id="123456",
        page_name="Example Page",
    )
    assert normalized.instagram_config is None