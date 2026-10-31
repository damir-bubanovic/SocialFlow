
import base64
import io
import json
from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest

from socialflow.infrastructure.wordpress.wordpress_category import (
    WordPressCategory,
)
from socialflow.infrastructure.wordpress.urllib_wordpress_category_client import (
    UrllibWordPressCategoryClient,
)


class FakeResponse:
    def __init__(self, payload, total_pages=1):
        self._stream = io.BytesIO(
            json.dumps(payload).encode("utf-8")
        )
        self.headers = {
            "X-WP-TotalPages": str(total_pages)
        }

    def read(self, size=-1):
        return self._stream.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self._stream.close()


class FakeOpener:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []
        self.timeouts = []

    def open(self, request, timeout):
        self.requests.append(request)
        self.timeouts.append(timeout)
        response = next(self.responses)

        if isinstance(response, Exception):
            raise response

        return response


def patched_client(opener):
    return patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_category_client.build_opener",
        return_value=opener,
    )


def test_retrieves_parent_and_child_categories():
    opener = FakeOpener([
        FakeResponse([
            {"id": 10, "name": "Technology", "parent": 0},
            {"id": 20, "name": "Python", "parent": 10},
        ])
    ])

    with patched_client(opener):
        categories = UrllibWordPressCategoryClient(
            timeout=5
        ).list_categories(
            "https://example.com", "admin", "secret"
        )

    assert categories == (
        WordPressCategory(10, "Technology"),
        WordPressCategory(20, "Python", 10),
    )
    request = opener.requests[0]
    assert request.full_url.endswith(
        "/wp-json/wp/v2/categories?per_page=100&page=1"
    )
    assert request.get_method() == "GET"
    assert request.get_header("Authorization") == (
        "Basic " + base64.b64encode(
            b"admin:secret"
        ).decode("ascii")
    )
    assert opener.timeouts == [5]


def test_retrieves_multiple_pages():
    opener = FakeOpener([
        FakeResponse(
            [{"id": 10, "name": "Technology", "parent": 0}],
            total_pages=2,
        ),
        FakeResponse(
            [{"id": 20, "name": "Python", "parent": 10}],
            total_pages=2,
        ),
    ])

    with patched_client(opener):
        categories = UrllibWordPressCategoryClient().list_categories(
            "https://example.com", "admin", "secret"
        )

    assert len(categories) == 2
    assert len(opener.requests) == 2
    assert opener.requests[1].full_url.endswith("page=2")


def test_creates_subcategory():
    opener = FakeOpener([
        FakeResponse({"id": 20, "name": "Python", "parent": 10})
    ])

    with patched_client(opener):
        category = UrllibWordPressCategoryClient().create_category(
            "https://example.com",
            "admin",
            "secret",
            " Python ",
            parent_id=10,
        )

    assert category == WordPressCategory(20, "Python", 10)
    request = opener.requests[0]
    assert request.get_method() == "POST"
    assert json.loads(request.data) == {
        "name": "Python",
        "parent": 10,
    }


@pytest.mark.parametrize(
    "site_url",
    [
        "http://example.com",
        "https://user:pass@example.com",
        "https://example.com?token=abc",
        "https://example.com#fragment",
        "https://example.com/wp-json/wp/v2/categories",
        "https://example.com/path/../other",
        "not-a-url",
    ],
)
def test_rejects_unsafe_urls(site_url):
    with pytest.raises(ValueError, match="HTTPS"):
        UrllibWordPressCategoryClient().list_categories(
            site_url, "admin", "secret"
        )


@pytest.mark.parametrize("timeout", [0, -1])
def test_rejects_invalid_timeout(timeout):
    with pytest.raises(ValueError, match="timeout"):
        UrllibWordPressCategoryClient(timeout=timeout)


@pytest.mark.parametrize("parent_id", [-1, True, "10", None])
def test_rejects_invalid_parent_before_request(parent_id):
    with pytest.raises(ValueError, match="parent category ID"):
        UrllibWordPressCategoryClient().create_category(
            "https://example.com",
            "admin",
            "secret",
            "Python",
            parent_id,
        )


def test_rejects_empty_name():
    with pytest.raises(ValueError, match="name"):
        UrllibWordPressCategoryClient().create_category(
            "https://example.com", "admin", "secret", " "
        )


@pytest.mark.parametrize("total_pages", [0, -1, 1001, "bad"])
def test_rejects_invalid_pagination(total_pages):
    opener = FakeOpener([
        FakeResponse([], total_pages=total_pages)
    ])

    with patched_client(opener):
        with pytest.raises(ValueError, match="pagination"):
            UrllibWordPressCategoryClient().list_categories(
                "https://example.com", "admin", "secret"
            )


def test_rejects_incomplete_collection():
    opener = FakeOpener([
        FakeResponse([], total_pages=2)
    ])

    with patched_client(opener):
        with pytest.raises(ValueError, match="incomplete"):
            UrllibWordPressCategoryClient().list_categories(
                "https://example.com", "admin", "secret"
            )


def test_rejects_inconsistent_pagination():
    opener = FakeOpener([
        FakeResponse(
            [{"id": 10, "name": "Technology", "parent": 0}],
            total_pages=2,
        ),
        FakeResponse(
            [{"id": 20, "name": "Python", "parent": 10}],
            total_pages=3,
        ),
    ])

    with patched_client(opener):
        with pytest.raises(ValueError, match="Inconsistent"):
            UrllibWordPressCategoryClient().list_categories(
                "https://example.com", "admin", "secret"
            )


def test_propagates_authentication_error():
    error = HTTPError(
        "https://example.com/wp-json/wp/v2/categories",
        401,
        "Unauthorized",
        Message(),
        None,
    )
    opener = FakeOpener([error])

    with patched_client(opener):
        with pytest.raises(HTTPError) as caught:
            UrllibWordPressCategoryClient().list_categories(
                "https://example.com", "admin", "secret"
            )

    assert caught.value.code == 401


def test_propagates_network_error():
    opener = FakeOpener([URLError("Connection refused")])

    with patched_client(opener):
        with pytest.raises(URLError):
            UrllibWordPressCategoryClient().list_categories(
                "https://example.com", "admin", "secret"
            )


def test_rejects_unexpected_creation_parent():
    opener = FakeOpener([
        FakeResponse({"id": 20, "name": "Python", "parent": 0})
    ])

    with patched_client(opener):
        with pytest.raises(ValueError, match="unexpected parent"):
            UrllibWordPressCategoryClient().create_category(
                "https://example.com",
                "admin",
                "secret",
                "Python",
                parent_id=10,
            )


def test_recovers_existing_category_with_matching_parent():
    payload = {
        "code": "term_exists",
        "data": {"status": 400, "term_id": 20},
    }
    error = HTTPError(
        "https://example.com/wp-json/wp/v2/categories",
        400,
        "Bad Request",
        Message(),
        io.BytesIO(json.dumps(payload).encode()),
    )
    opener = FakeOpener([
        error,
        FakeResponse([
            {"id": 20, "name": "Python", "parent": 10}
        ]),
    ])

    with patched_client(opener):
        category = UrllibWordPressCategoryClient().create_category(
            "https://example.com",
            "admin",
            "secret",
            "Python",
            parent_id=10,
        )

    assert category == WordPressCategory(20, "Python", 10)


def test_rejects_existing_category_with_different_parent():
    payload = {
        "code": "term_exists",
        "data": {"status": 400, "term_id": 20},
    }
    error = HTTPError(
        "https://example.com/wp-json/wp/v2/categories",
        400,
        "Bad Request",
        Message(),
        io.BytesIO(json.dumps(payload).encode()),
    )
    opener = FakeOpener([
        error,
        FakeResponse([
            {"id": 20, "name": "Python", "parent": 0}
        ]),
    ])

    with patched_client(opener):
        with pytest.raises(ValueError, match="different parent"):
            UrllibWordPressCategoryClient().create_category(
                "https://example.com",
                "admin",
                "secret",
                "Python",
                parent_id=10,
            )
