
"""Tests for Graph API multipart image uploads."""

from typing import Mapping
from urllib.error import URLError

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


class RecordingMultipartTransport(FacebookHttpTransport):
    def __init__(
        self,
        failure: Exception | None = None,
        status: int = 200,
        response_body: bytes = b'{"id":"123_456"}',
    ) -> None:
        self.requests: list[
            tuple[str, dict[str, str], bytes, float]
        ] = []
        self.failure = failure
        self.status = status
        self.response_body = response_body

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

        if self.failure is not None:
            raise self.failure

        return FacebookHttpResponse(
            status_code=self.status,
            body=self.response_body,
        )


def test_multipart_upload_uses_bearer_auth() -> None:
    transport = RecordingMultipartTransport()
    client = FacebookGraphClient(
        "v24.0",
        transport=transport,
        timeout=7.5,
    )

    result = client.post_multipart(
        path="123/photos",
        access_token="secret-page-token",
        fields={"caption": "Hello Facebook"},
        filename="photo.jpg",
        image_data=b"\xff\xd8image-data",
    )

    assert result == {"id": "123_456"}
    assert len(transport.requests) == 1

    url, headers, body, timeout = transport.requests[0]

    assert url == "https://graph.facebook.com/v24.0/123/photos"
    assert headers["Authorization"] == "Bearer secret-page-token"
    assert headers["Accept"] == "application/json"
    assert headers["Content-Type"].startswith(
        "multipart/form-data; boundary="
    )
    assert b"Hello Facebook" in body
    assert b"photo.jpg" in body
    assert b"\xff\xd8image-data" in body
    assert b"secret-page-token" not in body
    assert "secret-page-token" not in url
    assert timeout == 7.5


@pytest.mark.parametrize(
    "path",
    [
        "",
        "/123/photos",
        "123/photos?token=secret",
        "123//photos",
        "123/../photos",
        "123/photos/",
    ],
)
def test_multipart_rejects_invalid_paths(path: str) -> None:
    transport = RecordingMultipartTransport()
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(ValueError):
        client.post_multipart(
            path, "token", {}, "photo.jpg", b"image"
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    "fields",
    [
        {"access_token": "secret"},
        {"ACCESS_TOKEN": "secret"},
        {"message": 123},
        {"source": "duplicate"},
    ],
)
def test_multipart_rejects_invalid_fields(fields: dict) -> None:
    transport = RecordingMultipartTransport()
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(ValueError):
        client.post_multipart(
            "123/photos", "token", fields, "photo.jpg", b"image"
        )

    assert transport.requests == []


@pytest.mark.parametrize("token", ["", "   ", None])
def test_multipart_rejects_invalid_tokens(token: str | None) -> None:
    transport = RecordingMultipartTransport()
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(ValueError):
        client.post_multipart(
            "123/photos", token, {}, "photo.jpg", b"image"
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    "failure",
    [
        TimeoutError("timeout"),
        URLError("connection failed"),
        OSError("network unavailable"),
    ],
)
def test_multipart_network_failures_are_transient(
    failure: Exception,
) -> None:
    transport = RecordingMultipartTransport(failure=failure)
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(FacebookApiError) as exc_info:
        client.post_multipart(
            "123/photos", "token", {}, "photo.jpg", b"image"
        )

    assert exc_info.value.is_transient is True


def test_multipart_preserves_graph_api_errors() -> None:
    transport = RecordingMultipartTransport(
        status=400,
        response_body=(
            b'{"error":{"message":"Invalid OAuth access token.",'
            b'"type":"OAuthException","code":190}}'
        ),
    )
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(FacebookApiError) as exc_info:
        client.post_multipart(
            "123/photos", "token", {}, "photo.jpg", b"image"
        )

    assert exc_info.value.code == 190
    assert exc_info.value.status_code == 400
