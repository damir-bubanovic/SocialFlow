import base64
import io
import json
from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest
from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag
from socialflow.infrastructure.wordpress.urllib_wordpress_tag_client import (
    UrllibWordPressTagClient,
)


class FakeResponse:
    def __init__(self, payload, total_pages=1):
        self._stream = io.BytesIO(
            json.dumps(payload).encode("utf-8")
        )
        self.headers = {
            "X-WP-TotalPages": str(total_pages),
        }

    def read(self, size=-1):
        return self._stream.read(size)

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self._stream.close()


class FakeOpener:
    def __init__(self, payload, total_pages=1):
        self.payload = payload
        self.total_pages = total_pages
        self.request = None
        self.timeout = None
        self.requests = []

    def open(self, request, timeout):
        self.request = request
        self.timeout = timeout
        self.requests.append(request)

        return FakeResponse(
            self.payload,
            self.total_pages,
        )


def test_tag_client_retrieves_tags() -> None:
    opener = FakeOpener([
        {"id": 12, "name": "Python"},
        {"id": 34, "name": "SocialFlow"},
    ])

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=opener,
    ):
        client = UrllibWordPressTagClient(timeout=5.0)

        tags = client.list_tags(
            "https://example.com",
            "admin",
            "secret",
        )

    assert tags == (
        WordPressTag(id=12, name="Python"),
        WordPressTag(id=34, name="SocialFlow"),
    )
    assert opener.request.full_url == (
        "https://example.com/wp-json/wp/v2/tags"
        "?per_page=100&page=1"
    )
    assert opener.request.get_method() == "GET"
    assert opener.request.get_header("Accept") == "application/json"
    assert opener.request.get_header("Authorization") == (
        "Basic " + base64.b64encode(
            b"admin:secret"
        ).decode("ascii")
    )
    assert opener.timeout == 5.0
    assert len(opener.requests) == 1


@pytest.mark.parametrize(
    "site_url",
    [
        "http://example.com",
        "https://user:pass@example.com",
        "https://example.com?token=abc",
        "https://example.com#fragment",
        "not-a-url",
        "https://example.com:invalid",
        "https://example.com/wp-json/wp/v2/tags",
        "https://example.com/path/../other",
    ],
)
def test_tag_client_rejects_invalid_urls(site_url) -> None:
    client = UrllibWordPressTagClient()

    with pytest.raises(ValueError, match="HTTPS"):
        client.list_tags(site_url, "admin", "secret")


@pytest.mark.parametrize("timeout", [0, -1])
def test_tag_client_rejects_invalid_timeout(timeout) -> None:
    with pytest.raises(ValueError, match="timeout"):
        UrllibWordPressTagClient(timeout=timeout)


def test_tag_client_rejects_invalid_response() -> None:
    opener = FakeOpener({"unexpected": "object"})

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=opener,
    ):
        with pytest.raises(ValueError, match="tags response"):
            UrllibWordPressTagClient().list_tags(
                "https://example.com",
                "admin",
                "secret",
            )


def test_tag_client_retrieves_multiple_pages() -> None:
    class PaginatedOpener:
        def __init__(self):
            self.requests = []

        def open(self, request, timeout):
            _ = timeout
            self.requests.append(request)

            page = len(self.requests)

            if page == 1:
                return FakeResponse(
                    [{"id": 10, "name": "Python"}],
                    total_pages=2,
                )

            return FakeResponse(
                [{"id": 20, "name": "SocialFlow"}],
                total_pages=2,
            )

    opener = PaginatedOpener()

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=opener,
    ):
        tags = UrllibWordPressTagClient().list_tags(
            "https://example.com",
            "admin",
            "secret",
        )

    assert tags == (
        WordPressTag(id=10, name="Python"),
        WordPressTag(id=20, name="SocialFlow"),
    )

    assert len(opener.requests) == 2
    assert opener.requests[0].full_url.endswith(
        "per_page=100&page=1"
    )
    assert opener.requests[1].full_url.endswith(
        "per_page=100&page=2"
    )


@pytest.mark.parametrize(
    "total_pages",
    [0, -1, 1001, "invalid"],
)
def test_tag_client_rejects_invalid_pagination(
    total_pages,
) -> None:
    opener = FakeOpener(
        [{"id": 10, "name": "Python"}],
        total_pages=total_pages,
    )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=opener,
    ):
        with pytest.raises(ValueError, match="pagination"):
            UrllibWordPressTagClient().list_tags(
                "https://example.com",
                "admin",
                "secret",
            )


def test_tag_client_rejects_empty_intermediate_page() -> None:
    opener = FakeOpener([], total_pages=2)

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=opener,
    ):
        with pytest.raises(ValueError, match="incomplete"):
            UrllibWordPressTagClient().list_tags(
                "https://example.com",
                "admin",
                "secret",
            )


def test_tag_client_rejects_inconsistent_pagination_headers() -> None:
    class InconsistentOpener:
        def __init__(self):
            self.request_count = 0

        def open(self, request, timeout):
            _ = (request, timeout)
            self.request_count += 1

            if self.request_count == 1:
                return FakeResponse(
                    [{"id": 10, "name": "Python"}],
                    total_pages=2,
                )

            return FakeResponse(
                [{"id": 20, "name": "SocialFlow"}],
                total_pages=3,
            )

    opener = InconsistentOpener()

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=opener,
    ):
        with pytest.raises(
            ValueError,
            match="Inconsistent WordPress pagination",
        ):
            UrllibWordPressTagClient().list_tags(
                "https://example.com",
                "admin",
                "secret",
            )

    assert opener.request_count == 2


def test_tag_client_rejects_missing_pagination_on_later_page() -> None:
    class MissingHeaderOpener:
        def __init__(self):
            self.request_count = 0

        def open(self, request, timeout):
            _ = (request, timeout)
            self.request_count += 1

            response = FakeResponse(
                [{"id": self.request_count, "name": "Python"}],
                total_pages=2,
            )

            if self.request_count == 2:
                response.headers.pop("X-WP-TotalPages")

            return response

    opener = MissingHeaderOpener()

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=opener,
    ):
        with pytest.raises(
            ValueError,
            match="Invalid WordPress pagination header",
        ):
            UrllibWordPressTagClient().list_tags(
                "https://example.com",
                "admin",
                "secret",
            )

    assert opener.request_count == 2

def test_tag_client_propagates_http_error() -> None:
    class FailingOpener:
        @staticmethod
        def open(request, timeout):
            _ = (request, timeout)

            raise HTTPError(
                url="https://example.com/wp-json/wp/v2/tags",
                code=401,
                msg="Unauthorized",
                hdrs=Message(),
                fp=None,
            )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=FailingOpener(),
    ):
        with pytest.raises(HTTPError) as error:
            UrllibWordPressTagClient().list_tags(
                "https://example.com",
                "admin",
                "secret",
            )

    assert error.value.code == 401


def test_tag_client_propagates_network_error() -> None:
    class FailingOpener:
        @staticmethod
        def open(request, timeout):
            _ = (request, timeout)
            raise URLError("Connection refused")

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=FailingOpener(),
    ):
        with pytest.raises(URLError):
            UrllibWordPressTagClient().list_tags(
                "https://example.com",
                "admin",
                "secret",
            )


def test_tag_client_does_not_log_credentials(
    caplog,
) -> None:
    class FailingOpener:
        @staticmethod
        def open(request, timeout):
            _ = (request, timeout)
            raise URLError("Connection refused")

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=FailingOpener(),
    ):
        with pytest.raises(URLError):
            UrllibWordPressTagClient().list_tags(
                "https://example.com",
                "admin",
                "super-secret-password",
            )

    assert "super-secret-password" not in caplog.text
    assert "admin:super-secret-password" not in caplog.text


def test_tag_client_creates_tag() -> None:
    opener = FakeOpener({"id": 42, "name": "Python"})

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=opener,
    ):
        client = UrllibWordPressTagClient(timeout=5.0)

        tag = client.create_tag(
            "https://example.com",
            "admin",
            "secret",
            "  Python  ",
        )

    assert tag == WordPressTag(id=42, name="Python")
    assert opener.request.full_url == (
        "https://example.com/wp-json/wp/v2/tags"
    )
    assert opener.request.get_method() == "POST"
    assert json.loads(
        opener.request.data.decode("utf-8")
    ) == {"name": "Python"}
    assert opener.request.get_header("Content-type") == (
        "application/json"
    )
    assert opener.request.get_header("Authorization") == (
        "Basic " + base64.b64encode(
            b"admin:secret"
        ).decode("ascii")
    )
    assert opener.timeout == 5.0


@pytest.mark.parametrize(
    "name",
    ["", " ", "\t\n"],
)
def test_tag_client_rejects_empty_tag_name(name: str) -> None:
    client = UrllibWordPressTagClient()

    with pytest.raises(ValueError, match="name"):
        client.create_tag(
            "https://example.com",
            "admin",
            "secret",
            name,
        )


def test_tag_client_rejects_invalid_creation_response() -> None:
    opener = FakeOpener({"id": "invalid", "name": "Python"})

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=opener,
    ):
        with pytest.raises(ValueError, match="tag ID"):
            UrllibWordPressTagClient().create_tag(
                "https://example.com",
                "admin",
                "secret",
                "Python",
            )


def test_tag_client_creation_propagates_http_error() -> None:
    class FailingOpener:
        @staticmethod
        def open(request, timeout):
            _ = (request, timeout)
            raise HTTPError(
                url="https://example.com/wp-json/wp/v2/tags",
                code=403,
                msg="Forbidden",
                hdrs=Message(),
                fp=None,
            )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=FailingOpener(),
    ):
        with pytest.raises(HTTPError) as error:
            UrllibWordPressTagClient().create_tag(
                "https://example.com",
                "admin",
                "secret",
                "Python",
            )

    assert error.value.code == 403

def test_tag_client_recovers_when_tag_already_exists() -> None:
    class DuplicateTagOpener:
        @staticmethod
        def open(request, timeout):
            _ = timeout

            error_payload = {
                "code": "term_exists",
                "message": "A term with the name provided already exists.",
                "data": {
                    "status": 400,
                    "term_id": 42,
                },
            }

            raise HTTPError(
                url=request.full_url,
                code=400,
                msg="Bad Request",
                hdrs=Message(),
                fp=io.BytesIO(
                    json.dumps(error_payload).encode("utf-8")
                ),
            )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=DuplicateTagOpener(),
    ):
        tag = UrllibWordPressTagClient().create_tag(
            "https://example.com",
            "admin",
            "secret",
            "Python",
        )

    assert tag == WordPressTag(id=42, name="Python")

@pytest.mark.parametrize(
    ("http_status", "error_payload"),
    [
        (400, {"code": "invalid_term", "data": {"status": 400, "term_id": 42}}),
        (400, {"code": "term_exists", "data": {"status": 400}}),
        (400, {"code": "term_exists", "data": {"status": 400, "term_id": 0}}),
        (400, {"code": "term_exists", "data": {"status": 400, "term_id": -1}}),
        (400, {"code": "term_exists", "data": {"status": 400, "term_id": True}}),
        (400, {"code": "term_exists", "data": {"status": 400, "term_id": "42"}}),
        (400, {"code": "term_exists", "data": {"status": 403, "term_id": 42}}),
        (403, {"code": "term_exists", "data": {"status": 400, "term_id": 42}}),
        (500, {"code": "term_exists", "data": {"status": 400, "term_id": 42}}),
        (400, ["term_exists"]),
        (400, None),
    ],
)
def test_create_tag_rejects_invalid_duplicate_responses(
    http_status,
    error_payload,
):
    class ErrorOpener:
        @staticmethod
        def open(request, timeout):
            _ = timeout

            raise HTTPError(
                url=request.full_url,
                code=http_status,
                msg="WordPress API Error",
                hdrs=Message(),
                fp=io.BytesIO(
                    json.dumps(error_payload).encode("utf-8")
                ),
            )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=ErrorOpener(),
    ):
        with pytest.raises(HTTPError) as captured:
            UrllibWordPressTagClient().create_tag(
                "https://example.com",
                "admin",
                "secret",
                "Python",
            )

    assert captured.value.code == http_status

@pytest.mark.parametrize(
    "response_body",
    [
        b"",
        b"{invalid json",
        b'{"code": "term_exists",',
        b"\xff\xfe\xfa",
    ],
)
def test_create_tag_rejects_malformed_duplicate_error_body(
    response_body: bytes,
) -> None:
    class MalformedResponseOpener:
        @staticmethod
        def open(request, timeout):
            raise HTTPError(
                url=request.full_url,
                code=400,
                msg="Bad Request",
                hdrs=Message(),
                fp=io.BytesIO(response_body),
            )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_tag_client.build_opener",
        return_value=MalformedResponseOpener(),
    ):
        with pytest.raises(HTTPError) as captured:
            UrllibWordPressTagClient().create_tag(
                "https://example.com",
                "admin",
                "secret",
                "Python",
            )

    assert captured.value.code == 400