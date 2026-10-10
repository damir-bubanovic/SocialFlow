
from unittest.mock import Mock

import pytest

from socialflow.application.publishing.errors import (
    PublisherNotConfiguredError,
)
from socialflow.application.publishing.publisher import Publisher
from socialflow.application.publishing.publisher_router import PublisherRouter
from socialflow.domain.account.account import Account
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination


class RecordingPublisher(Publisher):
    """Test publisher used for routing assertions."""

    def publish(self, post: Post) -> None:
        pass


def test_publisher_router_returns_publisher_for_destination() -> None:
    facebook_publisher = RecordingPublisher()

    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: facebook_publisher,
        }
    )

    publisher = router.publisher_for(
        PublishingDestination.FACEBOOK
    )

    assert publisher is facebook_publisher


def test_publisher_router_rejects_unconfigured_destination() -> None:
    router = PublisherRouter({})

    with pytest.raises(
        PublisherNotConfiguredError,
        match="No publisher configured for instagram.",
    ):
        router.publisher_for(PublishingDestination.INSTAGRAM)


def test_publisher_for_account_uses_account_factory() -> None:
    wordpress_publisher = Mock()
    wordpress_factory = Mock(return_value=wordpress_publisher)

    router = PublisherRouter(
        publishers={},
        account_factories={
            PublishingDestination.WORDPRESS: wordpress_factory,
        },
    )

    account = Account(
        name="Test WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    result = router.publisher_for_account(account)

    assert result is wordpress_publisher
    wordpress_factory.assert_called_once_with(account)


def test_publisher_for_account_falls_back_to_destination() -> None:
    facebook_publisher = Mock()

    router = PublisherRouter(
        publishers={
            PublishingDestination.FACEBOOK: facebook_publisher,
        },
    )

    account = Account(
        name="Test Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    result = router.publisher_for_account(account)

    assert result is facebook_publisher


def test_publisher_for_account_rejects_unconfigured_destination() -> None:
    router = PublisherRouter(publishers={})

    account = Account(
        name="Unconfigured WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    with pytest.raises(PublisherNotConfiguredError):
        router.publisher_for_account(account)


def test_different_wordpress_accounts_get_separate_publishers() -> None:
    first_account = Account(
        name="WordPress Site One",
        destination=PublishingDestination.WORDPRESS,
    )

    second_account = Account(
        name="WordPress Site Two",
        destination=PublishingDestination.WORDPRESS,
    )

    first_publisher = Mock(spec=Publisher)
    second_publisher = Mock(spec=Publisher)

    wordpress_factory = Mock(
        side_effect=[first_publisher, second_publisher]
    )

    router = PublisherRouter(
        publishers={},
        account_factories={
            PublishingDestination.WORDPRESS: wordpress_factory,
        },
    )

    result_one = router.publisher_for_account(first_account)
    result_two = router.publisher_for_account(second_account)

    assert result_one is first_publisher
    assert result_two is second_publisher
    assert result_one is not result_two

    assert wordpress_factory.call_count == 2
    assert wordpress_factory.call_args_list == [
        ((first_account,), {}),
        ((second_account,), {}),
    ]
