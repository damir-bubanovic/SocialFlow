from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from socialflow.modules.facebook.api.urllib_facebook_http_transport import (
    UrllibFacebookHttpTransport,
)


@pytest.mark.parametrize(
    "url",
    [
        "http://graph.facebook.com/v24.0/me",
        "ftp://graph.facebook.com/me",
        "https://user:pass@graph.facebook.com/me",
        "https://graph.facebook.com/me#fragment",
        "not-a-url",
    ],
)
def test_transport_rejects_invalid_urls(url: str) -> None:
    transport = UrllibFacebookHttpTransport()

    with pytest.raises(ValueError, match="HTTPS"):
        transport.get(url, {}, 10.0)


@pytest.mark.parametrize("timeout", [0, -1])
def test_transport_rejects_invalid_timeout(timeout: float) -> None:
    transport = UrllibFacebookHttpTransport()

    with pytest.raises(ValueError, match="timeout"):
        transport.get(
            "https://graph.facebook.com/v24.0/me",
            {},
            timeout,
        )


def test_transport_returns_successful_response() -> None:
    response = MagicMock()
    response.status = 200
    response.read.return_value = b'{"id":"123"}'
    response.__enter__.return_value = response

    opener = MagicMock()
    opener.open.return_value = response

    with patch(
        "socialflow.modules.facebook.api."
        "urllib_facebook_http_transport.build_opener",
        return_value=opener,
    ):
        result = UrllibFacebookHttpTransport().get(
            "https://graph.facebook.com/v24.0/me",
            {"Authorization": "Bearer test-token"},
            5.0,
        )

    assert result.status_code == 200
    assert result.body == b'{"id":"123"}'
    assert opener.open.call_args.kwargs["timeout"] == 5.0


def test_transport_post_sends_body_and_headers() -> None:
    response = MagicMock()
    response.status = 200
    response.read.return_value = b'{"id":"123_456"}'
    response.__enter__.return_value = response

    opener = MagicMock()
    opener.open.return_value = response

    with patch(
        "socialflow.modules.facebook.api."
        "urllib_facebook_http_transport.build_opener",
        return_value=opener,
    ):
        result = UrllibFacebookHttpTransport().post(
            "https://graph.facebook.com/v24.0/123/feed",
            {
                "Authorization": "Bearer secret-token",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            b"message=Hello+Facebook",
            5.0,
        )

    request = opener.open.call_args.args[0]

    assert request.get_method() == "POST"
    assert request.data == b"message=Hello+Facebook"
    assert request.get_header("Authorization") == "Bearer secret-token"
    assert request.get_header("Content-type") == (
        "application/x-www-form-urlencoded"
    )
    assert opener.open.call_args.kwargs["timeout"] == 5.0
    assert result.status_code == 200
    assert result.body == b'{"id":"123_456"}'


@pytest.mark.parametrize(
    "body",
    [
        None,
        "message=Hello",
        {"message": "Hello"},
        123,
    ],
)
def test_transport_post_rejects_non_bytes_body(body: Any) -> None:
    transport = UrllibFacebookHttpTransport()

    with pytest.raises(ValueError, match="body"):
        transport.post(
            "https://graph.facebook.com/v24.0/123/feed",
            {},
            body,
            5.0,
        )
