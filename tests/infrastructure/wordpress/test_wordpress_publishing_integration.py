
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
from socialflow.domain.post.tag import Tag
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag


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

def test_account_routed_wordpress_publisher_sends_selected_tag_ids():
    account = Account(
        name="Tagged WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    credential_store = Mock()
    credential_store.get.return_value = "secret"

    post_client = Mock()
    post_client.create_post.return_value = 201

    tag_client = Mock()
    tag_client.list_tags.return_value = (
        WordPressTag(id=101, name="Python"),
        WordPressTag(id=202, name="SocialFlow"),
    )

    router = PublisherRouter(
        publishers={},
        account_factories={
            PublishingDestination.WORDPRESS: (
                lambda selected_account: WordPressPublisher(
                    account=selected_account,
                    credential_store=credential_store,
                    post_client=post_client,
                    tag_client=tag_client,
                )
            ),
        },
    )

    post = PreparedPost(
        source=Post(
            text="Publishing with WordPress tags",
            language=Language.ENGLISH,
            tags=(
                Tag("SocialFlow"),
                Tag("Python"),
            ),
        ),
    )

    publisher = router.publisher_for_account(account)
    publisher.publish(post)

    tag_client.list_tags.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
    )

    post_client.create_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
        content="Publishing with WordPress tags",
        tags=(202, 101),
    )