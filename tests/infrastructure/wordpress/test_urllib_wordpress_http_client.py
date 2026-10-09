import http.client
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from socialflow.infrastructure.wordpress.urllib_wordpress_http_client import (
    UrllibWordPressHttpClient,
)


@pytest.mark.parametrize(
    "site_url",
    [
        "http://example.com",
        "ftp://example.com",
        "https://user:password@example.com",
        "https://example.com?token=secret",
        "https://example.com#fragment",
        "not-a-url",
    ],
)
def test_http_client_rejects_invalid_site_urls(
    site_url: str,
) -> None:
    client = UrllibWordPressHttpClient()

    with pytest.raises(ValueError):
        client.get_authenticated_user(
            site_url=site_url,
            username="admin",
            application_password="test-password",
        )


def test_http_client_rejects_invalid_timeout() -> None:
    with pytest.raises(ValueError):
        UrllibWordPressHttpClient(timeout=0)


class FakeHttpResponse:
    """Simulate a successful HTTP response."""

    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


def test_http_client_accepts_successful_response() -> None:
    client = UrllibWordPressHttpClient()

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_http_client.build_opener"
    ) as mocked_opener:
        mocked_opener.return_value.open.return_value = (
            FakeHttpResponse(200)
        )

        result = client.get_authenticated_user(
            site_url="https://example.com",
            username="admin",
            application_password="test-password",
        )

    assert result.status_code == 200


@pytest.mark.parametrize("status_code", [401, 403])
def test_http_client_returns_authentication_error_status(
    status_code: int,
) -> None:
    client = UrllibWordPressHttpClient()

    error = HTTPError(
        url="https://example.com/wp-json/wp/v2/users/me",
        code=status_code,
        msg="Authentication failed",
        hdrs=http.client.HTTPMessage(),
        fp=BytesIO(b""),
    )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_http_client.build_opener"
    ) as mocked_opener:
        mocked_opener.return_value.open.side_effect = error

        result = client.get_authenticated_user(
            site_url="https://example.com",
            username="admin",
            application_password="wrong-password",
        )

    assert result.status_code == status_code


def test_http_client_disables_redirects() -> None:
    client = UrllibWordPressHttpClient()

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_http_client.build_opener"
    ) as mocked_opener:
        mocked_opener.return_value.open.return_value = (
            FakeHttpResponse(200)
        )

        client.get_authenticated_user(
            site_url="https://example.com",
            username="admin",
            application_password="test-password",
        )

        handlers = mocked_opener.call_args.args

    assert any(
        handler.__class__.__name__ == "_NoRedirectHandler"
        for handler in handlers
    )
