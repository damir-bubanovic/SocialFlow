from typing import Mapping
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit

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


class RecordingPostTransport(FacebookHttpTransport):
    def __init__(self) -> None:
        self.requests: list[
            tuple[str, dict[str, str], bytes, float]
        ] = []

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
            status_code=200,
            body=b'{"id":"123_456"}',
        )


def test_post_sends_form_body_and_bearer_token() -> None:
    transport = RecordingPostTransport()
    client = FacebookGraphClient(
        "v24.0",
        transport=transport,
        timeout=7.5,
    )

    result = client.post(
        "123/feed",
        "page-secret-token",
        {"message": "Hello Facebook!"},
    )

    assert result == {"id": "123_456"}
    assert len(transport.requests) == 1

    url, headers, body, timeout = transport.requests[0]

    assert url == "https://graph.facebook.com/v24.0/123/feed"
    assert urlsplit(url).query == ""
    assert headers["Authorization"] == "Bearer page-secret-token"
    assert headers["Accept"] == "application/json"
    assert headers["Content-Type"] == (
        "application/x-www-form-urlencoded"
    )
    assert parse_qs(body.decode("utf-8")) == {
        "message": ["Hello Facebook!"],
    }
    assert b"page-secret-token" not in body
    assert "page-secret-token" not in url
    assert timeout == 7.5


@pytest.mark.parametrize(
    "path",
    [
        "",
        "/123/feed",
        "123/feed?access_token=secret",
        "123/feed#fragment",
        "123//feed",
        "123/../feed",
        "123\\feed",
        "123/feed/",
    ],
)
def test_post_rejects_invalid_paths(path: str) -> None:
    transport = RecordingPostTransport()
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(ValueError, match="resource path"):
        client.post(path, "page-token", {"message": "Hello"})

    assert transport.requests == []


@pytest.mark.parametrize(
    "params",
    [
        {"access_token": "secret"},
        {"ACCESS_TOKEN": "secret"},
        {"message": 123},
        {123: "Hello"},
        {"": "Hello"},
    ],
)
def test_post_rejects_invalid_parameters(params) -> None:
    transport = RecordingPostTransport()
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(ValueError):
        client.post("123/feed", "page-token", params)

    assert transport.requests == []


@pytest.mark.parametrize(
    "token",
    [
        "",
        "   ",
        None,
    ],
)
def test_post_rejects_invalid_tokens(token) -> None:
    transport = RecordingPostTransport()
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(ValueError, match="access token"):
        client.post("123/feed", token, {"message": "Hello"})

    assert transport.requests == []


class FailingPostTransport(RecordingPostTransport):
    def __init__(
        self,
        failure: Exception | None = None,
        status: int = 200,
        response_body: bytes = b'{"id":"123_456"}',
    ) -> None:
        super().__init__()
        self.failure = failure
        self.status = status
        self.response_body = response_body

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


@pytest.mark.parametrize(
    "failure",
    [
        TimeoutError("page-secret-token"),
        URLError("page-secret-token"),
        OSError("page-secret-token"),
    ],
)
def test_post_network_errors_do_not_expose_credentials(
    failure: Exception,
) -> None:
    transport = FailingPostTransport(failure=failure)
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(FacebookApiError) as exc_info:
        client.post(
            "123/feed",
            "page-secret-token",
            {"message": "Hello"},
        )

    error = exc_info.value

    assert error.is_transient is True
    assert "page-secret-token" not in str(error)
    assert "page-secret-token" not in error.message
    assert error.__cause__ is None
    assert error.__suppress_context__ is True


def test_post_graph_api_error_is_structured() -> None:
    transport = FailingPostTransport(
        status=403,
        response_body=(
            b'{"error":{"message":"page-secret-token",'
            b'"type":"OAuthException","code":200}}'
        ),
    )
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(FacebookApiError) as exc_info:
        client.post(
            "123/feed",
            "page-secret-token",
            {"message": "Hello"},
        )

    error = exc_info.value

    assert error.status_code == 403
    assert error.code == 200
    assert error.error_type == "OAuthException"
    assert error.is_transient is False
    assert "page-secret-token" not in str(error)
    assert "page-secret-token" not in error.message


@pytest.mark.parametrize(
    ("status", "response_body"),
    [
        (500, b'{"error":{"code":4}}'),
        (429, b'{"error":{"code":613}}'),
        (503, b'{"unexpected":"response"}'),
    ],
)
def test_post_transient_http_errors(
    status: int,
    response_body: bytes,
) -> None:
    transport = FailingPostTransport(
        status=status,
        response_body=response_body,
    )
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(FacebookApiError) as exc_info:
        client.post(
            "123/feed",
            "page-secret-token",
            {"message": "Hello"},
        )

    assert exc_info.value.status_code == status
    assert exc_info.value.is_transient is True


@pytest.mark.parametrize(
    ("status", "response_body"),
    [
        (200, b"not-json"),
        (200, b"[]"),
        (201, b'{"id":"123_456"}'),
        (302, b'{"id":"123_456"}'),
    ],
)
def test_post_rejects_unexpected_responses(
    status: int,
    response_body: bytes,
) -> None:
    transport = FailingPostTransport(
        status=status,
        response_body=response_body,
    )
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(FacebookApiError):
        client.post(
            "123/feed",
            "page-secret-token",
            {"message": "Hello"},
        )
