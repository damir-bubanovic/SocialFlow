
"""Tests for Facebook photo deletion during publishing recovery."""

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
from socialflow.modules.facebook.api.facebook_publishing_service import (
    FacebookPublishingService,
)


class RecordingDeleteTransport(FacebookHttpTransport):
    def __init__(
        self,
        status_code: int = 200,
        body: bytes = b'{"success":true}',
    ) -> None:
        self.status_code = status_code
        self.body = body
        self.requests: list[
            tuple[str, dict[str, str], float]
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
        raise AssertionError("Unexpected POST request.")

    def delete(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> FacebookHttpResponse:
        self.requests.append(
            (url, dict(headers), timeout)
        )

        return FacebookHttpResponse(
            status_code=self.status_code,
            body=self.body,
        )


def make_service(
    transport: RecordingDeleteTransport,
) -> FacebookPublishingService:
    return FacebookPublishingService(
        FacebookGraphClient(
            "v24.0",
            transport=transport,
        )
    )


def test_deletes_unpublished_photo() -> None:
    transport = RecordingDeleteTransport()
    service = make_service(transport)

    service.delete_unpublished_photo(
        photo_id="123456",
        access_token="secret-token",
    )
    assert len(transport.requests) == 1

    url, headers, timeout = transport.requests[0]

    assert url == "https://graph.facebook.com/v24.0/123456"
    assert headers["Authorization"] == "Bearer secret-token"
    assert headers["Accept"] == "application/json"
    assert timeout == 10.0
    assert "secret-token" not in url


@pytest.mark.parametrize(
    "invalid_photo_id",
    [
        "",
        " ",
        "abc",
        "123/456",
        "../123",
        None,
        123,
    ],
)
def test_rejects_invalid_photo_id_before_http(
    invalid_photo_id: object,
) -> None:
    transport = RecordingDeleteTransport()
    service = make_service(transport)

    with pytest.raises(ValueError, match="photo ID"):
        service.delete_unpublished_photo(
            photo_id=invalid_photo_id,  # type: ignore[arg-type]
            access_token="token",
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    "invalid_token",
    ["", "   ", None, 123],
)
def test_rejects_invalid_token_before_http(
    invalid_token: object,
) -> None:
    transport = RecordingDeleteTransport()
    service = make_service(transport)

    with pytest.raises(ValueError, match="access token"):
        service.delete_unpublished_photo(
            photo_id="123456",
            access_token=invalid_token,  # type: ignore[arg-type]
        )

    assert transport.requests == []


@pytest.mark.parametrize(
    "response_body",
    [
        b'{"success":false}',
        b'{"success":null}',
        b'{"success":1}',
        b'{}',
    ],
)
def test_requires_explicit_deletion_confirmation(
    response_body: bytes,
) -> None:
    transport = RecordingDeleteTransport(body=response_body)
    service = make_service(transport)

    with pytest.raises(ValueError, match="confirm photo deletion"):
        service.delete_unpublished_photo(
            photo_id="123456",
            access_token="token",
        )

    assert len(transport.requests) == 1


def test_preserves_graph_api_deletion_error() -> None:
    transport = RecordingDeleteTransport(
        status_code=403,
        body=b'{"error":{"message":"Denied","code":200}}',
    )
    service = make_service(transport)

    with pytest.raises(FacebookApiError) as exc_info:
        service.delete_unpublished_photo(
            photo_id="123456",
            access_token="secret-token",
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == 200
    assert "secret-token" not in str(exc_info.value)
    assert len(transport.requests) == 1
