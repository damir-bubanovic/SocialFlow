
"""Cross-layer integration tests for Facebook multiple-photo publishing."""

import json
from pathlib import Path
from urllib.parse import parse_qs
from unittest.mock import Mock

from PIL import Image

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.facebook_page_config import (
    FacebookPageConfig,
)
from socialflow.modules.accounts.services.facebook_credential_keys import (
    FacebookCredentialKeys,
)
from socialflow.modules.facebook.adapters.facebook_publisher import (
    FacebookPublisher,
)
from socialflow.modules.facebook.api.facebook_graph_client import (
    FacebookGraphClient,
)
from socialflow.modules.facebook.api.facebook_http_transport import (
    FacebookHttpResponse,
)
from socialflow.modules.facebook.api.facebook_publishing_service import (
    FacebookPublishingService,
)
from socialflow.modules.posts.models.image_attachment import (
    ImageAttachment,
)
from socialflow.modules.posts.models.language import Language
from socialflow.modules.posts.models.post import Post
from socialflow.modules.posts.services.prepared_post import PreparedPost
import pytest

from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)


def test_multiple_photo_publishing_uses_two_uploads_and_one_feed_post(
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "first.jpg"
    second_path = tmp_path / "second.jpg"

    Image.new("RGB", (100, 100), color="red").save(first_path)
    Image.new("RGB", (100, 100), color="blue").save(second_path)

    first = ImageAttachment(path=first_path)
    second = ImageAttachment(path=second_path)

    account = Account(
        name="Test Facebook Page",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="123456789",
            page_name="Test Facebook Page",
        ),
    )

    credentials = Mock()
    credentials.get.return_value = "test-page-token"

    transport = Mock()
    transport.post.side_effect = [
        FacebookHttpResponse(
            status_code=200,
            body=b'{"id":"1001"}',
        ),
        FacebookHttpResponse(
            status_code=200,
            body=b'{"id":"1002"}',
        ),
        FacebookHttpResponse(
            status_code=200,
            body=b'{"id":"123456789_9999"}',
        ),
    ]

    graph_client = FacebookGraphClient(
        api_version="v24.0",
        transport=transport,
    )
    publishing_service = FacebookPublishingService(
        client=graph_client,
    )
    publisher = FacebookPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    publisher.publish(
        PreparedPost(
            source=Post(
                text="Two Facebook photos",
                language=Language.ENGLISH,
                images=(first, second),
            )
        )
    )

    credentials.get.assert_called_once_with(
        FacebookCredentialKeys.page_access_token(account)
    )

    assert transport.post.call_count == 3
    transport.delete.assert_not_called()

    requests = [
        call.kwargs
        for call in transport.post.call_args_list
    ]

    photos_url = (
        "https://graph.facebook.com/v24.0/123456789/photos"
    )
    feed_url = (
        "https://graph.facebook.com/v24.0/123456789/feed"
    )

    assert [request["url"] for request in requests] == [
        photos_url,
        photos_url,
        feed_url,
    ]

    for request in requests:
        assert request["headers"]["Authorization"] == (
            "Bearer test-page-token"
        )
        assert "test-page-token" not in request["url"]

    for request in requests[:2]:
        assert request["headers"]["Content-Type"].startswith(
            "multipart/form-data;"
        )
        assert b'name="published"' in request["body"]
        assert b"false" in request["body"]

    feed_request = requests[2]

    assert feed_request["headers"]["Content-Type"] == (
        "application/x-www-form-urlencoded"
    )

    params = parse_qs(
        feed_request["body"].decode("utf-8")
    )

    assert params["message"] == ["Two Facebook photos"]

    assert json.loads(params["attached_media[0]"][0]) == {
        "media_fbid": "1001"
    }
    assert json.loads(params["attached_media[1]"][0]) == {
        "media_fbid": "1002"
    }


def test_failed_third_upload_cleans_up_previous_photos(
    tmp_path: Path,
) -> None:
    image_paths = [
        tmp_path / f"photo-{index}.jpg"
        for index in range(3)
    ]

    for path in image_paths:
        Image.new("RGB", (100, 100), color="red").save(path)

    attachments = tuple(
        ImageAttachment(path=path)
        for path in image_paths
    )

    account = Account(
        name="Test Facebook Page",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="123456789",
            page_name="Test Facebook Page",
        ),
    )

    credentials = Mock()
    credentials.get.return_value = "test-page-token"

    transport = Mock()
    transport.post.side_effect = [
        FacebookHttpResponse(
            status_code=200,
            body=b'{"id":"1001"}',
        ),
        FacebookHttpResponse(
            status_code=200,
            body=b'{"id":"1002"}',
        ),
        FacebookHttpResponse(
            status_code=400,
            body=(
                b'{"error":{"message":"Sensitive upload error",'
                b'"type":"OAuthException","code":100}}'
            ),
        ),
    ]
    transport.delete.return_value = FacebookHttpResponse(
        status_code=200,
        body=b'{"success":true}',
    )

    graph_client = FacebookGraphClient(
        api_version="v24.0",
        transport=transport,
    )
    publishing_service = FacebookPublishingService(
        client=graph_client,
    )
    publisher = FacebookPublisher(
        account=account,
        credential_store=credentials,
        publishing_service=publishing_service,
    )

    post = PreparedPost(
        source=Post(
            text="Three Facebook photos",
            language=Language.ENGLISH,
            images=attachments,
        )
    )

    with pytest.raises(FacebookApiError) as error:
        publisher.publish(post)

    assert error.value.status_code == 400
    assert error.value.code == 100

    error_text = str(error.value)
    assert "Facebook API request failed" in error_text
    assert "test-page-token" not in error_text
    assert "Sensitive upload error" not in error_text

    credentials.get.assert_called_once_with(
        FacebookCredentialKeys.page_access_token(account)
    )

    assert transport.post.call_count == 3
    assert transport.delete.call_count == 2

    photos_url = (
        "https://graph.facebook.com/v24.0/123456789/photos"
    )

    assert [
        call.kwargs["url"]
        for call in transport.post.call_args_list
    ] == [
        photos_url,
        photos_url,
        photos_url,
    ]

    assert [
        call.kwargs["url"]
        for call in transport.delete.call_args_list
    ] == [
        "https://graph.facebook.com/v24.0/1002",
        "https://graph.facebook.com/v24.0/1001",
    ]

    for call in transport.delete.call_args_list:
        assert call.kwargs["headers"]["Authorization"] == (
            "Bearer test-page-token"
        )
        assert "test-page-token" not in call.kwargs["url"]

    assert all(
        "/feed" not in call.kwargs["url"]
        for call in transport.post.call_args_list
    )
