
"""Tests for multiple-photo Facebook publishing orchestration."""

from pathlib import Path
from typing import Mapping
from urllib.parse import parse_qs

import pytest
from PIL import Image

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
from socialflow.modules.posts.models.image_attachment import (
    ImageAttachment,
)


class RecordingMultiplePhotoTransport(FacebookHttpTransport):
    def __init__(self, fail_on_request: int | None = None) -> None:
        self.requests: list[
            tuple[str, dict[str, str], bytes, float]
        ] = []
        self.fail_on_request = fail_on_request

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
        self.requests.append((url, dict(headers), body, timeout))
        request_number = len(self.requests)

        if request_number == self.fail_on_request:
            return FacebookHttpResponse(
                status_code=400,
                body=b'{"error":{"message":"Upload failed","code":100}}',
            )

        if url.endswith("/photos"):
            response_body = (
                f'{{"id":"{1000 + request_number}"}}'.encode()
            )
        elif url.endswith("/feed"):
            response_body = b'{"id":"123_999"}'
        else:
            raise AssertionError(f"Unexpected endpoint: {url}")

        return FacebookHttpResponse(
            status_code=200,
            body=response_body,
        )


def make_service(
    transport: RecordingMultiplePhotoTransport,
) -> FacebookPublishingService:
    return FacebookPublishingService(
        FacebookGraphClient("v24.0", transport=transport)
    )


def make_attachments(
    tmp_path: Path,
    count: int,
) -> tuple[ImageAttachment, ...]:
    attachments = []

    for index in range(count):
        path = tmp_path / f"photo-{index}.jpg"
        Image.new("RGB", (20, 20)).save(path, format="JPEG")
        attachments.append(ImageAttachment(path=path))

    return tuple(attachments)


def test_uploads_three_photos_then_creates_one_post(
    tmp_path: Path,
) -> None:
    transport = RecordingMultiplePhotoTransport()
    service = make_service(transport)

    result = service.publish_multiple_photos(
        page_id="123",
        access_token="secret-token",
        attachments=make_attachments(tmp_path, 3),
        message="Three photos",
    )

    assert result == "123_999"
    assert len(transport.requests) == 4

    for url, headers, body, _timeout in transport.requests[:3]:
        assert url.endswith("/123/photos")
        assert headers["Authorization"] == "Bearer secret-token"
        assert b'name="published"' in body
        assert b"\r\n\r\nfalse\r\n" in body

    feed_url, _headers, feed_body, _timeout = transport.requests[3]
    assert feed_url.endswith("/123/feed")

    fields = parse_qs(feed_body.decode())
    assert fields["message"] == ["Three photos"]
    assert len(
        [key for key in fields if key.startswith("attached_media[")]
    ) == 3


@pytest.mark.parametrize("failure_number", [1, 2, 3])
def test_upload_failure_prevents_feed_post(
    tmp_path: Path,
    failure_number: int,
) -> None:
    transport = RecordingMultiplePhotoTransport(
        fail_on_request=failure_number,
    )
    service = make_service(transport)

    with pytest.raises(Exception):
        service.publish_multiple_photos(
            page_id="123",
            access_token="token",
            attachments=make_attachments(tmp_path, 3),
            message="Photos",
        )

    assert len(transport.requests) == failure_number
    assert all(
        url.endswith("/photos")
        for url, _headers, _body, _timeout in transport.requests
    )


def test_rejects_single_image_before_http(
    tmp_path: Path,
) -> None:
    transport = RecordingMultiplePhotoTransport()
    service = make_service(transport)

    with pytest.raises(ValueError, match="At least two"):
        service.publish_multiple_photos(
            page_id="123",
            access_token="token",
            attachments=make_attachments(tmp_path, 1),
        )

    assert transport.requests == []


def test_rejects_invalid_image_before_http(
    tmp_path: Path,
) -> None:
    transport = RecordingMultiplePhotoTransport()
    service = make_service(transport)

    attachments = list(make_attachments(tmp_path, 2))
    attachments[1].path.unlink()

    with pytest.raises(ValueError):
        service.publish_multiple_photos(
            page_id="123",
            access_token="token",
            attachments=tuple(attachments),
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    "invalid_page_id",
    ["", "   ", "abc", "123/456", None, 123],
)
def test_rejects_invalid_page_id_before_upload(
    tmp_path: Path,
    invalid_page_id: object,
) -> None:
    transport = RecordingMultiplePhotoTransport()
    service = make_service(transport)

    with pytest.raises(ValueError, match="Page ID"):
        service.publish_multiple_photos(
            page_id=invalid_page_id,  # type: ignore[arg-type]
            access_token="token",
            attachments=make_attachments(tmp_path, 2),
            message="Photos",
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    "invalid_token",
    ["", "   ", None, 123],
)
def test_rejects_invalid_token_before_upload(
    tmp_path: Path,
    invalid_token: object,
) -> None:
    transport = RecordingMultiplePhotoTransport()
    service = make_service(transport)

    with pytest.raises(ValueError, match="access token"):
        service.publish_multiple_photos(
            page_id="123",
            access_token=invalid_token,  # type: ignore[arg-type]
            attachments=make_attachments(tmp_path, 2),
            message="Photos",
        )

    assert transport.requests == []


def test_accepts_ten_photos(
    tmp_path: Path,
) -> None:
    transport = RecordingMultiplePhotoTransport()
    service = make_service(transport)

    result = service.publish_multiple_photos(
        page_id="123",
        access_token="token",
        attachments=make_attachments(tmp_path, 10),
        message="Ten photos",
    )

    assert result == "123_999"

    # Ten unpublished photo uploads plus one feed post.
    assert len(transport.requests) == 11

    assert all(
        url.endswith("/photos")
        for url, _headers, _body, _timeout in transport.requests[:10]
    )

    assert transport.requests[-1][0].endswith("/feed")


def test_rejects_eleven_photos_before_http(
    tmp_path: Path,
) -> None:
    transport = RecordingMultiplePhotoTransport()
    service = make_service(transport)

    with pytest.raises(ValueError, match="at most 10 photos"):
        service.publish_multiple_photos(
            page_id="123",
            access_token="token",
            attachments=make_attachments(tmp_path, 11),
            message="Too many photos",
        )

    assert transport.requests == []


def test_failed_upload_cleans_up_previous_photos_in_reverse_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = RecordingMultiplePhotoTransport(fail_on_request=3)
    service = make_service(transport)
    deleted_ids: list[str] = []

    def record_delete(photo_id: str, access_token: str) -> None:
        assert access_token == "token"
        deleted_ids.append(photo_id)

    monkeypatch.setattr(
        service,
        "delete_unpublished_photo",
        record_delete,
    )

    with pytest.raises(Exception):
        service.publish_multiple_photos(
            page_id="123",
            access_token="token",
            attachments=make_attachments(tmp_path, 3),
            message="Photos",
        )

    assert deleted_ids == ["1002", "1001"]
    assert len(transport.requests) == 3
    assert all(
        url.endswith("/photos")
        for url, _headers, _body, _timeout in transport.requests
    )


def test_cleanup_failure_preserves_original_upload_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = RecordingMultiplePhotoTransport(fail_on_request=3)
    service = make_service(transport)
    deleted_ids: list[str] = []

    def failing_delete(photo_id: str, access_token: str) -> None:
        assert access_token == "token"
        deleted_ids.append(photo_id)
        raise RuntimeError("Cleanup failed")

    monkeypatch.setattr(
        service,
        "delete_unpublished_photo",
        failing_delete,
    )

    with pytest.raises(
            Exception,
            match=r"Facebook API request failed, HTTP 400, code 100",
    ):
        service.publish_multiple_photos(
            page_id="123",
            access_token="token",
            attachments=make_attachments(tmp_path, 3),
        )

    assert deleted_ids == ["1002", "1001"]
    assert len(transport.requests) == 3


def test_feed_failure_does_not_delete_uploaded_photos(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transport = RecordingMultiplePhotoTransport(fail_on_request=4)
    service = make_service(transport)
    deleted_ids: list[str] = []

    def record_delete(photo_id: str, access_token: str) -> None:
        assert access_token == "token"
        deleted_ids.append(photo_id)

    monkeypatch.setattr(
        service,
        "delete_unpublished_photo",
        record_delete,
    )

    with pytest.raises(Exception):
        service.publish_multiple_photos(
            page_id="123",
            access_token="token",
            attachments=make_attachments(tmp_path, 3),
        )

    assert deleted_ids == []
    assert len(transport.requests) == 4
    assert transport.requests[-1][0].endswith("/feed")
