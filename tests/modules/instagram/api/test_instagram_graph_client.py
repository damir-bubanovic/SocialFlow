from typing import Mapping
from urllib.parse import parse_qs, urlsplit

import pytest

from socialflow.modules.instagram.api.instagram_api_error import (
    InstagramApiError,
)
from socialflow.modules.instagram.api.instagram_graph_client import (
    InstagramGraphClient,
)
from socialflow.modules.instagram.api.instagram_http_transport import (
    InstagramHttpResponse,
    InstagramHttpTransport,
)


class FakeInstagramTransport(InstagramHttpTransport):
    def __init__(
        self,
        status_code: int = 200,
        body: bytes = b'{"id":"123","username":"test_account"}',
    ) -> None:
        self.response = InstagramHttpResponse(status_code, body)
        self.get_requests: list[
            tuple[str, dict[str, str], float]
        ] = []
        self.post_requests: list[
            tuple[str, dict[str, str], bytes, float]
        ] = []

    def get(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> InstagramHttpResponse:
        self.get_requests.append((url, dict(headers), timeout))
        return self.response

    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout: float,
    ) -> InstagramHttpResponse:
        self.post_requests.append(
            (url, dict(headers), body, timeout)
        )
        return self.response


def test_get_uses_versioned_instagram_url() -> None:
    transport = FakeInstagramTransport()
    client = InstagramGraphClient("v24.0", transport=transport)

    result = client.get("me", "test-token")

    assert result["id"] == "123"
    assert transport.get_requests[0][0] == (
        "https://graph.instagram.com/v24.0/me"
    )


def test_get_sends_bearer_token_in_header_only() -> None:
    transport = FakeInstagramTransport()
    client = InstagramGraphClient("v24.0", transport=transport)

    client.get("me", " secret-token ")

    url, headers, _ = transport.get_requests[0]

    assert headers["Authorization"] == "Bearer secret-token"
    assert headers["Accept"] == "application/json"
    assert "secret-token" not in url


def test_get_encodes_query_parameters() -> None:
    transport = FakeInstagramTransport()
    client = InstagramGraphClient("v24.0", transport=transport)

    client.get(
        "me",
        "token",
        params={"fields": "id,username"},
    )

    assert "fields=id%2Cusername" in transport.get_requests[0][0]


def test_post_sends_form_encoded_body() -> None:
    transport = FakeInstagramTransport(
        body=b'{"id":"container-123"}',
    )
    client = InstagramGraphClient(
        "v24.0",
        transport=transport,
        timeout=7.5,
    )

    result = client.post(
        "123/media",
        "secret-token",
        {
            "image_url": "https://example.com/image.jpg",
            "caption": "Hello Instagram!",
        },
    )

    assert result == {"id": "container-123"}

    url, headers, body, timeout = transport.post_requests[0]

    assert url == "https://graph.instagram.com/v24.0/123/media"
    assert urlsplit(url).query == ""
    assert headers["Authorization"] == "Bearer secret-token"
    assert headers["Content-Type"] == (
        "application/x-www-form-urlencoded"
    )
    assert parse_qs(body.decode("utf-8")) == {
        "image_url": ["https://example.com/image.jpg"],
        "caption": ["Hello Instagram!"],
    }
    assert b"secret-token" not in body
    assert timeout == 7.5


@pytest.mark.parametrize(
    "version",
    ["", "24.0", "v0.0", "latest", "v24", "v24.0/other"],
)
def test_rejects_invalid_versions(version: str) -> None:
    with pytest.raises(ValueError, match="version"):
        InstagramGraphClient(version)


@pytest.mark.parametrize(
    "path",
    [
        "",
        "/me",
        "../me",
        "me/../accounts",
        "me?token=x",
        "me#fragment",
        "me//accounts",
        "https://example.com",
        "me\\accounts",
        "me/",
    ],
)
def test_rejects_invalid_paths(path: str) -> None:
    transport = FakeInstagramTransport()
    client = InstagramGraphClient("v24.0", transport=transport)

    with pytest.raises(ValueError, match="path"):
        client.get(path, "token")

    assert transport.get_requests == []


@pytest.mark.parametrize(
    "params",
    [
        {"access_token": "secret"},
        {"ACCESS_TOKEN": "secret"},
        {"": "value"},
        {123: "value"},
        {"limit": 5},
        {"fields": None},
    ],
)
def test_rejects_invalid_parameters(params: object) -> None:
    transport = FakeInstagramTransport()
    client = InstagramGraphClient("v24.0", transport=transport)

    with pytest.raises(ValueError):
        client.get("me", "token", params=params)  # type: ignore[arg-type]

    assert transport.get_requests == []


@pytest.mark.parametrize("token", ["", " ", "\t"])
def test_rejects_blank_tokens(token: str) -> None:
    transport = FakeInstagramTransport()
    client = InstagramGraphClient("v24.0", transport=transport)

    with pytest.raises(ValueError, match="token"):
        client.get("me", token)

    assert transport.get_requests == []


def test_graph_api_error_is_structured_and_safe() -> None:
    transport = FakeInstagramTransport(
        status_code=400,
        body=(
            b'{"error":{"message":"secret-token",'
            b'"type":"OAuthException","code":190,'
            b'"error_subcode":463}}'
        ),
    )
    client = InstagramGraphClient("v24.0", transport=transport)

    with pytest.raises(InstagramApiError) as exc_info:
        client.get("me", "secret-token")

    error = exc_info.value

    assert error.status_code == 400
    assert error.code == 190
    assert error.subcode == 463
    assert error.error_type == "OAuthException"
    assert "secret-token" not in str(error)
    assert "secret-token" not in error.message


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_transient_http_errors(status: int) -> None:
    transport = FakeInstagramTransport(
        status_code=status,
        body=b'{"error":{"code":1}}',
    )
    client = InstagramGraphClient("v24.0", transport=transport)

    with pytest.raises(InstagramApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.is_transient is True


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"not-json",
        b"\xff\xfe",
        b"[]",
    ],
)
def test_rejects_invalid_json_responses(body: bytes) -> None:
    transport = FakeInstagramTransport(body=body)
    client = InstagramGraphClient("v24.0", transport=transport)

    with pytest.raises(InstagramApiError):
        client.get("me", "token")


def test_rejects_unexpected_http_status() -> None:
    transport = FakeInstagramTransport(
        status_code=201,
        body=b'{"id":"123"}',
    )
    client = InstagramGraphClient("v24.0", transport=transport)

    with pytest.raises(InstagramApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.status_code == 201