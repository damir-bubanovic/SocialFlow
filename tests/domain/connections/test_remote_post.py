from datetime import datetime

from socialflow.domain.post.remote_post import RemotePost
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)


def test_remote_post_stores_platform_post_information():
    post = RemotePost(
        remote_id="42",
        destination=PublishingDestination.WORDPRESS,
        content="<p>Hello WordPress</p>",
        published_at=datetime(2026, 10, 14, 10, 30),
        status="publish",
    )

    assert post.remote_id == "42"
    assert post.destination == PublishingDestination.WORDPRESS
    assert post.content == "<p>Hello WordPress</p>"
    assert post.published_at == datetime(2026, 10, 14, 10, 30)
    assert post.status == "publish"


def test_remote_post_stores_existing_tag_ids():
    post = RemotePost(
        remote_id="42",
        destination=PublishingDestination.WORDPRESS,
        content="<p>Hello WordPress</p>",
        published_at=datetime(2026, 10, 14, 10, 30),
        status="publish",
        tag_ids=(12, 34),
    )

    assert post.tag_ids == (12, 34)


def test_remote_post_defaults_to_no_known_tags():
    post = RemotePost(
        remote_id="42",
        destination=PublishingDestination.WORDPRESS,
        content="<p>Hello WordPress</p>",
        published_at=datetime(2026, 10, 14, 10, 30),
        status="publish",
    )

    assert post.tag_ids == ()
