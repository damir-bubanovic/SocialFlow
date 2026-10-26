from datetime import datetime

from socialflow.infrastructure.wordpress.wordpress_post import (
    WordPressPost,
)


def test_wordpress_post_stores_remote_post_information():
    post = WordPressPost(
        id=42,
        content="<p>Hello WordPress</p>",
        published_at=datetime(2026, 10, 14, 10, 30),
        status="publish",
    )

    assert post.id == 42
    assert post.content == "<p>Hello WordPress</p>"
    assert post.published_at == datetime(2026, 10, 14, 10, 30)
    assert post.status == "publish"


def test_wordpress_post_is_immutable():
    from dataclasses import FrozenInstanceError

    import pytest

    post = WordPressPost(
        id=42,
        content="<p>Hello WordPress</p>",
        published_at=datetime(2026, 10, 14, 10, 30),
        status="publish",
    )

    with pytest.raises(FrozenInstanceError):
        setattr(post, "content", "Changed")

def test_wordpress_post_preserves_unicode_title():
    post = WordPressPost(
        id=42,
        content="Existing content",
        published_at=datetime(2026, 10, 26),
        status="publish",
        title="Naslov članka čćžšđ",
    )

    assert post.title == "Naslov članka čćžšđ"