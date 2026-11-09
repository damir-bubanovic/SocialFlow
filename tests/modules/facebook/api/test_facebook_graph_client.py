
import json
from typing import Mapping

import pytest

from socialflow.modules.facebook.api.facebook_graph_client import (
    FacebookGraphClient,
)
from socialflow.modules.facebook.api.facebook_http_transport import (
    FacebookHttpResponse,
    FacebookHttpTransport,
)
from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)


class FakeFacebookTransport(FacebookHttpTransport):
    def __init__(
        self,
        status_code: int = 200,
        body: bytes = b'{"id":"123","name":"Test Page"}',
    ) -> None:
        self.response = FacebookHttpResponse(status_code, body)
        self.requests: list[tuple[str, dict[str, str], float]] = []

    def get(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> FacebookHttpResponse:
        self.requests.append((url, dict(headers), timeout))
        return self.response

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


class FakeDeleteTransport(FakeFacebookTransport):
    def __init__(
        self,
        status_code: int = 200,
        body: bytes = b'{"success":true}',
    ) -> None:
        super().__init__(status_code=status_code, body=body)
        self.delete_requests: list[
            tuple[str, dict[str, str], float]
        ] = []

    def delete(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> FacebookHttpResponse:
        self.delete_requests.append(
            (url, dict(headers), timeout)
        )
        return self.response

def test_graph_client_uses_versioned_url() -> None:
    transport = FakeFacebookTransport()
    client = FacebookGraphClient("v24.0", transport=transport)

    result = client.get("123", "test-token")

    assert result["id"] == "123"
    assert transport.requests[0][0] == (
        "https://graph.facebook.com/v24.0/123"
    )


def test_graph_client_sends_token_in_header_only() -> None:
    transport = FakeFacebookTransport()
    client = FacebookGraphClient("v24.0", transport=transport)

    client.get("me/accounts", "secret-token")

    url, headers, _ = transport.requests[0]

    assert "secret-token" not in url
    assert headers["Authorization"] == "Bearer secret-token"
    assert headers["Accept"] == "application/json"


def test_graph_client_encodes_query_parameters() -> None:
    transport = FakeFacebookTransport()
    client = FacebookGraphClient("v24.0", transport=transport)

    client.get(
        "me/accounts",
        "test-token",
        params={"fields": "id,name", "limit": "5"},
    )

    url = transport.requests[0][0]

    assert "fields=id%2Cname" in url
    assert "limit=5" in url


def test_graph_client_uses_configured_timeout() -> None:
    transport = FakeFacebookTransport()
    client = FacebookGraphClient(
        "v24.0",
        transport=transport,
        timeout=7.5,
    )

    client.get("123", "test-token")

    assert transport.requests[0][2] == 7.5


@pytest.mark.parametrize(
    "version",
    ["", "24.0", "v0.0", "latest", "v24", "v24.0/other"],
)
def test_graph_client_rejects_invalid_versions(version: str) -> None:
    with pytest.raises(ValueError, match="version"):
        FacebookGraphClient(version)


@pytest.mark.parametrize("timeout", [0, -1, -10])
def test_graph_client_rejects_invalid_timeout(timeout: float) -> None:
    with pytest.raises(ValueError, match="timeout"):
        FacebookGraphClient("v24.0", timeout=timeout)


@pytest.mark.parametrize(
    "path",
    ["", "/me", "../me", "me/../accounts", "me?token=x",
     "me#fragment", "me//accounts", "https://example.com"],
)
def test_graph_client_rejects_invalid_paths(path: str) -> None:
    client = FacebookGraphClient(
        "v24.0",
        transport=FakeFacebookTransport(),
    )

    with pytest.raises(ValueError, match="path"):
        client.get(path, "test-token")


@pytest.mark.parametrize("token", ["", " ", "\t"])
def test_graph_client_rejects_blank_token(token: str) -> None:
    client = FacebookGraphClient(
        "v24.0",
        transport=FakeFacebookTransport(),
    )

    with pytest.raises(ValueError, match="token"):
        client.get("me", token)


def test_graph_client_rejects_non_object_json() -> None:
    transport = FakeFacebookTransport(body=b'["unexpected"]')
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "test-token")

    assert exc_info.value.status_code == 200
    assert "JSON object" not in str(exc_info.value)


def test_graph_client_reports_http_status_without_token() -> None:
    transport = FakeFacebookTransport(
        status_code=403,
        body=b'{"error":"permission denied"}',
    )
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "secret-token")

    assert "403" in str(exc_info.value)
    assert "secret-token" not in str(exc_info.value)


def test_graph_client_returns_json_object() -> None:
    payload = {"data": [{"id": "123", "name": "Page"}]}
    transport = FakeFacebookTransport(
        body=json.dumps(payload).encode("utf-8"),
    )
    client = FacebookGraphClient("v24.0", transport=transport)

    assert client.get("me/accounts", "test-token") == payload


def test_graph_client_delete_uses_versioned_url_and_auth() -> None:
    transport = FakeDeleteTransport()
    client = FacebookGraphClient(
        "v24.0",
        transport=transport,
        timeout=7.5,
    )

    result = client.delete("123456", " secret-token ")

    assert result == {"success": True}
    assert len(transport.delete_requests) == 1

    url, headers, timeout = transport.delete_requests[0]

    assert url == "https://graph.facebook.com/v24.0/123456"
    assert headers["Authorization"] == "Bearer secret-token"
    assert headers["Accept"] == "application/json"
    assert timeout == 7.5
    assert "secret-token" not in url


@pytest.mark.parametrize(
    "invalid_path",
    ["", "/123", "../123", "123?token=x", "123/../456"],
)
def test_graph_client_delete_rejects_invalid_paths(
    invalid_path: str,
) -> None:
    transport = FakeDeleteTransport()
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(ValueError, match="path"):
        client.delete(invalid_path, "token")

    assert transport.delete_requests == []


@pytest.mark.parametrize("invalid_token", ["", " ", "\t"])
def test_graph_client_delete_rejects_blank_token(
    invalid_token: str,
) -> None:
    transport = FakeDeleteTransport()
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(ValueError, match="token"):
        client.delete("123456", invalid_token)

    assert transport.delete_requests == []


def test_graph_client_delete_reports_graph_api_error() -> None:
    transport = FakeDeleteTransport(
        status_code=400,
        body=b'{"error":{"message":"Deletion denied","code":100}}',
    )
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(FacebookApiError) as exc_info:
        client.delete("123456", "secret-token")

    assert exc_info.value.status_code == 400
    assert exc_info.value.code == 100
    assert "secret-token" not in str(exc_info.value)


def test_graph_client_delete_rejects_invalid_json_response() -> None:
    transport = FakeDeleteTransport(body=b"not-json")
    client = FacebookGraphClient("v24.0", transport=transport)

    with pytest.raises(FacebookApiError):
        client.delete("123456", "token")
