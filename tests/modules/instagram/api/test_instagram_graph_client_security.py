from typing import Any, Mapping
from urllib.error import URLError

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


class StubInstagramTransport(InstagramHttpTransport):
    def __init__(
        self,
        status: Any = 200,
        body: Any = b'{"id":"123"}',
        failure: Exception | None = None,
    ) -> None:
        self.status = status
        self.body = body
        self.failure = failure
        self.calls = 0

    def get(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> InstagramHttpResponse:
        self.calls += 1

        if self.failure is not None:
            raise self.failure

        return InstagramHttpResponse(
            status_code=self.status,
            body=self.body,
        )

    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout: float,
    ) -> InstagramHttpResponse:
        self.calls += 1

        if self.failure is not None:
            raise self.failure

        return InstagramHttpResponse(
            status_code=self.status,
            body=self.body,
        )


@pytest.mark.parametrize(
    "timeout",
    [
        0,
        -1,
        float("inf"),
        float("-inf"),
        float("nan"),
        True,
        "10",
    ],
)
def test_client_rejects_invalid_timeouts(timeout: Any) -> None:
    with pytest.raises(ValueError, match="timeout"):
        InstagramGraphClient("v24.0", timeout=timeout)


@pytest.mark.parametrize(
    "status",
    [0, -1, 99, 600, 1000, True, "200", None],
)
def test_rejects_invalid_http_status(status: Any) -> None:
    client = InstagramGraphClient(
        "v24.0",
        transport=StubInstagramTransport(status=status),
    )

    with pytest.raises(InstagramApiError) as exc_info:
        client.get("me", "secret-token")

    assert exc_info.value.status_code is None
    assert "secret-token" not in str(exc_info.value)


@pytest.mark.parametrize(
    "body",
    [None, "not bytes", {"id": "123"}, 123],
)
def test_rejects_non_bytes_response_body(body: Any) -> None:
    client = InstagramGraphClient(
        "v24.0",
        transport=StubInstagramTransport(body=body),
    )

    with pytest.raises(InstagramApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.status_code == 200


@pytest.mark.parametrize(
    "status",
    [201, 202, 204, 301, 302, 307, 308],
)
def test_rejects_unexpected_http_status(status: int) -> None:
    client = InstagramGraphClient(
        "v24.0",
        transport=StubInstagramTransport(status=status),
    )

    with pytest.raises(InstagramApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.status_code == status


@pytest.mark.parametrize(
    "failure",
    [
        TimeoutError("secret-token"),
        URLError("secret-token"),
        OSError("secret-token"),
    ],
)
def test_get_network_failures_are_safe(
    failure: Exception,
) -> None:
    client = InstagramGraphClient(
        "v24.0",
        transport=StubInstagramTransport(failure=failure),
    )

    with pytest.raises(InstagramApiError) as exc_info:
        client.get("me", "secret-token")

    error = exc_info.value

    assert error.is_transient is True
    assert error.__cause__ is None
    assert error.__suppress_context__ is True
    assert "secret-token" not in str(error)
    assert "secret-token" not in error.message


@pytest.mark.parametrize(
    "failure",
    [
        TimeoutError("secret-token"),
        URLError("secret-token"),
        OSError("secret-token"),
    ],
)
def test_post_network_failures_are_safe(
    failure: Exception,
) -> None:
    client = InstagramGraphClient(
        "v24.0",
        transport=StubInstagramTransport(failure=failure),
    )

    with pytest.raises(InstagramApiError) as exc_info:
        client.post(
            "123/media",
            "secret-token",
            {"caption": "Test"},
        )

    error = exc_info.value

    assert error.is_transient is True
    assert error.__cause__ is None
    assert error.__suppress_context__ is True
    assert "secret-token" not in str(error)


@pytest.mark.parametrize(
    "code",
    [4, 17, 32, 613],
)
def test_transient_graph_error_codes(code: int) -> None:
    client = InstagramGraphClient(
        "v24.0",
        transport=StubInstagramTransport(
            status=400,
            body=(
                '{"error":{"code":' + str(code) + "}}"
            ).encode("utf-8"),
        ),
    )

    with pytest.raises(InstagramApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.code == code
    assert exc_info.value.is_transient is True


def test_explicit_transient_flag() -> None:
    client = InstagramGraphClient(
        "v24.0",
        transport=StubInstagramTransport(
            status=400,
            body=b'{"error":{"code":2,"is_transient":true}}',
        ),
    )

    with pytest.raises(InstagramApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.is_transient is True


def test_graph_error_in_successful_http_response() -> None:
    client = InstagramGraphClient(
        "v24.0",
        transport=StubInstagramTransport(
            body=b'{"error":{"code":190}}',
        ),
    )

    with pytest.raises(InstagramApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.status_code == 200
    assert exc_info.value.code == 190


def test_invalid_optional_error_fields_are_ignored() -> None:
    client = InstagramGraphClient(
        "v24.0",
        transport=StubInstagramTransport(
            status=400,
            body=(
                b'{"error":{"code":"invalid",'
                b'"error_subcode":true,'
                b'"type":123,'
                b'"is_transient":"yes"}}'
            ),
        ),
    )

    with pytest.raises(InstagramApiError) as exc_info:
        client.get("me", "token")

    error = exc_info.value

    assert error.code is None
    assert error.subcode is None
    assert error.error_type is None
    assert error.is_transient is False


@pytest.mark.parametrize(
    "params",
    [
        {"access_token": "secret"},
        {"ACCESS_TOKEN": "secret"},
        {"caption": 123},
        {123: "caption"},
        {"": "caption"},
    ],
)
def test_post_rejects_invalid_parameters(
    params: Any,
) -> None:
    transport = StubInstagramTransport()
    client = InstagramGraphClient(
        "v24.0",
        transport=transport,
    )

    with pytest.raises(ValueError):
        client.post("123/media", "token", params)

    assert transport.calls == 0


@pytest.mark.parametrize(
    "path",
    [
        "",
        "/123/media",
        "123/media?access_token=secret",
        "123/media#fragment",
        "123//media",
        "123/../media",
        "123\\media",
        "123/media/",
    ],
)
def test_post_rejects_invalid_paths(path: str) -> None:
    transport = StubInstagramTransport()
    client = InstagramGraphClient(
        "v24.0",
        transport=transport,
    )

    with pytest.raises(ValueError, match="path"):
        client.post(path, "token", {"caption": "Test"})

    assert transport.calls == 0