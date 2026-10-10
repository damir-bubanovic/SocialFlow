
from unittest.mock import Mock

from socialflow.application.publishing.prepared_post import PreparedPost
from socialflow.application.publishing.publisher_router import PublisherRouter
from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_publisher import (
    WordPressPublisher,
)


def test_wordpress_account_resolves_to_wordpress_publisher() -> None:
    account = Account(
        name="Test WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    credential_store = Mock()
    post_client = Mock()

    router = PublisherRouter(
        publishers={},
        account_factories={
            PublishingDestination.WORDPRESS: (
                lambda selected_account: WordPressPublisher(
                    account=selected_account,
                    credential_store=credential_store,
                    post_client=post_client,
                )
            ),
        },
    )

    publisher = router.publisher_for_account(account)

    assert isinstance(publisher, WordPressPublisher)


def test_wordpress_publisher_uses_selected_account() -> None:
    first_account = Account(
        name="First WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    second_account = Account(
        name="Second WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    credential_store = Mock()
    post_client = Mock()

    router = PublisherRouter(
        publishers={},
        account_factories={
            PublishingDestination.WORDPRESS: (
                lambda selected_account: WordPressPublisher(
                    account=selected_account,
                    credential_store=credential_store,
                    post_client=post_client,
                )
            ),
        },
    )

    first_publisher = router.publisher_for_account(first_account)
    second_publisher = router.publisher_for_account(second_account)

    assert isinstance(first_publisher, WordPressPublisher)
    assert isinstance(second_publisher, WordPressPublisher)

    assert first_publisher is not second_publisher
    assert first_publisher._account is first_account
    assert second_publisher._account is second_account


def test_wordpress_publisher_rejects_unconfigured_account() -> None:
    account = Account(
        name="Unconfigured WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    publisher = WordPressPublisher(
        account=account,
        credential_store=Mock(),
        post_client=Mock(),
    )

    post = PreparedPost(
        source=Post(
            text="Test WordPress publication",
            language=Language.ENGLISH,
        )
    )

    import pytest

    with pytest.raises(ValueError, match="settings are incomplete"):
        publisher.publish(post)
