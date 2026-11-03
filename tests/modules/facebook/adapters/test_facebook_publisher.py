from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.services.facebook_credential_keys import (
    FacebookCredentialKeys,
)
from socialflow.modules.facebook.adapters.facebook_publisher import (
    FacebookPublisher,
)
from socialflow.modules.posts.models.language import Language
from socialflow.modules.posts.models.post import Post
from socialflow.modules.posts.services.prepared_post import PreparedPost
from socialflow.modules.posts.services.errors import (
    PublisherNotConfiguredError,
)


def make_account():
    config = Mock()
    config.is_complete.return_value = True
    config.normalized.return_value = SimpleNamespace(
        page_id="123456789",
        page_name="Test Facebook Page",
    )

    return SimpleNamespace(
        id="test-facebook-account",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=config,
    )


def make_post(text: str = "Hello Facebook!") -> PreparedPost:
    return PreparedPost(
        source=Post(
            text=text,
            language=Language.ENGLISH,
        )
    )


def make_publisher(
    account=None,
    token: str | None = "page-secret-token",
):
    account = account if account is not None else make_account()

    credentials = Mock()
    credentials.get.return_value = token

    publishing_service = Mock()

    publisher = FacebookPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    return publisher, credentials, publishing_service


def test_successful_facebook_publication() -> None:
    publisher, credentials, service = make_publisher()

    publisher.publish(make_post())

    credentials.get.assert_called_once_with(
        FacebookCredentialKeys.page_access_token(
            publisher._account
        )
    )

    service.publish_text.assert_called_once_with(
        page_id="123456789",
        access_token="page-secret-token",
        message="Hello Facebook!",
    )

def test_rejects_missing_facebook_configuration() -> None:
    account = make_account()
    account.facebook_config = None

    publisher, credentials, service = make_publisher(
        account=account,
    )

    with pytest.raises(
            PublisherNotConfiguredError,
            match="Facebook Page connection settings are incomplete",
    ):
        publisher.publish(make_post())

    credentials.get.assert_not_called()
    service.publish_text.assert_not_called()


def test_rejects_incomplete_facebook_configuration() -> None:
    account = make_account()
    account.facebook_config.is_complete.return_value = False

    publisher, credentials, service = make_publisher(
        account=account,
    )

    with pytest.raises(
            PublisherNotConfiguredError,
            match="Facebook Page connection settings are incomplete",
    ):
        publisher.publish(make_post())

    credentials.get.assert_not_called()
    service.publish_text.assert_not_called()


@pytest.mark.parametrize("token", [None, "", "   "])
def test_rejects_missing_facebook_access_token(token) -> None:
    publisher, credentials, service = make_publisher(
        token=token,
    )

    with pytest.raises(
        ValueError,
        match="Facebook Page access token is missing",
    ):
        publisher.publish(make_post())

    credentials.get.assert_called_once()
    service.publish_text.assert_not_called()

def test_rejects_source_images() -> None:
    publisher, credentials, service = make_publisher()

    post = PreparedPost(
        source=Post(
            text="Hello Facebook!",
            language=Language.ENGLISH,
            images=(Mock(),),
        )
    )

    with pytest.raises(
        ValueError,
        match="Facebook image publishing is not supported yet",
    ):
        publisher.publish(post)

    credentials.get.assert_not_called()
    service.publish_text.assert_not_called()


def test_rejects_prepared_images() -> None:
    publisher, credentials, service = make_publisher()

    post = PreparedPost(
        source=Post(
            text="Hello Facebook!",
            language=Language.ENGLISH,
        ),
        images=(Mock(),),
    )

    with pytest.raises(
        ValueError,
        match="Facebook image publishing is not supported yet",
    ):
        publisher.publish(post)

    credentials.get.assert_not_called()
    service.publish_text.assert_not_called()


def test_rejects_facebook_tags() -> None:
    publisher, credentials, service = make_publisher()

    post = PreparedPost(
        source=Post(
            text="Hello Facebook!",
            language=Language.ENGLISH,
            tags=(Mock(),),
        )
    )

    with pytest.raises(
        ValueError,
        match="Facebook tag publishing is not supported yet",
    ):
        publisher.publish(post)

    credentials.get.assert_not_called()
    service.publish_text.assert_not_called()

@pytest.mark.parametrize("text", ["", " ", "   \t\n"])
def test_rejects_empty_facebook_post_text(text: str) -> None:
    publisher, credentials, service = make_publisher()

    with pytest.raises(
        ValueError,
        match="Facebook post text is required",
    ):
        publisher.publish(make_post(text=text))

    credentials.get.assert_not_called()
    service.publish_text.assert_not_called()


def test_propagates_facebook_publishing_error() -> None:
    publisher, credentials, service = make_publisher()

    service.publish_text.side_effect = RuntimeError(
        "Facebook publishing failed."
    )

    with pytest.raises(
        RuntimeError,
        match="Facebook publishing failed",
    ):
        publisher.publish(make_post())

    credentials.get.assert_called_once()
    service.publish_text.assert_called_once_with(
        page_id="123456789",
        access_token="page-secret-token",
        message="Hello Facebook!",
    )

def test_rejects_non_facebook_account() -> None:
    account = make_account()
    account.destination = PublishingDestination.WORDPRESS

    with pytest.raises(
        ValueError,
        match="A Facebook account is required",
    ):
        make_publisher(account=account)