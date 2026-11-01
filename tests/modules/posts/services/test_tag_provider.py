from socialflow.modules.posts.services.null_tag_provider import NullTagProvider
from socialflow.modules.posts.services.tag_provider import TagProvider
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.tag import Tag
from socialflow.core.destination import PublishingDestination


def test_null_tag_provider_implements_tag_provider() -> None:
    provider = NullTagProvider()

    assert isinstance(provider, TagProvider)


def test_null_tag_provider_returns_no_existing_tags() -> None:
    provider = NullTagProvider()

    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    assert provider.list_tags(account) == ()


def test_null_tag_provider_returns_created_tag() -> None:
    provider = NullTagProvider()

    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    tag = Tag(name="SocialFlow")

    result = provider.create_tag(
        account=account,
        tag=tag,
    )

    assert result == tag