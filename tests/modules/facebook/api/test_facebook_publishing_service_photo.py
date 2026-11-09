
"""Tests for Facebook Page photo publishing."""

from pathlib import Path
from typing import Mapping, Any
from PIL import Image

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
from socialflow.modules.facebook.api.facebook_multipart_encoder import (
    MAX_MULTIPART_SIZE,
)
from socialflow.modules.facebook.api.facebook_publishing_service import (
    FacebookPublishingService,
)
from socialflow.modules.posts.models.image_attachment import (
    ImageAttachment,
)


class RecordingPhotoTransport(FacebookHttpTransport):
    def __init__(
        self,
        response_body: bytes = b'{"id":"123_789"}',
        status_code: int = 200,
    ) -> None:
        self.requests: list[
            tuple[str, dict[str, str], bytes, float]
        ] = []
        self.response_body = response_body
        self.status_code = status_code

    def get(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> FacebookHttpResponse:
        raise NotImplementedError

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


def make_service(
    transport: RecordingPhotoTransport,
) -> FacebookPublishingService:
    return FacebookPublishingService(
        FacebookGraphClient("v24.0", transport=transport)
    )


@pytest.mark.parametrize(
    "filename",
    ["photo.jpg", "photo.jpeg", "photo.png"],
)
def test_publish_photo_sends_multipart_request(
    tmp_path: Path,
    filename: str,
) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)
    attachment = make_attachment(tmp_path, filename)

    photo_id = service.publish_photo(
        page_id="123",
        access_token="secret-page-token",
        attachment=attachment,
        caption="My photo",
    )

    assert photo_id == "123_789"
    assert len(transport.requests) == 1

    url, headers, body, _timeout = transport.requests[0]

    assert url == "https://graph.facebook.com/v24.0/123/photos"
    assert headers["Authorization"] == "Bearer secret-page-token"
    assert headers["Content-Type"].startswith("multipart/form-data;")
    assert b"My photo" in body
    expected_extension = (
        ".png" if filename.lower().endswith(".png") else ".jpg"
    )
    assert f"facebook-photo{expected_extension}".encode() in body
    assert attachment.path.read_bytes() in body
    assert b"secret-page-token" not in body


def test_publish_photo_accepts_empty_caption(tmp_path: Path) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)

    result = service.publish_photo(
        "123",
        "token",
        make_attachment(tmp_path),
    )

    assert result == "123_789"


@pytest.mark.parametrize(
    "page_id",
    ["", "abc", "123/456", None],
)
def test_rejects_invalid_page_id(
    tmp_path: Path,
    page_id: Any,
) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)

    with pytest.raises(ValueError, match="Page ID"):
        service.publish_photo(
            page_id, "token", make_attachment(tmp_path)
        )

    assert transport.requests == []


@pytest.mark.parametrize("token", ["", "   ", None])
def test_rejects_invalid_token(
    tmp_path: Path,
    token: Any,
) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)

    with pytest.raises(ValueError, match="access token"):
        service.publish_photo(
            "123", token, make_attachment(tmp_path)
        )

    assert transport.requests == []



def test_rejects_invalid_caption(tmp_path: Path) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)

    invalid_caption: Any = None

    with pytest.raises(ValueError, match="caption"):
        service.publish_photo(
            "123",
            "token",
            make_attachment(tmp_path),
            caption=invalid_caption,
        )

    assert transport.requests == []



def test_rejects_webp(tmp_path: Path) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)

    with pytest.raises(ValueError, match="JPEG and PNG"):
        service.publish_photo(
            "123",
            "token",
            make_attachment(tmp_path, "photo.webp"),
        )

    assert transport.requests == []


def test_rejects_deleted_file(tmp_path: Path) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)
    attachment = make_attachment(tmp_path)
    attachment.path.unlink()

    with pytest.raises(ValueError, match="does not exist"):
        service.publish_photo("123", "token", attachment)

    assert transport.requests == []


def test_rejects_oversized_file(tmp_path: Path) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)

    path = tmp_path / "large.jpg"
    with path.open("wb") as file:
        file.truncate(MAX_MULTIPART_SIZE + 1)

    attachment = ImageAttachment(path=path)

    with pytest.raises(ValueError, match="size limit"):
        service.publish_photo("123", "token", attachment)

    assert transport.requests == []


def test_rejects_missing_photo_id(tmp_path: Path) -> None:
    transport = RecordingPhotoTransport(response_body=b"{}")
    service = make_service(transport)

    with pytest.raises(ValueError, match="photo ID"):
        service.publish_photo(
            "123", "token", make_attachment(tmp_path)
        )


def test_preserves_graph_api_error(tmp_path: Path) -> None:
    transport = RecordingPhotoTransport(
        status_code=400,
        response_body=(
            b'{"error":{"message":"Invalid token",'
            b'"type":"OAuthException","code":190}}'
        ),
    )
    service = make_service(transport)

    with pytest.raises(FacebookApiError) as exc_info:
        service.publish_photo(
            "123", "token", make_attachment(tmp_path)
        )

    assert exc_info.value.code == 190


def make_attachment(
    tmp_path: Path,
    filename: str = "photo.jpg",
) -> ImageAttachment:
    path = tmp_path / filename

    image_format = (
        "PNG" if path.suffix.lower() == ".png" else "JPEG"
    )

    Image.new("RGB", (10, 10)).save(
        path,
        format=image_format,
    )

    return ImageAttachment(path=path)


def test_rejects_invalid_image_before_http_request(
    tmp_path: Path,
) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)

    path = tmp_path / "invalid.jpg"
    path.write_bytes(b"not-a-real-jpeg")

    attachment = ImageAttachment(path=path)

    with pytest.raises(
        ValueError,
        match="invalid or corrupted image data",
    ):
        service.publish_photo(
            page_id="123",
            access_token="token",
            attachment=attachment,
            caption="Invalid image",
        )

    assert transport.requests == []


def test_rejects_mismatched_format_before_http_request(
    tmp_path: Path,
) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)

    path = tmp_path / "incorrect.jpg"
    Image.new("RGB", (10, 10)).save(
        path,
        format="PNG",
    )

    attachment = ImageAttachment(path=path)

    with pytest.raises(
        ValueError,
        match="does not match its extension",
    ):
        service.publish_photo(
            page_id="123",
            access_token="token",
            attachment=attachment,
            caption="Wrong format",
        )

    assert transport.requests == []


def test_upload_uses_validated_image_bytes(
    tmp_path: Path,
) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)
    attachment = make_attachment(tmp_path, "photo.png")

    original_data = attachment.path.read_bytes()

    result = service.publish_photo(
        page_id="123",
        access_token="token",
        attachment=attachment,
        caption="Validated image",
    )

    assert result == "123_789"
    assert len(transport.requests) == 1

    _url, _headers, body, _timeout = transport.requests[0]

    assert original_data in body


def test_rejects_truncated_image_before_http_request(
    tmp_path: Path,
) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)
    attachment = make_attachment(tmp_path, "photo.png")

    original_data = attachment.path.read_bytes()
    attachment.path.write_bytes(original_data[:20])

    with pytest.raises(
        ValueError,
        match="invalid or corrupted image data",
    ):
        service.publish_photo(
            page_id="123",
            access_token="token",
            attachment=attachment,
        )

    assert transport.requests == []


def test_rejects_image_with_wrong_content_format(
    tmp_path: Path,
) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)

    path = tmp_path / "wrong.png"

    Image.new("RGB", (10, 10)).save(
        path,
        format="JPEG",
    )

    attachment = ImageAttachment(path=path)

    with pytest.raises(
        ValueError,
        match="does not match its extension",
    ):
        service.publish_photo(
            page_id="123",
            access_token="token",
            attachment=attachment,
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    "filename",
    [
        "summer holiday.jpg",
        "obiteljska fotografija.png",
        "slika čćžšđ.jpg",
        "写真.png",
        "photo (final).jpeg",
        "image;special.jpg",
    ],
)
def test_publishes_images_with_unsafe_local_filenames(
    tmp_path: Path,
    filename: str,
) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)

    attachment = make_attachment(tmp_path, filename)

    photo_id = service.publish_photo(
        page_id="123",
        access_token="token",
        attachment=attachment,
        caption="Filename compatibility test",
    )

    assert photo_id == "123_789"
    assert len(transport.requests) == 1

    _url, _headers, body, _timeout = transport.requests[0]

    expected_extension = (
        ".png" if filename.lower().endswith(".png") else ".jpg"
    )
    expected_filename = f"facebook-photo{expected_extension}"

    assert expected_filename.encode("ascii") in body
    assert attachment.path.read_bytes() in body
    assert b"Filename compatibility test" in body


def test_publish_photo_defaults_to_published(
    tmp_path: Path,
) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)

    photo_id = service.publish_photo(
        page_id="123",
        access_token="token",
        attachment=make_attachment(tmp_path),
    )

    assert photo_id == "123_789"
    assert len(transport.requests) == 1

    _url, _headers, body, _timeout = transport.requests[0]

    assert b'name="published"' in body
    assert b"\r\n\r\ntrue\r\n" in body


def test_publish_photo_can_upload_unpublished_media(
    tmp_path: Path,
) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)

    photo_id = service.publish_photo(
        page_id="123",
        access_token="token",
        attachment=make_attachment(tmp_path),
        published=False,
    )

    assert photo_id == "123_789"
    assert len(transport.requests) == 1

    url, headers, body, _timeout = transport.requests[0]

    assert url.endswith("/123/photos")
    assert headers["Authorization"] == "Bearer token"
    assert b'name="published"' in body
    assert b"\r\n\r\nfalse\r\n" in body


@pytest.mark.parametrize(
    "invalid_value",
    [None, 0, 1, "false", "true", []],
)

def test_publish_photo_rejects_invalid_published_flag(
    tmp_path: Path,
    invalid_value: Any,
) -> None:
    transport = RecordingPhotoTransport()
    service = make_service(transport)

    with pytest.raises(ValueError, match="published flag"):
        service.publish_photo(
            page_id="123",
            access_token="token",
            attachment=make_attachment(tmp_path),
            published=invalid_value,
        )

    assert transport.requests == []
