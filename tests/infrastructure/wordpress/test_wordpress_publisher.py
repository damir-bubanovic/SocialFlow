from types import SimpleNamespace
from unittest.mock import Mock
from pathlib import Path
import pytest

from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_publisher import (
    WordPressPublisher,
)
from socialflow.application.publishing.prepared_post import PreparedPost
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.infrastructure.wordpress.wordpress_media import (
    WordPressMedia,
)
from socialflow.domain.post.tag import Tag
from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag


def make_account(
    site_url="https://example.com",
    username="admin",
):
    config = Mock()
    config.is_complete.return_value = True
    config.normalized.return_value = SimpleNamespace(
        site_url=site_url,
        username=username,
    )

    return SimpleNamespace(
        id="test-wordpress-account",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=config,
    )


def make_post(text: str = "Hello WordPress") -> PreparedPost:
    post = Post(
        text=text,
        language=Language.ENGLISH,
        title="WordPress Test Title",
    )

    return PreparedPost(source=post)


def make_publisher(
    account=None,
    password: str | None = "secret",
    status: int = 201,
):
    account = account or make_account()

    credentials = Mock()
    credentials.get.return_value = password

    client = Mock()
    client.create_post.return_value = status

    publisher = WordPressPublisher(
        account=account,
        credential_store=credentials,
        post_client=client,
    )

    return publisher, credentials, client


def test_successful_wordpress_publication():
    publisher, credentials, client = make_publisher()

    publisher.publish(make_post())

    client.create_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
        content="Hello WordPress",
        tags=(),
        title="WordPress Test Title",
        categories=(),
    )

@pytest.mark.parametrize("title", ["", " ", "   \t\n"])
def test_rejects_missing_wordpress_title(title):
    publisher, credentials, client = make_publisher()

    post = PreparedPost(
        source=Post(
            text="Hello WordPress",
            language=Language.ENGLISH,
            title=title,
        )
    )

    with pytest.raises(
        ValueError,
        match="WordPress post title is required",
    ):
        publisher.publish(post)

    client.create_post.assert_not_called()


def test_trims_wordpress_title_before_publishing():
    publisher, credentials, client = make_publisher()

    post = PreparedPost(
        source=Post(
            text="Hello WordPress",
            language=Language.ENGLISH,
            title="  WordPress Test Title  ",
        )
    )

    publisher.publish(post)

    assert (
        client.create_post.call_args.kwargs["title"]
        == "WordPress Test Title"
    )

def test_missing_application_password():
    publisher, credentials, client = make_publisher(password=None)

    with pytest.raises(ValueError, match="password is missing"):
        publisher.publish(make_post())

    client.create_post.assert_not_called()


def test_rejects_http_failure():
    publisher, credentials, client = make_publisher(status=401)

    with pytest.raises(RuntimeError, match="HTTP 401"):
        publisher.publish(make_post())


def test_rejects_insecure_wordpress_url():
    publisher, credentials, client = make_publisher(
        account=make_account(site_url="http://example.com")
    )

    with pytest.raises(ValueError, match="HTTPS"):
        publisher.publish(make_post())

    client.create_post.assert_not_called()


def test_rejects_unprepared_images():
    publisher, credentials, client = make_publisher()

    post = PreparedPost(
        source=Post(
            text="Hello WordPress",
            language=Language.ENGLISH,
            title="WordPress Test Title",
            images=(Mock(),),
        ),
        images=(),
    )

    with pytest.raises(
        ValueError,
        match="images must be prepared",
    ):
        publisher.publish(post)

    client.upload_media.assert_not_called()
    client.create_post.assert_not_called()


def test_rejects_empty_post():
    publisher, credentials, client = make_publisher()

    with pytest.raises(ValueError, match="post text is required"):
        publisher.publish(make_post(text="   "))

    client.create_post.assert_not_called()

def test_publishes_wordpress_post_with_image():
    publisher, credentials, client = make_publisher()

    image = Mock()
    image.path = Path("/tmp/wordpress-photo.jpg")

    post = PreparedPost(
        source=Post(
            text="Hello WordPress",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=(image,),
    )

    client.upload_media.return_value = WordPressMedia(
        media_id=123,
        source_url="https://example.com/wp-content/uploads/photo.jpg",
    )

    publisher.publish(post)

    client.upload_media.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
        image_path=image.path,
    )

    client.create_post.assert_called_once()

    content = client.create_post.call_args.kwargs["content"]

    assert "Hello WordPress" in content
    assert '<!-- wp:image {"id":123} -->' in content
    assert (
            'src="https://example.com/wp-content/uploads/photo.jpg"'
            in content
    )
    assert 'class="wp-image-123"' in content
    assert "<!-- /wp:image -->" in content

def test_publishes_wordpress_post_with_multiple_images():
    publisher, credentials, client = make_publisher()

    first_image = Mock()
    first_image.path = Path("/tmp/first.jpg")

    second_image = Mock()
    second_image.path = Path("/tmp/second.jpg")

    post = PreparedPost(
        source=Post(
            text="Two WordPress images",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=(first_image, second_image),
    )

    client.upload_media.side_effect = [
        WordPressMedia(
            media_id=123,
            source_url="https://example.com/uploads/first.jpg",
        ),
        WordPressMedia(
            media_id=456,
            source_url="https://example.com/uploads/second.jpg",
        ),
    ]

    publisher.publish(post)

    assert client.upload_media.call_count == 2
    assert [
        call.kwargs["image_path"]
        for call in client.upload_media.call_args_list
    ] == [
        first_image.path,
        second_image.path,
    ]

    client.create_post.assert_called_once()

    content = client.create_post.call_args.kwargs["content"]

    assert content.startswith("Two WordPress images")
    assert '<!-- wp:image {"id":123} -->' in content
    assert '<!-- wp:image {"id":456} -->' in content
    assert 'src="https://example.com/uploads/first.jpg"' in content
    assert 'src="https://example.com/uploads/second.jpg"' in content

    assert content.index("wp-image-123") < content.index("wp-image-456")

def test_publishes_wordpress_image_with_escaped_url():
    publisher, credentials, client = make_publisher()

    image = Mock()
    image.path = Path("/tmp/photo.jpg")

    post = PreparedPost(
        source=Post(
            text="WordPress image",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=(image,),
    )

    client.upload_media.return_value = WordPressMedia(
        media_id=123,
        source_url=(
            "https://example.com/uploads/photo.jpg"
            '?size=large&name="test"'
        ),
    )

    publisher.publish(post)

    content = client.create_post.call_args.kwargs["content"]

    assert (
        'src="https://example.com/uploads/photo.jpg'
        '?size=large&amp;name=&quot;test&quot;"'
    ) in content

    assert (
        'src="https://example.com/uploads/photo.jpg'
        '?size=large&name="test""'
    ) not in content

def test_does_not_create_post_when_media_upload_fails():
    publisher, credentials, client = make_publisher()

    image = Mock()
    image.path = Path("/tmp/photo.jpg")

    post = PreparedPost(
        source=Post(
            text="Hello WordPress",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=(image,),
    )

    client.upload_media.side_effect = RuntimeError(
        "WordPress media upload failed."
    )

    with pytest.raises(
        RuntimeError,
        match="WordPress media upload failed",
    ):
        publisher.publish(post)

    client.upload_media.assert_called_once()
    client.create_post.assert_not_called()

def test_does_not_create_post_when_second_image_upload_fails():
    publisher, credentials, client = make_publisher()

    first_image = Mock()
    first_image.path = Path("/tmp/first.jpg")

    second_image = Mock()
    second_image.path = Path("/tmp/second.jpg")

    post = PreparedPost(
        source=Post(
            text="Two WordPress images",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=(first_image, second_image),
    )

    client.upload_media.side_effect = [
        WordPressMedia(
            media_id=123,
            source_url="https://example.com/uploads/first.jpg",
        ),
        RuntimeError("Second image upload failed."),
    ]

    with pytest.raises(
        RuntimeError,
        match="Second image upload failed",
    ):
        publisher.publish(post)

    assert client.upload_media.call_count == 2

    assert [
        call.kwargs["image_path"]
        for call in client.upload_media.call_args_list
    ] == [
        first_image.path,
        second_image.path,
    ]

    client.create_post.assert_not_called()

def test_cleans_up_uploaded_media_when_second_upload_fails():
    publisher, credentials, client = make_publisher()

    first_image = Mock()
    first_image.path = Path("/tmp/first.jpg")

    second_image = Mock()
    second_image.path = Path("/tmp/second.jpg")

    post = PreparedPost(
        source=Post(
            text="WordPress media cleanup",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=(first_image, second_image),
    )

    client.upload_media.side_effect = [
        WordPressMedia(
            media_id=123,
            source_url="https://example.com/uploads/first.jpg",
        ),
        RuntimeError("Second image upload failed."),
    ]

    with pytest.raises(
        RuntimeError,
        match="Second image upload failed",
    ):
        publisher.publish(post)

    client.delete_media.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
        media_id=123,
    )

    client.create_post.assert_not_called()

def test_preserves_upload_error_when_media_cleanup_fails():
    publisher, credentials, client = make_publisher()

    first_image = Mock()
    first_image.path = Path("/tmp/first.jpg")

    second_image = Mock()
    second_image.path = Path("/tmp/second.jpg")

    post = PreparedPost(
        source=Post(
            text="WordPress cleanup failure",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=(first_image, second_image),
    )

    client.upload_media.side_effect = [
        WordPressMedia(
            media_id=123,
            source_url="https://example.com/uploads/first.jpg",
        ),
        RuntimeError("Second image upload failed."),
    ]

    client.delete_media.side_effect = OSError(
        "WordPress media deletion failed."
    )

    with pytest.raises(
        RuntimeError,
        match="Second image upload failed",
    ):
        publisher.publish(post)

    client.delete_media.assert_called_once()
    assert client.delete_media.call_args.kwargs["media_id"] == 123

    client.create_post.assert_not_called()

def test_cleans_up_multiple_uploaded_images_in_reverse_order():
    publisher, credentials, client = make_publisher()

    images = []
    for filename in ("first.jpg", "second.jpg", "third.jpg"):
        image = Mock()
        image.path = Path("/tmp") / filename
        images.append(image)

    post = PreparedPost(
        source=Post(
            text="WordPress multiple image cleanup",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=tuple(images),
    )

    client.upload_media.side_effect = [
        WordPressMedia(
            media_id=101,
            source_url="https://example.com/uploads/first.jpg",
        ),
        WordPressMedia(
            media_id=102,
            source_url="https://example.com/uploads/second.jpg",
        ),
        RuntimeError("Third image upload failed."),
    ]

    with pytest.raises(
        RuntimeError,
        match="Third image upload failed",
    ):
        publisher.publish(post)

    assert client.upload_media.call_count == 3

    assert [
        call.kwargs["media_id"]
        for call in client.delete_media.call_args_list
    ] == [102, 101]

    assert client.delete_media.call_count == 2

    client.create_post.assert_not_called()

def test_continues_media_cleanup_when_one_deletion_fails():
    publisher, credentials, client = make_publisher()

    images = []
    for filename in ("first.jpg", "second.jpg", "third.jpg"):
        image = Mock()
        image.path = Path("/tmp") / filename
        images.append(image)

    post = PreparedPost(
        source=Post(
            text="WordPress cleanup resilience",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=tuple(images),
    )

    client.upload_media.side_effect = [
        WordPressMedia(
            media_id=101,
            source_url="https://example.com/uploads/first.jpg",
        ),
        WordPressMedia(
            media_id=102,
            source_url="https://example.com/uploads/second.jpg",
        ),
        RuntimeError("Third image upload failed."),
    ]

    client.delete_media.side_effect = [
        OSError("Failed to delete media 102."),
        None,
    ]

    with pytest.raises(
        RuntimeError,
        match="Third image upload failed",
    ):
        publisher.publish(post)

    assert [
        call.kwargs["media_id"]
        for call in client.delete_media.call_args_list
    ] == [102, 101]

    assert client.delete_media.call_count == 2

    client.create_post.assert_not_called()

def test_does_not_delete_media_after_successful_publishing():
    publisher, credentials, client = make_publisher()

    images = []
    for filename in ("first.jpg", "second.jpg"):
        image = Mock()
        image.path = Path("/tmp") / filename
        images.append(image)

    post = PreparedPost(
        source=Post(
            text="WordPress successful publishing",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=tuple(images),
    )

    client.upload_media.side_effect = [
        WordPressMedia(
            media_id=101,
            source_url="https://example.com/uploads/first.jpg",
        ),
        WordPressMedia(
            media_id=102,
            source_url="https://example.com/uploads/second.jpg",
        ),
    ]

    client.create_post.return_value = 201

    publisher.publish(post)

    assert client.upload_media.call_count == 2

    client.create_post.assert_called_once()

    content = client.create_post.call_args.kwargs["content"]

    assert 'class="wp-image-101"' in content
    assert 'class="wp-image-102"' in content

    client.delete_media.assert_not_called()

def test_does_not_delete_media_when_post_creation_raises():
    publisher, credentials, client = make_publisher()

    image = Mock()
    image.path = Path("/tmp/photo.jpg")

    post = PreparedPost(
        source=Post(
            text="WordPress post creation failure",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=(image,),
    )

    client.upload_media.return_value = WordPressMedia(
        media_id=123,
        source_url="https://example.com/uploads/photo.jpg",
    )

    client.create_post.side_effect = OSError(
        "Connection lost while creating WordPress post."
    )

    with pytest.raises(
        OSError,
        match="Connection lost while creating WordPress post",
    ):
        publisher.publish(post)

    client.upload_media.assert_called_once()
    client.create_post.assert_called_once()
    client.delete_media.assert_not_called()

@pytest.mark.parametrize(
    "status_code",
    [400, 401, 403, 500],
)
def test_does_not_delete_media_when_post_creation_returns_error(
    status_code,
):
    publisher, credentials, client = make_publisher()

    image = Mock()
    image.path = Path("/tmp/photo.jpg")

    post = PreparedPost(
        source=Post(
            text="WordPress unsuccessful publishing",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=(image,),
    )

    client.upload_media.return_value = WordPressMedia(
        media_id=123,
        source_url="https://example.com/uploads/photo.jpg",
    )

    client.create_post.return_value = status_code

    with pytest.raises(
        RuntimeError,
        match=f"WordPress publishing failed \\(HTTP {status_code}\\)",
    ):
        publisher.publish(post)

    client.upload_media.assert_called_once()
    client.create_post.assert_called_once()
    client.delete_media.assert_not_called()

def test_publishes_text_only_post_without_media_operations():
    publisher, credentials, client = make_publisher()

    post = PreparedPost(
        source=Post(
            text="WordPress text-only post",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=(),
    )

    client.create_post.return_value = 201

    publisher.publish(post)

    client.upload_media.assert_not_called()
    client.delete_media.assert_not_called()

    client.create_post.assert_called_once()

    assert (
        client.create_post.call_args.kwargs["content"]
        == "WordPress text-only post"
    )

def test_does_not_upload_images_when_post_text_is_empty():
    publisher, credentials, client = make_publisher()

    image = Mock()
    image.path = Path("/tmp/photo.jpg")

    post = PreparedPost(
        source=Post(
            text="   ",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=(image,),
    )

    with pytest.raises(
        ValueError,
        match="WordPress post text is required",
    ):
        publisher.publish(post)

    client.upload_media.assert_not_called()
    client.create_post.assert_not_called()
    client.delete_media.assert_not_called()

def test_does_not_upload_images_without_tag_client():
    publisher, credentials, client = make_publisher()

    image = Mock()
    image.path = Path("/tmp/photo.jpg")

    post = PreparedPost(
        source=Post(
            text="WordPress post with unsupported tags",
            language=Language.ENGLISH,
            title="WordPress Test Title",
            tags=(Tag(name="technology"),),
        ),
        images=(image,),
    )

    with pytest.raises(
            ValueError,
            match="WordPress tag client is required when publishing tags",
    ):
        publisher.publish(post)

    client.upload_media.assert_not_called()
    client.create_post.assert_not_called()
    client.delete_media.assert_not_called()

def test_does_not_upload_images_when_application_password_is_missing():
    publisher, credentials, client = make_publisher(password=None)

    image = Mock()
    image.path = Path("/tmp/photo.jpg")

    post = PreparedPost(
        source=Post(
            text="WordPress post with missing credentials",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=(image,),
    )

    with pytest.raises(
        ValueError,
        match="WordPress application password is missing",
    ):
        publisher.publish(post)

    credentials.get.assert_called_once()

    client.upload_media.assert_not_called()
    client.create_post.assert_not_called()
    client.delete_media.assert_not_called()

@pytest.mark.parametrize(
    "site_url",
    [
        "http://example.com",
        "https://",
        "https://admin:password@example.com",
        "https://example.com?token=secret",
        "https://example.com#fragment",
    ],
)
def test_does_not_upload_images_when_wordpress_url_is_invalid(site_url):
    publisher, credentials, client = make_publisher(
        account=make_account(site_url=site_url)
    )

    image = Mock()
    image.path = Path("/tmp/photo.jpg")

    post = PreparedPost(
        source=Post(
            text="WordPress invalid URL test",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=(image,),
    )

    with pytest.raises(
        ValueError,
        match="A valid HTTPS WordPress site URL is required",
    ):
        publisher.publish(post)

    credentials.get.assert_not_called()
    client.upload_media.assert_not_called()
    client.create_post.assert_not_called()
    client.delete_media.assert_not_called()

def test_logs_media_cleanup_failure_and_preserves_upload_error(caplog):
    publisher, credentials, client = make_publisher()

    first_image = Mock()
    first_image.path = Path("/tmp/first.jpg")

    second_image = Mock()
    second_image.path = Path("/tmp/second.jpg")

    post = PreparedPost(
        source=Post(
            text="WordPress cleanup logging",
            language=Language.ENGLISH,
            title="WordPress Test Title",
        ),
        images=(first_image, second_image),
    )

    client.upload_media.side_effect = [
        WordPressMedia(
            media_id=123,
            source_url="https://example.com/uploads/first.jpg",
        ),
        RuntimeError("Second image upload failed."),
    ]

    client.delete_media.side_effect = OSError(
        "WordPress media deletion failed."
    )

    with pytest.raises(
        RuntimeError,
        match="Second image upload failed",
    ):
        publisher.publish(post)

    assert "Failed to delete WordPress media 123" in caplog.text
    assert "test-wordpress-account" in caplog.text
    assert "WordPress media deletion failed" in caplog.text

    client.delete_media.assert_called_once()
    client.create_post.assert_not_called()

def test_publisher_resolves_and_sends_wordpress_tags():
    publisher, credentials, client = make_publisher()

    tag_client = Mock()
    tag_client.list_tags.return_value = (
        WordPressTag(id=12, name="Python"),
        WordPressTag(id=34, name="SocialFlow"),
    )

    publisher._tag_client = tag_client

    post = PreparedPost(
        source=Post(
            text="Hello WordPress",
            language=Language.ENGLISH,
            title="WordPress Test Title",
            tags=(
                Tag(name="SocialFlow"),
                Tag(name="Python"),
            ),
        ),
        images=(),
    )

    publisher.publish(post)

    tag_client.list_tags.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
    )

    client.create_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
        content="Hello WordPress",
        tags=(34, 12),
        title="WordPress Test Title",
        categories=(),
    )

def test_publisher_rejects_missing_wordpress_tag():
    publisher, credentials, client = make_publisher()

    tag_client = Mock()
    tag_client.list_tags.return_value = (
        WordPressTag(id=12, name="Python"),
    )

    publisher._tag_client = tag_client

    post = PreparedPost(
        source=Post(
            text="Hello WordPress",
            language=Language.ENGLISH,
            title="WordPress Test Title",
            tags=(Tag(name="Missing"),),
        ),
        images=(),
    )

    with pytest.raises(
        ValueError,
        match="WordPress tag not found: Missing",
    ):
        publisher.publish(post)

    tag_client.list_tags.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
    )

    client.upload_media.assert_not_called()
    client.create_post.assert_not_called()

def test_publisher_stops_when_wordpress_tag_lookup_fails():
    publisher, credentials, client = make_publisher()

    tag_client = Mock()
    tag_client.list_tags.side_effect = RuntimeError(
        "WordPress tag lookup failed."
    )

    publisher._tag_client = tag_client

    post = PreparedPost(
        source=Post(
            text="Hello WordPress",
            language=Language.ENGLISH,
            title="WordPress Test Title",
            tags=(Tag(name="Python"),),
        ),
        images=(),
    )

    with pytest.raises(
        RuntimeError,
        match="WordPress tag lookup failed",
    ):
        publisher.publish(post)

    tag_client.list_tags.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
    )

    client.upload_media.assert_not_called()
    client.create_post.assert_not_called()

def test_publisher_rejects_ambiguous_wordpress_tags():
    publisher, credentials, client = make_publisher()

    tag_client = Mock()
    tag_client.list_tags.return_value = (
        WordPressTag(id=12, name="Python"),
        WordPressTag(id=34, name="python"),
    )

    publisher._tag_client = tag_client

    post = PreparedPost(
        source=Post(
            text="Hello WordPress",
            language=Language.ENGLISH,
            title="WordPress Test Title",
            tags=(Tag(name="Python"),),
        ),
        images=(),
    )

    with pytest.raises(
        ValueError,
        match="Ambiguous WordPress tag: Python",
    ):
        publisher.publish(post)

    tag_client.list_tags.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
    )

    client.upload_media.assert_not_called()
    client.create_post.assert_not_called()

def test_publisher_sends_tags_with_uploaded_images():
    publisher, credentials, client = make_publisher()

    tag_client = Mock()
    tag_client.list_tags.return_value = (
        WordPressTag(id=12, name="Python"),
    )
    publisher._tag_client = tag_client

    image = Mock()
    image.path = Path("/tmp/photo.jpg")

    media = Mock()
    media.media_id = 55
    media.source_url = "https://example.com/photo.jpg"
    client.upload_media.return_value = media

    post = PreparedPost(
        source=Post(
            text="Hello WordPress",
            language=Language.ENGLISH,
            title="WordPress Test Title",
            tags=(Tag(name="Python"),),
        ),
        images=(image,),
    )

    publisher.publish(post)

    client.upload_media.assert_called_once()

    client.create_post.assert_called_once()

    kwargs = client.create_post.call_args.kwargs

    assert kwargs["tags"] == (12,)
    assert kwargs["content"].startswith("Hello WordPress")
    assert 'wp-image-55' in kwargs["content"]
    assert "https://example.com/photo.jpg" in kwargs["content"]



def test_publisher_passes_selected_categories_to_client():
    publisher, _, client = make_publisher()

    post = PreparedPost(
        source=Post(
            text="Hello WordPress",
            language=Language.ENGLISH,
            title="Category Test",
            category_ids=(10, 20),
        )
    )

    publisher.publish(post)

    assert client.create_post.call_args.kwargs["categories"] == (10, 20)


def test_publisher_passes_empty_categories_by_default():
    publisher, _, client = make_publisher()

    publisher.publish(make_post())

    assert client.create_post.call_args.kwargs["categories"] == ()
