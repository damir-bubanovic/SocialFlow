from unittest.mock import Mock

import pytest

from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.infrastructure.wordpress.wordpress_post_provider import (
    WordPressPostProvider,
)
from socialflow.application.publishing.remote_post_provider import (
    RemotePostProvider,
)


def test_rejects_non_wordpress_account():
    retriever = Mock()
    credential_store = Mock()

    provider = WordPressPostProvider(
        retriever=retriever,
        credential_store=credential_store,
    )

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    with pytest.raises(
        ValueError,
        match="A WordPress account is required",
    ):
        provider.list_recent_posts(account)

    retriever.list_recent_posts.assert_not_called()
    credential_store.get.assert_not_called()

def test_retrieves_posts_using_stored_wordpress_credentials():
    from socialflow.domain.connections.wordpress_connection_config import (
        WordPressConnectionConfig,
    )
    from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
        WordPressCredentialKeys,
    )

    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    retriever = Mock()
    retriever.list_recent_posts.return_value = ()

    credential_store = Mock()
    credential_store.get.return_value = "test-application-password"

    provider = WordPressPostProvider(
        retriever=retriever,
        credential_store=credential_store,
    )

    posts = provider.list_recent_posts(
        account=account,
        limit=5,
    )

    assert posts == ()

    credential_store.get.assert_called_once_with(
        WordPressCredentialKeys.application_password(account)
    )

    retriever.list_recent_posts.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="test-application-password",
        limit=5,
    )

def test_rejects_missing_wordpress_application_password():
    from socialflow.domain.connections.wordpress_connection_config import (
        WordPressConnectionConfig,
    )

    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    retriever = Mock()
    credential_store = Mock()
    credential_store.get.return_value = None

    provider = WordPressPostProvider(
        retriever=retriever,
        credential_store=credential_store,
    )

    with pytest.raises(
        ValueError,
        match="WordPress application password is missing",
    ):
        provider.list_recent_posts(account)

    retriever.list_recent_posts.assert_not_called()


def test_converts_wordpress_posts_to_remote_posts():
    from datetime import datetime

    from socialflow.domain.connections.wordpress_connection_config import (
        WordPressConnectionConfig,
    )
    from socialflow.domain.post.remote_post import RemotePost
    from socialflow.infrastructure.wordpress.wordpress_post import (
        WordPressPost,
    )

    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    retriever = Mock()
    retriever.list_recent_posts.return_value = (
        WordPressPost(
            id=42,
            content="<p>Hello WordPress</p>",
            published_at=datetime(2026, 10, 14, 10, 30),
            status="publish",
            tag_ids=(12, 34),
        ),
    )

    credential_store = Mock()
    credential_store.get.return_value = "test-password"

    provider = WordPressPostProvider(
        retriever=retriever,
        credential_store=credential_store,
    )

    posts = provider.list_recent_posts(account)

    assert posts == (
        RemotePost(
            remote_id="42",
            destination=PublishingDestination.WORDPRESS,
            content="<p>Hello WordPress</p>",
            published_at=datetime(2026, 10, 14, 10, 30),
            status="publish",
            tag_ids=(12, 34),
        ),
    )

    assert isinstance(provider, RemotePostProvider)
