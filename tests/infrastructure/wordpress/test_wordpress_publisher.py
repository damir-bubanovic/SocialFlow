from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_publisher import (
    WordPressPublisher,
)
from socialflow.application.publishing.prepared_post import PreparedPost
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post


def make_account(
    site_url="https://example.com",
    username="admin",
):
    config = Mock()
    config.is_complete.return_value = True
    config.normalized.return_value = SimpleNamespace(
        site_url=site_url,
        username=username,
    )

    return SimpleNamespace(
        id="test-wordpress-account",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=config,
    )


def make_post(text: str = "Hello WordPress") -> PreparedPost:
    post = Post(
        text=text,
        language=Language.ENGLISH,
    )

    return PreparedPost(source=post)


def make_publisher(
    account=None,
    password: str | None = "secret",
    status: int = 201,
):
    account = account or make_account()

    credentials = Mock()
    credentials.get.return_value = password

    client = Mock()
    client.create_post.return_value = status

    publisher = WordPressPublisher(
        account=account,
        credential_store=credentials,
        post_client=client,
    )

    return publisher, credentials, client


def test_successful_wordpress_publication():
    publisher, credentials, client = make_publisher()

    publisher.publish(make_post())

    client.create_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
        content="Hello WordPress",
    )


def test_missing_application_password():
    publisher, credentials, client = make_publisher(password=None)

    with pytest.raises(ValueError, match="password is missing"):
        publisher.publish(make_post())

    client.create_post.assert_not_called()


def test_rejects_http_failure():
    publisher, credentials, client = make_publisher(status=401)

    with pytest.raises(RuntimeError, match="HTTP 401"):
        publisher.publish(make_post())


def test_rejects_insecure_wordpress_url():
    publisher, credentials, client = make_publisher(
        account=make_account(site_url="http://example.com")
    )

    with pytest.raises(ValueError, match="HTTPS"):
        publisher.publish(make_post())

    client.create_post.assert_not_called()


def test_rejects_unsupported_images():
    publisher, credentials, client = make_publisher()

    post = PreparedPost(
        source=Post(
            text="Hello WordPress",
            language=Language.ENGLISH,
        ),
        images=(Mock(),),
    )

    with pytest.raises(ValueError, match="images and tags"):
        publisher.publish(post)

    client.create_post.assert_not_called()


def test_rejects_empty_post():
    publisher, credentials, client = make_publisher()

    with pytest.raises(ValueError, match="post text is required"):
        publisher.publish(make_post(text="   "))

    client.create_post.assert_not_called()
