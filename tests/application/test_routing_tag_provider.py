
from unittest.mock import Mock

from socialflow.application.tags.routing_tag_provider import (
    RoutingTagProvider,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination


def make_account(destination: PublishingDestination) -> Account:
    return Account(
        name="Test Account",
        destination=destination,
    )


def test_routes_wordpress_tag_listing() -> None:
    wordpress = Mock()
    fallback = Mock()
    expected = (Tag(name="Python"),)
    wordpress.list_tags.return_value = expected

    provider = RoutingTagProvider(
        providers={PublishingDestination.WORDPRESS: wordpress},
        fallback=fallback,
    )

    account = make_account(PublishingDestination.WORDPRESS)

    assert provider.list_tags(account) == expected

    wordpress.list_tags.assert_called_once_with(account)
    fallback.list_tags.assert_not_called()


def test_uses_fallback_for_facebook() -> None:
    wordpress = Mock()
    fallback = Mock()
    fallback.list_tags.return_value = ()

    provider = RoutingTagProvider(
        providers={PublishingDestination.WORDPRESS: wordpress},
        fallback=fallback,
    )

    account = make_account(PublishingDestination.FACEBOOK)

    assert provider.list_tags(account) == ()

    fallback.list_tags.assert_called_once_with(account)
    wordpress.list_tags.assert_not_called()


def test_routes_wordpress_tag_creation() -> None:
    wordpress = Mock()
    fallback = Mock()
    tag = Tag(name="Python")
    wordpress.create_tag.return_value = tag

    provider = RoutingTagProvider(
        providers={PublishingDestination.WORDPRESS: wordpress},
        fallback=fallback,
    )

    account = make_account(PublishingDestination.WORDPRESS)

    assert provider.create_tag(account, tag) == tag

    wordpress.create_tag.assert_called_once_with(account, tag)
    fallback.create_tag.assert_not_called()


def test_uses_fallback_for_instagram_creation() -> None:
    wordpress = Mock()
    fallback = Mock()
    tag = Tag(name="SocialFlow")
    fallback.create_tag.return_value = tag

    provider = RoutingTagProvider(
        providers={PublishingDestination.WORDPRESS: wordpress},
        fallback=fallback,
    )

    account = make_account(PublishingDestination.INSTAGRAM)

    assert provider.create_tag(account, tag) == tag

    fallback.create_tag.assert_called_once_with(account, tag)
    wordpress.create_tag.assert_not_called()
