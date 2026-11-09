
"""Tests for creating a Facebook Page post from uploaded photos."""

import json
from typing import Any, Mapping
from urllib.parse import parse_qs

import pytest

from socialflow.modules.facebook.api.facebook_graph_client import (
    FacebookGraphClient,
)
from socialflow.modules.facebook.api.facebook_http_transport import (
    FacebookHttpResponse,
    FacebookHttpTransport,
)
from socialflow.modules.facebook.api.facebook_publishing_service import (
    FacebookPublishingService,
)


class RecordingAlbumTransport(FacebookHttpTransport):
    def __init__(
        self,
        response_body: bytes = b'{"id":"123_456"}',
    ) -> None:
        self.response_body = response_body
        self.requests: list[
            tuple[str, dict[str, str], bytes, float]
        ] = []

    def get(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> FacebookHttpResponse:
        raise AssertionError("Unexpected GET request.")

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
            status_code=200,
            body=self.response_body,
        )


def make_service(
    transport: RecordingAlbumTransport,
) -> FacebookPublishingService:
    return FacebookPublishingService(
        FacebookGraphClient(
            "v24.0",
            transport=transport,
        )
    )


def test_creates_one_feed_post_with_multiple_photos() -> None:
    transport = RecordingAlbumTransport()
    service = make_service(transport)

    post_id = service.publish_photo_album(
        page_id="123",
        access_token="secret-token",
        message="Holiday photos",
        photo_ids=("111", "222", "333"),
    )

    assert post_id == "123_456"
    assert len(transport.requests) == 1

    url, headers, body, _timeout = transport.requests[0]

    assert url == "https://graph.facebook.com/v24.0/123/feed"
    assert headers["Authorization"] == "Bearer secret-token"
    assert headers["Content-Type"] == (
        "application/x-www-form-urlencoded"
    )

    fields = parse_qs(body.decode("utf-8"))

    assert fields["message"] == ["Holiday photos"]

    for index, photo_id in enumerate(("111", "222", "333")):
        assert json.loads(
            fields[f"attached_media[{index}]"][0]
        ) == {"media_fbid": photo_id}

    assert "secret-token" not in url
    assert b"secret-token" not in body


def test_allows_empty_message_with_photos() -> None:
    transport = RecordingAlbumTransport()
    service = make_service(transport)

    result = service.publish_photo_album(
        page_id="123",
        access_token="token",
        message="",
        photo_ids=("111", "222"),
    )

    assert result == "123_456"
    assert len(transport.requests) == 1


@pytest.mark.parametrize(
    "photo_ids",
    [
        (),
        ("111",),
        ("111", "111"),
        ("111", ""),
        ("111", "abc"),
        ("111", " 222"),
        ("111", "222/333"),
    ],
)
def test_rejects_invalid_photo_ids(
    photo_ids: tuple[str, ...],
) -> None:
    transport = RecordingAlbumTransport()
    service = make_service(transport)

    with pytest.raises(ValueError):
        service.publish_photo_album(
            page_id="123",
            access_token="token",
            message="Photos",
            photo_ids=photo_ids,
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    "invalid_ids",
    [
        None,
        ["111", "222"],
        ("111", 222),
    ],
)
def test_rejects_invalid_photo_id_types(
    invalid_ids: Any,
) -> None:
    transport = RecordingAlbumTransport()
    service = make_service(transport)

    with pytest.raises(ValueError):
        service.publish_photo_album(
            page_id="123",
            access_token="token",
            message="Photos",
            photo_ids=invalid_ids,
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    "page_id",
    ["", "abc", "123/456", None],
)
def test_rejects_invalid_page_id(
    page_id: Any,
) -> None:
    transport = RecordingAlbumTransport()
    service = make_service(transport)

    with pytest.raises(ValueError, match="Page ID"):
        service.publish_photo_album(
            page_id=page_id,
            access_token="token",
            message="Photos",
            photo_ids=("111", "222"),
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    "token",
    ["", "   ", None],
)
def test_rejects_invalid_token(
    token: Any,
) -> None:
    transport = RecordingAlbumTransport()
    service = make_service(transport)

    with pytest.raises(ValueError, match="access token"):
        service.publish_photo_album(
            page_id="123",
            access_token=token,
            message="Photos",
            photo_ids=("111", "222"),
        )

    assert transport.requests == []


def test_rejects_invalid_message() -> None:
    transport = RecordingAlbumTransport()
    service = make_service(transport)

    with pytest.raises(ValueError, match="message"):
        service.publish_photo_album(
            page_id="123",
            access_token="token",
            message=None,  # type: ignore[arg-type]
            photo_ids=("111", "222"),
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
def test_rejects_invalid_post_id(
    response_body: bytes,
) -> None:
    transport = RecordingAlbumTransport(response_body)
    service = make_service(transport)

    with pytest.raises(ValueError, match="post ID"):
        service.publish_photo_album(
            page_id="123",
            access_token="token",
            message="Photos",
            photo_ids=("111", "222"),
        )

    assert len(transport.requests) == 1
