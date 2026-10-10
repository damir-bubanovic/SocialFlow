from email.message import Message
import base64
import json
from io import BytesIO
from unittest.mock import Mock, patch
from urllib.error import HTTPError

import pytest

from socialflow.infrastructure.wordpress.urllib_wordpress_post_client import (
    UrllibWordPressPostClient,
)


def make_response(status=201):
    response = Mock()
    response.status = status
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    return response


def test_creates_wordpress_post():
    response = make_response()

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()
        status = client.create_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            content="Hello WordPress",
        )

    assert status == 201

    request = opener.open.call_args.args[0]

    assert request.full_url == (
        "https://example.com/wp-json/wp/v2/posts"
    )
    assert request.get_method() == "POST"

    payload = json.loads(request.data.decode("utf-8"))

    assert payload == {
        "content": "Hello WordPress",
        "status": "publish",
    }

    expected_auth = base64.b64encode(
        b"admin:secret"
    ).decode("ascii")

    assert request.get_header("Authorization") == (
        f"Basic {expected_auth}"
    )


def test_returns_http_error_status():
    error = HTTPError(
        url="https://example.com/wp-json/wp/v2/posts",
        code=401,
        msg="Unauthorized",
        hdrs=Message(),
        fp=BytesIO(b""),
    )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.side_effect = error

        client = UrllibWordPressPostClient()

        status = client.create_post(
            "https://example.com",
            "admin",
            "wrong-password",
            "Test",
        )

    assert status == 401


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://user:password@example.com",
        "https://example.com?token=secret",
        "https://example.com#fragment",
        "not-a-url",
    ],
)
def test_rejects_invalid_urls(url):
    client = UrllibWordPressPostClient()

    with pytest.raises(ValueError, match="HTTPS"):
        client.create_post(
            url,
            "admin",
            "secret",
            "Test",
        )


def test_rejects_invalid_timeout():
    with pytest.raises(ValueError, match="timeout"):
        UrllibWordPressPostClient(timeout=0)


def test_preserves_unicode_content():
    response = make_response()

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()

        client.create_post(
            "https://example.com",
            "admin",
            "secret",
            "Č, ć, ž, š, đ — Hrvatski tekst",
        )

    request = opener.open.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert payload["content"] == (
        "Č, ć, ž, š, đ — Hrvatski tekst"
    )


def test_uses_configured_timeout():
    response = make_response()

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient(timeout=5.0)

        client.create_post(
            "https://example.com",
            "admin",
            "secret",
            "Test",
        )

    assert opener.open.call_args.kwargs["timeout"] == 5.0
