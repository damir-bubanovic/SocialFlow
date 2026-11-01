import pytest

from socialflow.modules.wordpress.models.wordpress_media import (
    WordPressMedia,
)


def test_wordpress_media_stores_upload_result():
    media = WordPressMedia(
        media_id=123,
        source_url="https://example.com/wp-content/uploads/photo.jpg",
    )

    assert media.media_id == 123
    assert media.source_url == (
        "https://example.com/wp-content/uploads/photo.jpg"
    )


def test_wordpress_media_is_immutable():
    media = WordPressMedia(
        media_id=123,
        source_url="https://example.com/photo.jpg",
    )

    with pytest.raises(AttributeError):
        setattr(media, "media_id", 456)