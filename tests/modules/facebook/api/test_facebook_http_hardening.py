from email.message import Message
from io import BytesIO
from typing import Any, Mapping, cast
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.request import Request


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
from socialflow.modules.facebook.api.urllib_facebook_http_transport import (
    UrllibFacebookHttpTransport,
)


class StubTransport(FacebookHttpTransport):
    def __init__(
        self,
        status: Any = 200,
        body: Any = b'{"id":"123"}',
    ) -> None:
        self.status = status
        self.body = body
        self.calls = 0

    def get(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> FacebookHttpResponse:
        self.calls += 1
        return FacebookHttpResponse(
            status_code=self.status,
            body=self.body,
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


@pytest.mark.parametrize(
    "params",
    [
        {"access_token": "secret"},
        {"ACCESS_TOKEN": "secret"},
        {"": "value"},
        {123: "value"},
        {"limit": 5},
        {"fields": None},
        ["fields", "id"],
        "fields=id",
    ],
)
def test_rejects_invalid_query_parameters(
    params: Any,
) -> None:
    transport = StubTransport()
    client = FacebookGraphClient(
        "v24.0",
        transport=transport,
    )

    with pytest.raises(ValueError):
        client.get(
            "me/accounts",
            "secret-token",
            params=cast(Any, params),
        )

    assert transport.calls == 0


@pytest.mark.parametrize(
    "status",
    [
        0,
        -1,
        99,
        600,
        1000,
        True,
        "200",
        None,
    ],
)
def test_rejects_invalid_http_status(
    status: Any,
) -> None:
    client = FacebookGraphClient(
        "v24.0",
        transport=StubTransport(status=status),
    )

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "secret-token")

    assert exc_info.value.status_code is None
    assert "secret-token" not in str(exc_info.value)


@pytest.mark.parametrize(
    "body",
    [
        None,
        "not bytes",
        {"id": "123"},
        123,
    ],
)
def test_rejects_non_bytes_response_body(
    body: Any,
) -> None:
    client = FacebookGraphClient(
        "v24.0",
        transport=StubTransport(body=body),
    )

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "secret-token")

    assert exc_info.value.status_code == 200


@pytest.mark.parametrize(
    "status",
    [201, 202, 204, 301, 302, 307, 308],
)
def test_rejects_unexpected_http_status(
    status: int,
) -> None:
    client = FacebookGraphClient(
        "v24.0",
        transport=StubTransport(status=status),
    )

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "secret-token")

    assert exc_info.value.status_code == status


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
def test_transport_rejects_invalid_timeouts(
    timeout: Any,
) -> None:
    transport = UrllibFacebookHttpTransport()

    with pytest.raises(ValueError, match="timeout"):
        transport.get(
            "https://graph.facebook.com/v24.0/me",
            {},
            cast(Any, timeout),
        )


@pytest.mark.parametrize(
    "url",
    [
        "https://graph.facebook.com:abc/me",
        "https://graph.facebook.com:99999/me",
        "https://graph.facebook.com:0/me",
    ],
)
def test_transport_rejects_invalid_ports(
    url: str,
) -> None:
    transport = UrllibFacebookHttpTransport()

    with pytest.raises(ValueError, match="port"):
        transport.get(url, {}, 10.0)


def test_redirect_handler_refuses_redirect() -> None:
    from urllib.request import HTTPRedirectHandler

    from socialflow.modules.facebook.api import (
        urllib_facebook_http_transport,
    )

    handler = urllib_facebook_http_transport._NoRedirectHandler()

    assert isinstance(handler, HTTPRedirectHandler)

    request = Request(
        "https://graph.facebook.com/v24.0/me",
        headers={"Authorization": "Bearer secret-token"},
    )

    redirected = handler.redirect_request(
        request,
        BytesIO(b""),
        302,
        "Found",
        cast(Any, Message()),
        "https://example.com",
    )

    assert redirected is None

def test_transport_returns_http_error_response() -> None:
    error = HTTPError(
        url="https://graph.facebook.com/v24.0/me",
        code=403,
        msg="Forbidden",
        hdrs=cast(Any, Message()),
        fp=BytesIO(b'{"error":{"code":200}}'),
    )

    opener = MagicMock()
    opener.open.side_effect = error

    with patch(
        "socialflow.modules.facebook.api."
        "urllib_facebook_http_transport.build_opener",
        return_value=opener,
    ):
        response = UrllibFacebookHttpTransport().get(
            "https://graph.facebook.com/v24.0/me",
            {"Authorization": "Bearer secret-token"},
            10.0,
        )

    assert response.status_code == 403
    assert response.body == b'{"error":{"code":200}}'


def test_network_error_does_not_expose_exception_chain() -> None:
    class FailingTransport(FacebookHttpTransport):
        def get(
            self,
            url: str,
            headers: Mapping[str, str],
            timeout: float,
        ) -> FacebookHttpResponse:
            raise TimeoutError("secret-token")

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

    client = FacebookGraphClient(
        "v24.0",
        transport=FailingTransport(),
    )

    with pytest.raises(FacebookApiError) as exc_info:
        client.get("me", "secret-token")

    error = exc_info.value

    assert "secret-token" not in str(error)
    assert error.__suppress_context__ is True
    assert error.__cause__ is None
