from email.message import Message
import base64
import json
from io import BytesIO
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from typing import cast

import pytest

from socialflow.infrastructure.wordpress.urllib_wordpress_post_client import (
    UrllibWordPressPostClient,
)
from socialflow.infrastructure.wordpress.wordpress_media import (
    WordPressMedia,
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
            title="WordPress Test Title",
        )

        assert status == 201

    request = opener.open.call_args.args[0]

    assert request.full_url == (
        "https://example.com/wp-json/wp/v2/posts"
    )
    assert request.get_method() == "POST"

    payload = json.loads(request.data.decode("utf-8"))

    assert payload == {
        "title": "WordPress Test Title",
        "content": "Hello WordPress",
        "status": "publish",
    }

    expected_auth = base64.b64encode(
        b"admin:secret"
    ).decode("ascii")

    assert request.get_header("Authorization") == (
        f"Basic {expected_auth}"
    )


@pytest.mark.parametrize("title", ["", " ", "   \t\n"])
def test_create_post_rejects_missing_title(title):
    client = UrllibWordPressPostClient()

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        with pytest.raises(
            ValueError,
            match="WordPress post title must be a non-empty string",
        ):
            client.create_post(
                site_url="https://example.com",
                username="admin",
                application_password="secret",
                content="Hello WordPress",
                title=title,
            )

        build_opener.return_value.open.assert_not_called()


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
            title="WordPress Test Title",
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
            title="Hrvatski naslov",
        )

    request = opener.open.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert payload["content"] == (
        "Č, ć, ž, š, đ — Hrvatski tekst"
    )
    assert payload["title"] == "Hrvatski naslov"


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
            title="WordPress Test Title",
        )

    assert opener.open.call_args.kwargs["timeout"] == 5.0

def test_uploads_wordpress_media(tmp_path):
    image_path = tmp_path / "photo.jpg"
    image_data = b"test-image-data"
    image_path.write_bytes(image_data)

    response = make_response()
    response.read.return_value = (
        b'{"id": 123, '
        b'"source_url": "https://example.com/wp-content/uploads/photo.jpg"}'
    )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()
        media = client.upload_media(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            image_path=image_path,
        )

    assert isinstance(media, WordPressMedia)
    assert media.media_id == 123
    assert media.source_url == (
        "https://example.com/wp-content/uploads/photo.jpg"
    )

    request = opener.open.call_args.args[0]

    assert request.full_url == (
        "https://example.com/wp-json/wp/v2/media"
    )
    assert request.get_method() == "POST"
    assert request.data == image_data

    assert request.get_header("Content-type") == "image/jpeg"
    assert request.get_header("Content-disposition") == (
        'attachment; filename="photo.jpg"'
    )

    expected_auth = base64.b64encode(
        b"admin:secret"
    ).decode("ascii")

    assert request.get_header("Authorization") == (
        f"Basic {expected_auth}"
    )

@pytest.mark.parametrize(
    "response_body",
    [
        b"{}",
        b'{"id": null}',
        b'{"id": 0}',
        b'{"id": -1}',
        b'{"id": "123"}',
        b'{"id": true}',
    ],
)
def test_upload_media_rejects_invalid_media_id(
    tmp_path,
    response_body,
):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"test-image-data")

    response = make_response()
    response.read.return_value = response_body

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.return_value = response

        client = UrllibWordPressPostClient()

        with pytest.raises(
            ValueError,
            match="valid media ID",
        ):
            client.upload_media(
                site_url="https://example.com",
                username="admin",
                application_password="secret",
                image_path=image_path,
            )

@pytest.mark.parametrize(
    "status_code",
    [400, 401, 403, 413, 500],
)
def test_upload_media_propagates_http_errors(
    tmp_path,
    status_code,
):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"test-image-data")

    error = HTTPError(
        url="https://example.com/wp-json/wp/v2/media",
        code=status_code,
        msg="Media upload failed",
        hdrs=Message(),
        fp=BytesIO(b""),
    )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.side_effect = error

        client = UrllibWordPressPostClient()

        with pytest.raises(HTTPError) as exc_info:
            client.upload_media(
                site_url="https://example.com",
                username="admin",
                application_password="secret",
                image_path=image_path,
            )

    assert exc_info.value.code == status_code

@pytest.mark.parametrize(
    "filename",
    [
        "document.pdf",
        "archive.zip",
        "script.py",
        "photo.bmp",
        "image.svg",
        "file.txt",
    ],
)
def test_upload_media_rejects_unsupported_formats(
    tmp_path,
    filename,
):
    image_path = tmp_path / filename
    image_path.write_bytes(b"test-file-data")

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        client = UrllibWordPressPostClient()

        with pytest.raises(
            ValueError,
            match="Unsupported WordPress image format",
        ):
            client.upload_media(
                site_url="https://example.com",
                username="admin",
                application_password="secret",
                image_path=image_path,
            )

        build_opener.assert_not_called()

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
def test_upload_media_rejects_invalid_urls(
    tmp_path,
    url,
):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"test-image-data")

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        client = UrllibWordPressPostClient()

        with pytest.raises(ValueError, match="HTTPS"):
            client.upload_media(
                site_url=url,
                username="admin",
                application_password="secret",
                image_path=image_path,
            )

        build_opener.assert_not_called()

@pytest.mark.parametrize(
    "filename",
    [
        'photo"name.jpg',
        "photo\\name.jpg",
        "photo\nname.jpg",
        "photo\rname.jpg",
    ],
)
def test_upload_media_rejects_unsafe_filenames(
    tmp_path,
    filename,
):
    image_path = tmp_path / filename
    image_path.write_bytes(b"test-image-data")

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        client = UrllibWordPressPostClient()

        with pytest.raises(
            ValueError,
            match="Unsafe image filename",
        ):
            client.upload_media(
                site_url="https://example.com",
                username="admin",
                application_password="secret",
                image_path=image_path,
            )

        build_opener.assert_not_called()

def test_upload_media_returns_media_id_and_source_url(tmp_path):
    image_path = tmp_path / "photo.jpg"
    image_path.write_bytes(b"test-image-data")

    response = make_response()
    response.read.return_value = (
        b'{"id": 123, '
        b'"source_url": "https://example.com/wp-content/uploads/photo.jpg"}'
    )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.return_value = response

        client = UrllibWordPressPostClient()

        media = client.upload_media(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            image_path=image_path,
        )

    assert isinstance(media, WordPressMedia)
    assert media.media_id == 123
    assert media.source_url == (
        "https://example.com/wp-content/uploads/photo.jpg"
    )

def test_deletes_wordpress_media():
    response = make_response()

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()

        client.delete_media(
            site_url="https://example.com",
            username="admin",
            application_password="test-password",
            media_id=123,
        )

        opener.open.assert_called_once()

        request = opener.open.call_args.args[0]

        assert request.get_method() == "DELETE"

        assert request.full_url == (
            "https://example.com/wp-json/wp/v2/media/"
            "123?force=true"
        )

        assert request.get_header("Accept") == "application/json"

        assert request.get_header("Authorization").startswith("Basic ")

        assert opener.open.call_args.kwargs["timeout"] == 10.0

@pytest.mark.parametrize(
    "media_id",
    [
        0,
        -1,
        True,
        False,
        "123",
        None,
        12.5,
    ],
)
def test_delete_media_rejects_invalid_media_id(media_id):
    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        client = UrllibWordPressPostClient()

        with pytest.raises(
            ValueError,
            match="valid WordPress media ID",
        ):
            client.delete_media(
                site_url="https://example.com",
                username="admin",
                application_password="test-password",
                media_id=media_id,
            )

        build_opener.assert_not_called()

@pytest.mark.parametrize(
    "status_code",
    [400, 401, 403, 404, 500],
)
def test_delete_media_propagates_http_errors(status_code):
    error = HTTPError(
        url="https://example.com/wp-json/wp/v2/media/123?force=true",
        code=status_code,
        msg="Media deletion failed",
        hdrs=Message(),
        fp=BytesIO(b""),
    )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.side_effect = error

        client = UrllibWordPressPostClient()

        with pytest.raises(HTTPError) as exc_info:
            client.delete_media(
                site_url="https://example.com",
                username="admin",
                application_password="test-password",
                media_id=123,
            )

        assert exc_info.value.code == status_code

        build_opener.return_value.open.assert_called_once()

def test_lists_recent_wordpress_posts():
    response = make_response(status=200)
    response.read.return_value = json.dumps(
        [
            {
                "id": 42,
                "date": "2026-10-14T10:30:00",
                "content": {
                    "rendered": "<p>Hello WordPress</p>"
                },
                "status": "publish",
            }
        ]
    ).encode("utf-8")

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()

        posts = client.list_recent_posts(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            limit=5,
        )

    assert posts == [
        {
            "id": 42,
            "date": "2026-10-14T10:30:00",
            "content": {
                "rendered": "<p>Hello WordPress</p>"
            },
            "status": "publish",
        }
    ]

    request = opener.open.call_args.args[0]

    assert request.full_url == (
        "https://example.com/wp-json/wp/v2/posts"
        "?per_page=5&orderby=date&order=desc"
    )
    assert request.get_method() == "GET"
    assert opener.open.call_args.kwargs["timeout"] == 10.0

def test_updates_existing_wordpress_post():
    response = make_response(status=200)

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient(timeout=5.0)

        status = client.update_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=123,
            content="Ažurirani sadržaj čćžšđ",
        )

    assert status == 200

    request = opener.open.call_args.args[0]

    assert request.full_url == (
        "https://example.com/wp-json/wp/v2/posts/123"
    )
    assert request.get_method() == "POST"

    payload = json.loads(request.data.decode("utf-8"))

    assert payload == {
        "content": "Ažurirani sadržaj čćžšđ",
    }
    assert "status" not in payload

    expected_auth = base64.b64encode(
        b"admin:secret"
    ).decode("ascii")

    assert request.get_header("Authorization") == (
        f"Basic {expected_auth}"
    )
    assert request.get_header("Content-type") == (
        "application/json; charset=utf-8"
    )

    assert opener.open.call_args.kwargs["timeout"] == 5.0


@pytest.mark.parametrize(
    "post_id",
    [0, -1, True, False, "123", None, 12.5],
)
def test_update_post_rejects_invalid_post_id(post_id):
    client = UrllibWordPressPostClient()

    with pytest.raises(ValueError, match="post ID"):
        client.update_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=post_id,
            content="Updated content",
        )


@pytest.mark.parametrize(
    "status_code",
    [400, 401, 403, 404, 500],
)
def test_update_post_returns_http_error_status(status_code):
    error = HTTPError(
        url="https://example.com/wp-json/wp/v2/posts/123",
        code=status_code,
        msg="Update failed",
        hdrs=Message(),
        fp=BytesIO(b""),
    )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.side_effect = error

        client = UrllibWordPressPostClient()

        status = client.update_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=123,
            content="Updated content",
        )

    assert status == status_code

def test_create_post_includes_wordpress_tag_ids():
    response = make_response(status=201)

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
            tags=(12, 34),
            title="WordPress Test Title",
        )

    assert status == 201

    request = opener.open.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert payload == {
        "title": "WordPress Test Title",
        "content": "Hello WordPress",
        "status": "publish",
        "tags": [12, 34],
    }


@pytest.mark.parametrize(
    "tags",
    [
        (0,),
        (-1,),
        (True,),
        ("12",),
        (12.5,),
        (None,),
    ],
)
def test_create_post_rejects_invalid_tag_ids(tags):
    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        client = UrllibWordPressPostClient()

        with pytest.raises(
            ValueError,
            match="WordPress tag IDs must be positive integers",
        ):
            client.create_post(
                site_url="https://example.com",
                username="admin",
                application_password="secret",
                content="Hello WordPress",
                tags=cast(tuple[int, ...], tags),
            )

        build_opener.assert_not_called()


def test_update_post_includes_wordpress_tag_ids():
    response = make_response(status=200)

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()

        status = client.update_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=123,
            content="Updated content",
            tags=(12, 34),
        )

    assert status == 200

    request = opener.open.call_args.args[0]

    assert request.full_url == (
        "https://example.com/wp-json/wp/v2/posts/123"
    )
    assert request.get_method() == "POST"

    payload = json.loads(request.data.decode("utf-8"))

    assert payload == {
        "content": "Updated content",
        "tags": [12, 34],
    }


def test_update_post_can_remove_all_tags():
    response = make_response(status=200)

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()

        status = client.update_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=123,
            content="Updated content",
            tags=(),
        )

    assert status == 200

    request = opener.open.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert payload == {
        "content": "Updated content",
        "tags": [],
    }


@pytest.mark.parametrize(
    "tags",
    [
        (0,),
        (-1,),
        (True,),
        ("12",),
        (12.5,),
        (None,),
        [12],
    ],
)
def test_update_post_rejects_invalid_tag_ids(tags):
    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        client = UrllibWordPressPostClient()

        with pytest.raises(
            ValueError,
            match="WordPress tag IDs must be positive integers",
        ):
            client.update_post(
                site_url="https://example.com",
                username="admin",
                application_password="secret",
                post_id=123,
                content="Updated content",
                tags=cast(tuple[int, ...], tags),
            )

        build_opener.assert_not_called()

def test_update_post_assigns_featured_image():
    response = make_response(status=200)

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()

        status = client.update_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=123,
            content="Updated content",
            featured_media_id=456,
        )

    assert status == 200

    request = opener.open.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert request.full_url == (
        "https://example.com/wp-json/wp/v2/posts/123"
    )
    assert request.get_method() == "POST"

    assert payload == {
        "content": "Updated content",
        "featured_media": 456,
    }


def test_update_post_removes_featured_image():
    response = make_response(status=200)

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()

        status = client.update_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=123,
            content="Updated content",
            featured_media_id=0,
        )

    assert status == 200

    request = opener.open.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert payload == {
        "content": "Updated content",
        "featured_media": 0,
    }


def test_update_post_preserves_featured_image_when_omitted():
    response = make_response(status=200)

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()

        status = client.update_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=123,
            content="Updated content",
        )

    assert status == 200

    request = opener.open.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert payload == {
        "content": "Updated content",
    }
    assert "featured_media" not in payload


def test_update_post_combines_tags_and_featured_image():
    response = make_response(status=200)

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()

        status = client.update_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=123,
            content="Updated content",
            tags=(12, 34),
            featured_media_id=456,
        )

    assert status == 200

    request = opener.open.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert payload == {
        "content": "Updated content",
        "tags": [12, 34],
        "featured_media": 456,
    }


@pytest.mark.parametrize(
    "featured_media_id",
    [
        -1,
        True,
        False,
        "123",
        12.5,
    ],
)
def test_update_post_rejects_invalid_featured_media_id(
    featured_media_id,
):
    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        client = UrllibWordPressPostClient()

        with pytest.raises(
            ValueError,
            match="WordPress featured media ID",
        ):
            client.update_post(
                site_url="https://example.com",
                username="admin",
                application_password="secret",
                post_id=123,
                content="Updated content",
                featured_media_id=featured_media_id,
            )

        build_opener.assert_not_called()

def test_lists_wordpress_image_media():
    media_items = [
        {
            "id": 123,
            "media_type": "image",
            "source_url": "https://example.com/uploads/photo.jpg",
        },
        {
            "id": 456,
            "media_type": "image",
            "source_url": "https://example.com/uploads/banner.png",
        },
    ]

    response = make_response(status=200)
    response.read.return_value = json.dumps(media_items).encode("utf-8")

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient(timeout=5.0)
        result = client.list_media(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            limit=20,
        )

    assert result == media_items

    request = opener.open.call_args.args[0]
    assert request.get_method() == "GET"
    assert request.full_url == (
        "https://example.com/wp-json/wp/v2/media"
        "?per_page=20&orderby=date&order=desc&media_type=image"
    )
    assert opener.open.call_args.kwargs["timeout"] == 5.0

    expected_auth = base64.b64encode(
        b"admin:secret"
    ).decode("ascii")

    assert request.get_header("Authorization") == (
        f"Basic {expected_auth}"
    )


@pytest.mark.parametrize(
    "limit",
    [0, -1, 101, True, False, "20", 1.5],
)
def test_list_media_rejects_invalid_limit(limit):
    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        client = UrllibWordPressPostClient()

        with pytest.raises(ValueError, match="Media limit"):
            client.list_media(
                "https://example.com",
                "admin",
                "secret",
                limit=limit,
            )

        build_opener.assert_not_called()


@pytest.mark.parametrize(
    "site_url",
    [
        "http://example.com",
        "https://user:password@example.com",
        "https://example.com?token=secret",
        "https://example.com#fragment",
        "not-a-url",
    ],
)
def test_list_media_rejects_invalid_url(site_url):
    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        client = UrllibWordPressPostClient()

        with pytest.raises(ValueError, match="HTTPS"):
            client.list_media(
                site_url,
                "admin",
                "secret",
            )

        build_opener.assert_not_called()


@pytest.mark.parametrize(
    "response_body",
    [
        b'{"id": 123}',
        b'[{"id": 123}, null]',
        b'[1, 2, 3]',
    ],
)
def test_list_media_rejects_invalid_response(response_body):
    response = make_response(status=200)
    response.read.return_value = response_body

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.return_value = response

        client = UrllibWordPressPostClient()

        with pytest.raises(ValueError, match="Invalid WordPress media"):
            client.list_media(
                "https://example.com",
                "admin",
                "secret",
            )


@pytest.mark.parametrize(
    "post_status",
    ("draft", "pending", "private", "publish"),
)
def test_update_post_includes_wordpress_status(post_status):
    response = make_response(status=200)

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()

        result = client.update_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=123,
            content="Updated content",
            status=post_status,
        )

    assert result == 200

    request = opener.open.call_args.args[0]

    assert request.full_url == (
        "https://example.com/wp-json/wp/v2/posts/123"
    )
    assert request.get_method() == "POST"

    payload = json.loads(request.data.decode("utf-8"))

    assert payload == {
        "content": "Updated content",
        "status": post_status,
    }


@pytest.mark.parametrize(
    "post_status",
    ("", "scheduled", "trash", "PUBLISH", 123, True),
)
def test_update_post_rejects_invalid_wordpress_status(post_status):
    client = UrllibWordPressPostClient()

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        with pytest.raises(
            ValueError,
            match="Unsupported WordPress post status",
        ):
            client.update_post(
                site_url="https://example.com",
                username="admin",
                application_password="secret",
                post_id=123,
                content="Updated content",
                status=cast(str, post_status),
            )

    build_opener.assert_not_called()


def test_update_post_combines_status_tags_and_featured_image():
    response = make_response(status=200)

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()

        result = client.update_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=123,
            content="Updated content",
            tags=(10, 20),
            featured_media_id=456,
            status="draft",
        )

    assert result == 200

    request = opener.open.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert payload == {
        "content": "Updated content",
        "tags": [10, 20],
        "featured_media": 456,
        "status": "draft",
    }


@pytest.mark.parametrize(
    "title",
    ["Updated title", "Novi naslov čćžšđ"],
)
def test_update_post_includes_wordpress_title(title):
    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        response = build_opener.return_value.open.return_value
        response.__enter__.return_value.status = 200

        client = UrllibWordPressPostClient()

        result = client.update_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=123,
            content="Updated content",
            title=title,
        )

        assert result == 200

        request = build_opener.return_value.open.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))

        assert payload == {
            "content": "Updated content",
            "title": title,
        }


@pytest.mark.parametrize(
    "title",
    ["", "   ", 123, True, []],
)
def test_update_post_rejects_invalid_wordpress_title(title):
    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        client = UrllibWordPressPostClient()

        with pytest.raises(
            ValueError,
            match="WordPress post title",
        ):
            client.update_post(
                site_url="https://example.com",
                username="admin",
                application_password="secret",
                post_id=123,
                content="Updated content",
                title=title,
            )

        build_opener.assert_not_called()



def test_trash_post_uses_delete_without_force():
    response = make_response(status=200)
    response.read.return_value = json.dumps({
        "id": 123,
        "status": "trash",
    }).encode("utf-8")

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()
        result = client.trash_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=123,
        )

    assert result == 200

    request = opener.open.call_args.args[0]
    assert request.get_method() == "DELETE"
    assert request.full_url == (
        "https://example.com/wp-json/wp/v2/posts/123"
    )
    assert "force=true" not in request.full_url

    expected_auth = base64.b64encode(
        b"admin:secret"
    ).decode("ascii")

    assert request.get_header("Authorization") == (
        f"Basic {expected_auth}"
    )


@pytest.mark.parametrize(
    "invalid_id",
    [0, -1, True, "123", None],
)
def test_trash_post_rejects_invalid_id(invalid_id):
    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        client = UrllibWordPressPostClient()

        with pytest.raises(
            ValueError,
            match="WordPress post ID",
        ):
            client.trash_post(
                site_url="https://example.com",
                username="admin",
                application_password="secret",
                post_id=invalid_id,
            )

        build_opener.assert_not_called()


@pytest.mark.parametrize(
    "invalid_url",
    [
        "http://example.com",
        "https://user:password@example.com",
        "https://example.com?token=secret",
        "https://example.com#fragment",
    ],
)
def test_trash_post_rejects_invalid_site_url(invalid_url):
    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        client = UrllibWordPressPostClient()

        with pytest.raises(
            ValueError,
            match="HTTPS WordPress URL",
        ):
            client.trash_post(
                site_url=invalid_url,
                username="admin",
                application_password="secret",
                post_id=123,
            )

        build_opener.assert_not_called()


def test_trash_post_returns_http_error_status():
    error = HTTPError(
        url="https://example.com/wp-json/wp/v2/posts/123",
        code=403,
        msg="Forbidden",
        hdrs=Message(),
        fp=BytesIO(b""),
    )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.side_effect = error

        client = UrllibWordPressPostClient()
        result = client.trash_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=123,
        )

    assert result == 403


@pytest.mark.parametrize(
    "payload",
    [
        {"id": 123, "status": "publish"},
        {"id": 999, "status": "trash"},
        {"id": 123},
        [],
    ],
)
def test_trash_post_requires_trash_confirmation(payload):
    response = make_response(status=200)
    response.read.return_value = json.dumps(
        payload
    ).encode("utf-8")

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.return_value = response

        client = UrllibWordPressPostClient()

        with pytest.raises(
            ValueError,
            match="did not confirm",
        ):
            client.trash_post(
                site_url="https://example.com",
                username="admin",
                application_password="secret",
                post_id=123,
            )



def test_restore_post_sets_draft_status():
    response = make_response(status=200)
    response.read.return_value = b'{"id":42,"status":"draft"}'

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()
        status = client.restore_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=42,
        )

    assert status == 200

    request = opener.open.call_args.args[0]

    assert request.full_url == (
        "https://example.com/wp-json/wp/v2/posts/42"
    )
    assert request.get_method() == "POST"
    assert json.loads(request.data.decode("utf-8")) == {
        "status": "draft",
    }
    assert request.get_header("Content-type") == (
        "application/json"
    )


@pytest.mark.parametrize("post_id", [
    0, -1, True, "42", None,
])
def test_restore_post_rejects_invalid_id(post_id):
    client = UrllibWordPressPostClient()

    with pytest.raises(ValueError):
        client.restore_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=post_id,
        )


@pytest.mark.parametrize("site_url", [
    "http://example.com",
    "https://",
    "https://admin:secret@example.com",
    "https://example.com?token=secret",
    "https://example.com#fragment",
])
def test_restore_post_rejects_invalid_site_url(site_url):
    client = UrllibWordPressPostClient()

    with pytest.raises(ValueError):
        client.restore_post(
            site_url=site_url,
            username="admin",
            application_password="secret",
            post_id=42,
        )


def test_restore_post_returns_http_error_status():
    error = HTTPError(
        url="https://example.com/wp-json/wp/v2/posts/42",
        code=403,
        msg="Forbidden",
        hdrs=Message(),
        fp=BytesIO(b""),
    )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.side_effect = error

        client = UrllibWordPressPostClient()
        status = client.restore_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            post_id=42,
        )

    assert status == 403


@pytest.mark.parametrize("payload", [
    {"id": 42, "status": "trash"},
    {"id": 99, "status": "draft"},
    {"id": 42},
    [],
])
def test_restore_post_requires_draft_confirmation(payload):
    response = make_response(status=200)
    response.read.return_value = json.dumps(payload).encode("utf-8")

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.return_value = response

        client = UrllibWordPressPostClient()

        with pytest.raises(ValueError, match="restored as a draft"):
            client.restore_post(
                site_url="https://example.com",
                username="admin",
                application_password="secret",
                post_id=42,
            )



def test_list_trashed_posts_uses_authenticated_edit_context():
    posts = [
        {"id": 42, "status": "trash"},
        {"id": 99, "status": "trash"},
    ]

    response = make_response(status=200)
    response.read.return_value = json.dumps(posts).encode("utf-8")

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        opener = build_opener.return_value
        opener.open.return_value = response

        client = UrllibWordPressPostClient()
        result = client.list_trashed_posts(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            limit=25,
        )

    assert result == posts

    request = opener.open.call_args.args[0]

    assert request.get_method() == "GET"
    assert request.full_url == (
        "https://example.com/wp-json/wp/v2/posts"
        "?status=trash&context=edit&per_page=25"
        "&orderby=date&order=desc"
    )

    expected_auth = base64.b64encode(
        b"admin:secret"
    ).decode("ascii")

    assert request.get_header("Authorization") == (
        f"Basic {expected_auth}"
    )
    assert request.get_header("Accept") == "application/json"


@pytest.mark.parametrize(
    "invalid_limit",
    [0, -1, 101, True, False, "25", None, 1.5],
)
def test_list_trashed_posts_rejects_invalid_limit(invalid_limit):
    client = UrllibWordPressPostClient()

    with pytest.raises(ValueError, match="Post limit"):
        client.list_trashed_posts(
            "https://example.com",
            "admin",
            "secret",
            limit=invalid_limit,
        )


@pytest.mark.parametrize(
    "site_url",
    [
        "http://example.com",
        "https://",
        "https://admin:secret@example.com",
        "https://example.com?token=secret",
        "https://example.com#fragment",
    ],
)
def test_list_trashed_posts_rejects_invalid_site_url(site_url):
    client = UrllibWordPressPostClient()

    with pytest.raises(ValueError, match="HTTPS WordPress URL"):
        client.list_trashed_posts(
            site_url,
            "admin",
            "secret",
        )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        None,
        "invalid",
        [42],
        [{"id": 42, "status": "publish"}],
        [{"id": 42}],
    ],
)
def test_list_trashed_posts_rejects_invalid_response(payload):
    response = make_response(status=200)
    response.read.return_value = json.dumps(payload).encode("utf-8")

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.return_value = response

        client = UrllibWordPressPostClient()

        with pytest.raises(ValueError, match="trashed"):
            client.list_trashed_posts(
                "https://example.com",
                "admin",
                "secret",
            )


def test_list_trashed_posts_accepts_empty_trash():
    response = make_response(status=200)
    response.read.return_value = b"[]"

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.return_value = response

        client = UrllibWordPressPostClient()

        assert client.list_trashed_posts(
            "https://example.com",
            "admin",
            "secret",
        ) == []


def test_list_trashed_posts_propagates_http_failure():
    error = HTTPError(
        url="https://example.com/wp-json/wp/v2/posts",
        code=403,
        msg="Forbidden",
        hdrs=Message(),
        fp=BytesIO(b""),
    )

    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.side_effect = error

        client = UrllibWordPressPostClient()

        with pytest.raises(HTTPError) as raised:
            client.list_trashed_posts(
                "https://example.com",
                "admin",
                "secret",
            )

    assert raised.value.code == 403



def test_create_post_includes_selected_categories_in_payload():
    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.return_value = make_response()

        client = UrllibWordPressPostClient()
        client.create_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            content="Hello WordPress",
            title="Category Test",
            categories=(10, 20),
        )

    request = build_opener.return_value.open.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert payload["categories"] == [10, 20]


def test_create_post_omits_categories_when_none_selected():
    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        build_opener.return_value.open.return_value = make_response()

        client = UrllibWordPressPostClient()
        client.create_post(
            site_url="https://example.com",
            username="admin",
            application_password="secret",
            content="Hello WordPress",
            title="Category Test",
        )

    request = build_opener.return_value.open.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    assert "categories" not in payload


@pytest.mark.parametrize(
    "categories",
    [
        (0,),
        (-1,),
        ("10",),
        (True,),
        (1.5,),
    ],
)
def test_create_post_rejects_invalid_category_ids(categories):
    with patch(
        "socialflow.infrastructure.wordpress."
        "urllib_wordpress_post_client.build_opener"
    ) as build_opener:
        client = UrllibWordPressPostClient()

        with pytest.raises(
            ValueError,
            match="WordPress category IDs must be positive integers",
        ):
            client.create_post(
                site_url="https://example.com",
                username="admin",
                application_password="secret",
                content="Hello WordPress",
                title="Category Test",
                categories=cast(tuple[int, ...], categories),
            )

        build_opener.assert_not_called()
