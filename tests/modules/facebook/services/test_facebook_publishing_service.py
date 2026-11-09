from typing import Mapping

import pytest

from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)
from socialflow.modules.facebook.api.facebook_graph_client import (
    FacebookGraphClient,
)
from socialflow.modules.facebook.api.facebook_http_transport import (
    FacebookHttpResponse,
    FacebookHttpTransport,
)
from socialflow.modules.facebook.services.facebook_publishing_service import (
    FacebookPublishingService,
)


class RecordingPublishingTransport(FacebookHttpTransport):
    def __init__(self) -> None:
        self.requests: list[
            tuple[str, dict[str, str], bytes, float]
        ] = []
        self.response_body = b'{"id":"123_456"}'
        self.status_code = 200

    def get(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> FacebookHttpResponse:
        raise NotImplementedError("GET is not supported.")

    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout: float,
    ) -> FacebookHttpResponse:
        self.requests.append(
            (url, dict(headers), body, timeout)
        )

        return FacebookHttpResponse(
            status_code=self.status_code,
            body=self.response_body,
        )


def test_publish_text_returns_facebook_post_id() -> None:
    transport = RecordingPublishingTransport()
    client = FacebookGraphClient(
        "v24.0",
        transport=transport,
    )
    service = FacebookPublishingService(client)

    post_id = service.publish_text(
        page_id="123",
        access_token="page-secret-token",
        message="Hello Facebook!",
    )

    assert post_id == "123_456"
    assert len(transport.requests) == 1

    url, headers, body, _timeout = transport.requests[0]

    assert url == "https://graph.facebook.com/v24.0/123/feed"
    assert headers["Authorization"] == "Bearer page-secret-token"
    assert body == b"message=Hello+Facebook%21"
    assert "page-secret-token" not in url


@pytest.mark.parametrize(
    "page_id",
    [
        "",
        "   ",
        "abc",
        "123/456",
        "../123",
        "123?access_token=secret",
        None,
        123,
    ],
)
def test_publish_text_rejects_invalid_page_id(page_id) -> None:
    transport = RecordingPublishingTransport()
    service = FacebookPublishingService(
        FacebookGraphClient("v24.0", transport=transport)
    )

    with pytest.raises(ValueError, match="Page ID"):
        service.publish_text(
            page_id=page_id,
            access_token="page-secret-token",
            message="Hello Facebook!",
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    "access_token",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_publish_text_rejects_invalid_access_token(
    access_token,
) -> None:
    transport = RecordingPublishingTransport()
    service = FacebookPublishingService(
        FacebookGraphClient("v24.0", transport=transport)
    )

    with pytest.raises(ValueError, match="access token"):
        service.publish_text(
            page_id="123",
            access_token=access_token,
            message="Hello Facebook!",
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
        "\n\t",
        None,
        123,
    ],
)
def test_publish_text_rejects_invalid_message(message) -> None:
    transport = RecordingPublishingTransport()
    service = FacebookPublishingService(
        FacebookGraphClient("v24.0", transport=transport)
    )

    with pytest.raises(ValueError, match="message"):
        service.publish_text(
            page_id="123",
            access_token="page-secret-token",
            message=message,
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    "response_body",
    [
        b"{}",
        b'{"id":null}',
        b'{"id":123}',
        b'{"id":""}',
        b'{"id":"   "}',
    ],
)
def test_publish_text_rejects_invalid_post_id(
    response_body: bytes,
) -> None:
    transport = RecordingPublishingTransport()
    transport.response_body = response_body

    service = FacebookPublishingService(
        FacebookGraphClient("v24.0", transport=transport)
    )

    with pytest.raises(ValueError, match="post ID"):
        service.publish_text(
            page_id="123",
            access_token="page-secret-token",
            message="Hello Facebook!",
        )

    assert len(transport.requests) == 1


def test_publish_text_preserves_structured_graph_api_error() -> None:
    transport = RecordingPublishingTransport()
    transport.status_code = 403
    transport.response_body = (
        b'{"error":{"message":"page-secret-token",'
        b'"type":"OAuthException","code":200}}'
    )

    service = FacebookPublishingService(
        FacebookGraphClient("v24.0", transport=transport)
    )

    with pytest.raises(FacebookApiError) as exc_info:
        service.publish_text(
            page_id="123",
            access_token="page-secret-token",
            message="Hello Facebook!",
        )

    error = exc_info.value

    assert error.status_code == 403
    assert error.code == 200
    assert error.error_type == "OAuthException"
    assert error.is_transient is False
    assert "page-secret-token" not in str(error)
    assert "page-secret-token" not in error.message
    assert len(transport.requests) == 1


def test_publish_text_preserves_transient_api_error() -> None:
    transport = RecordingPublishingTransport()
    transport.status_code = 503
    transport.response_body = b'{"error":{"code":4}}'

    service = FacebookPublishingService(
        FacebookGraphClient("v24.0", transport=transport)
    )

    with pytest.raises(FacebookApiError) as exc_info:
        service.publish_text(
            page_id="123",
            access_token="page-secret-token",
            message="Hello Facebook!",
        )

    error = exc_info.value

    assert error.status_code == 503
    assert error.is_transient is True
    assert len(transport.requests) == 1