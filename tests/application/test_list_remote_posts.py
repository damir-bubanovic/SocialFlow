from datetime import datetime
from unittest.mock import Mock

from socialflow.application.publishing.list_remote_posts import (
    ListRemotePosts,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_post import RemotePost
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)


def test_list_remote_posts_delegates_to_provider():
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    expected_posts = (
        RemotePost(
            remote_id="42",
            destination=PublishingDestination.WORDPRESS,
            content="<p>Hello WordPress</p>",
            published_at=datetime(2026, 10, 14, 10, 30),
            status="publish",
        ),
    )

    provider = Mock()
    provider.list_recent_posts.return_value = expected_posts

    service = ListRemotePosts(provider)

    posts = service.execute(account, limit=5)

    assert posts == expected_posts

    provider.list_recent_posts.assert_called_once_with(
        account=account,
        limit=5,
    )


def test_list_remote_posts_returns_empty_result():
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    provider = Mock()
    provider.list_recent_posts.return_value = ()

    service = ListRemotePosts(provider)

    assert service.execute(account) == ()