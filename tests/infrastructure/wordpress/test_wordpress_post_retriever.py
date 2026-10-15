from datetime import datetime
from unittest.mock import Mock

from socialflow.infrastructure.wordpress.wordpress_post import (
    WordPressPost,
)
from socialflow.infrastructure.wordpress.wordpress_post_parser import (
    WordPressPostParser,
)
from socialflow.infrastructure.wordpress.wordpress_post_retriever import (
    WordPressPostRetriever,
)


def test_retrieves_and_parses_recent_wordpress_posts():
    client = Mock()
    client.list_recent_posts.return_value = [
        {
            "id": 42,
            "date": "2026-10-14T10:30:00",
            "content": {
                "rendered": "<p>Hello WordPress</p>",
            },
            "status": "publish",
        }
    ]

    retriever = WordPressPostRetriever(
        client=client,
        parser=WordPressPostParser(),
    )

    posts = retriever.list_recent_posts(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
        limit=5,
    )

    assert posts == (
        WordPressPost(
            id=42,
            content="<p>Hello WordPress</p>",
            published_at=datetime(2026, 10, 14, 10, 30),
            status="publish",
        ),
    )

    client.list_recent_posts.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
        limit=5,
    )


def test_returns_empty_tuple_when_wordpress_has_no_posts():
    client = Mock()
    client.list_recent_posts.return_value = []

    retriever = WordPressPostRetriever(
        client=client,
        parser=WordPressPostParser(),
    )

    posts = retriever.list_recent_posts(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
    )

    assert posts == ()