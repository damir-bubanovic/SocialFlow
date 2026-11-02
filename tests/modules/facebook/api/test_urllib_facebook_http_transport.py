
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
