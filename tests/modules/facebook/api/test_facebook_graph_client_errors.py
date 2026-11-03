
import json
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


class StubTransport(FacebookHttpTransport):
    def __init__(
        self,
        status: int = 200,
        payload: object = None,
        body: bytes | None = None,
        failure: Exception | None = None,
    ) -> None:
        self.status = status
        self.payload = payload
        self.body = body
        self.failure = failure

    def get(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> FacebookHttpResponse:
        if self.failure is not None:
            raise self.failure

        body = self.body
        if body is None:
            body = json.dumps(self.payload).encode("utf-8")

        return FacebookHttpResponse(
            status_code=self.status,
            body=body,
        )

    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout: float,
    ) -> FacebookHttpResponse:
        raise NotImplementedError(
            "POST is not supported by this test transport."
        )


def make_client(transport: StubTransport) -> FacebookGraphClient:
    return FacebookGraphClient(
        "v24.0",
        transport=transport,
    )


def test_oauth_error_is_structured() -> None:
    client = make_client(
        StubTransport(
            status=400,
            payload={
                "error": {
                    "message": "Sensitive server diagnostic",
                    "type": "OAuthException",
                    "code": 190,
                    "error_subcode": 463,
                }
            },
        )
    )

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "secret-token")

    error = exc_info.value

    assert error.status_code == 400
    assert error.code == 190
    assert error.subcode == 463
    assert error.error_type == "OAuthException"
    assert error.is_transient is False

    assert "secret-token" not in str(error)
    assert "Sensitive server diagnostic" not in str(error)
    assert "Sensitive server diagnostic" not in error.message


def test_permission_error_is_structured() -> None:
    client = make_client(
        StubTransport(
            status=403,
            payload={
                "error": {
                    "code": 200,
                    "type": "OAuthException",
                }
            },
        )
    )

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me/accounts", "token")

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == 200
    assert exc_info.value.is_transient is False


@pytest.mark.parametrize(
    "status",
    [429, 500, 502, 503, 504],
)
def test_transient_http_statuses(status: int) -> None:
    client = make_client(
        StubTransport(
            status=status,
            payload={"error": {"code": 1}},
        )
    )

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.status_code == status
    assert exc_info.value.is_transient is True


@pytest.mark.parametrize(
    "code",
    [4, 17, 32, 613],
)
def test_transient_graph_codes(code: int) -> None:
    client = make_client(
        StubTransport(
            status=400,
            payload={"error": {"code": code}},
        )
    )

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.code == code
    assert exc_info.value.is_transient is True


def test_explicit_transient_flag() -> None:
    client = make_client(
        StubTransport(
            status=400,
            payload={
                "error": {
                    "code": 2,
                    "is_transient": True,
                }
            },
        )
    )

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.is_transient is True


def test_graph_error_inside_successful_http_response() -> None:
    client = make_client(
        StubTransport(
            status=200,
            payload={"error": {"code": 190}},
        )
    )

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.status_code == 200
    assert exc_info.value.code == 190


@pytest.mark.parametrize(
    "failure",
    [
        TimeoutError("timeout with secret-token"),
        URLError("network error with secret-token"),
        ConnectionError("connection failed with secret-token"),
    ],
)
def test_network_failures_are_safe_and_transient(
    failure: Exception,
) -> None:
    client = make_client(StubTransport(failure=failure))

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "secret-token")

    error = exc_info.value

    assert error.status_code is None
    assert error.is_transient is True
    assert "secret-token" not in str(error)
    assert "secret-token" not in error.message


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"not json",
        b"\xff\xfe",
        b"{broken",
    ],
)
def test_invalid_json_responses(body: bytes) -> None:
    client = make_client(StubTransport(body=body))

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.status_code == 200


@pytest.mark.parametrize(
    "payload",
    [
        [],
        [1, 2],
        "unexpected",
        123,
        None,
    ],
)
def test_non_object_json_responses(payload: object) -> None:
    client = make_client(StubTransport(payload=payload))

    with pytest.raises(FacebookApiError):
        client.get("me", "token")


def test_non_json_http_error_preserves_status() -> None:
    client = make_client(
        StubTransport(
            status=503,
            body=b"<html>Service unavailable</html>",
        )
    )

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.status_code == 503
    assert exc_info.value.is_transient is True


def test_http_error_without_graph_error_object() -> None:
    client = make_client(
        StubTransport(
            status=401,
            payload={"message": "Unauthorized"},
        )
    )

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.code is None


def test_valid_successful_response_is_unchanged() -> None:
    payload = {
        "data": [
            {"id": "123", "name": "Test Page"},
        ]
    }
    client = make_client(StubTransport(payload=payload))

    assert client.get("me/accounts", "token") == payload


def test_graph_error_ignores_invalid_optional_fields() -> None:
    client = make_client(
        StubTransport(
            status=400,
            payload={
                "error": {
                    "code": "not-an-integer",
                    "error_subcode": True,
                    "type": 123,
                    "is_transient": "yes",
                }
            },
        )
    )

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "token")

    assert exc_info.value.code is None
    assert exc_info.value.subcode is None
    assert exc_info.value.error_type is None
    assert exc_info.value.is_transient is False
