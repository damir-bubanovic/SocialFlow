from email.message import Message
from io import BytesIO
from typing import Any, cast
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request

import pytest

from socialflow.modules.instagram.api.urllib_instagram_http_transport import (
    UrllibInstagramHttpTransport,
)


@pytest.mark.parametrize(
    "url",
    [
        "http://graph.instagram.com/v24.0/me",
        "ftp://graph.instagram.com/me",
        "https://user:pass@graph.instagram.com/me",
        "https://graph.instagram.com/me#fragment",
        "not-a-url",
    ],
)
def test_transport_rejects_invalid_urls(url: str) -> None:
    transport = UrllibInstagramHttpTransport()

    with pytest.raises(ValueError, match="HTTPS"):
        transport.get(url, {}, 10.0)


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
    transport = UrllibInstagramHttpTransport()

    with pytest.raises(ValueError, match="timeout"):
        transport.get(
            "https://graph.instagram.com/v24.0/me",
            {},
            cast(Any, timeout),
        )


@pytest.mark.parametrize(
    "url",
    [
        "https://graph.instagram.com:abc/me",
        "https://graph.instagram.com:99999/me",
        "https://graph.instagram.com:0/me",
    ],
)
def test_transport_rejects_invalid_ports(url: str) -> None:
    transport = UrllibInstagramHttpTransport()

    with pytest.raises(ValueError, match="port"):
        transport.get(url, {}, 10.0)


def test_transport_returns_successful_response() -> None:
    response = MagicMock()
    response.status = 200
    response.read.return_value = b'{"id":"123"}'
    response.__enter__.return_value = response

    opener = MagicMock()
    opener.open.return_value = response

    with patch(
        "socialflow.modules.instagram.api."
        "urllib_instagram_http_transport.build_opener",
        return_value=opener,
    ):
        result = UrllibInstagramHttpTransport().get(
            "https://graph.instagram.com/v24.0/me",
            {"Authorization": "Bearer test-token"},
            5.0,
        )

    assert result.status_code == 200
    assert result.body == b'{"id":"123"}'
    assert opener.open.call_args.kwargs["timeout"] == 5.0


def test_transport_post_sends_body_and_headers() -> None:
    response = MagicMock()
    response.status = 200
    response.read.return_value = b'{"id":"container-123"}'
    response.__enter__.return_value = response

    opener = MagicMock()
    opener.open.return_value = response

    with patch(
        "socialflow.modules.instagram.api."
        "urllib_instagram_http_transport.build_opener",
        return_value=opener,
    ):
        result = UrllibInstagramHttpTransport().post(
            "https://graph.instagram.com/v24.0/123/media",
            {
                "Authorization": "Bearer secret-token",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            b"image_url=https%3A%2F%2Fexample.com%2Fimage.jpg",
            5.0,
        )

    request = opener.open.call_args.args[0]

    assert request.get_method() == "POST"
    assert request.data == (
        b"image_url=https%3A%2F%2Fexample.com%2Fimage.jpg"
    )
    assert request.get_header("Authorization") == "Bearer secret-token"
    assert request.get_header("Content-type") == (
        "application/x-www-form-urlencoded"
    )
    assert opener.open.call_args.kwargs["timeout"] == 5.0
    assert result.status_code == 200
    assert result.body == b'{"id":"container-123"}'


@pytest.mark.parametrize(
    "body",
    [
        None,
        "image_url=https://example.com/image.jpg",
        {"image_url": "https://example.com/image.jpg"},
        123,
    ],
)
def test_transport_post_rejects_non_bytes_body(
    body: Any,
) -> None:
    transport = UrllibInstagramHttpTransport()

    with pytest.raises(ValueError, match="body"):
        transport.post(
            "https://graph.instagram.com/v24.0/123/media",
            {},
            body,
            5.0,
        )


def test_redirect_handler_refuses_redirect() -> None:
    from socialflow.modules.instagram.api import (
        urllib_instagram_http_transport,
    )

    # noinspection PyProtectedMember
    handler = urllib_instagram_http_transport._NoRedirectHandler()

    assert isinstance(handler, HTTPRedirectHandler)

    request = Request(
        "https://graph.instagram.com/v24.0/me",
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
        url="https://graph.instagram.com/v24.0/me",
        code=403,
        msg="Forbidden",
        hdrs=cast(Any, Message()),
        fp=BytesIO(b'{"error":{"code":200}}'),
    )

    opener = MagicMock()
    opener.open.side_effect = error

    with patch(
        "socialflow.modules.instagram.api."
        "urllib_instagram_http_transport.build_opener",
        return_value=opener,
    ):
        response = UrllibInstagramHttpTransport().get(
            "https://graph.instagram.com/v24.0/me",
            {"Authorization": "Bearer secret-token"},
            10.0,
        )

    assert response.status_code == 403
    assert response.body == b'{"error":{"code":200}}'