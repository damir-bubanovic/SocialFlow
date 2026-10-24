import pytest

from socialflow.domain.post.remote_media import RemoteMedia
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)


def test_remote_media_accepts_valid_image():
    media = RemoteMedia(
        remote_id=123,
        destination=PublishingDestination.WORDPRESS,
        source_url="https://example.com/uploads/photo.jpg",
        title="Example photo",
        thumbnail_url="https://example.com/uploads/photo-150x150.jpg",
    )

    assert media.remote_id == 123
    assert media.title == "Example photo"
    assert media.thumbnail_url is not None


def test_remote_media_allows_missing_thumbnail():
    media = RemoteMedia(
        remote_id=123,
        destination=PublishingDestination.WORDPRESS,
        source_url="https://example.com/photo.jpg",
        title="Photo",
    )

    assert media.thumbnail_url is None


@pytest.mark.parametrize(
    "remote_id",
    [0, -1, True, False, "123", 1.5],
)
def test_remote_media_rejects_invalid_id(remote_id):
    with pytest.raises(ValueError, match="positive integer"):
        RemoteMedia(
            remote_id=remote_id,
            destination=PublishingDestination.WORDPRESS,
            source_url="https://example.com/photo.jpg",
            title="Photo",
        )


@pytest.mark.parametrize(
    "source_url",
    [
        "",
        "http://example.com/photo.jpg",
        "not-a-url",
        "https://user:password@example.com/photo.jpg",
    ],
)
def test_remote_media_rejects_invalid_source_url(source_url):
    with pytest.raises(ValueError, match="HTTPS URL"):
        RemoteMedia(
            remote_id=123,
            destination=PublishingDestination.WORDPRESS,
            source_url=source_url,
            title="Photo",
        )


def test_remote_media_rejects_invalid_thumbnail_url():
    with pytest.raises(ValueError, match="HTTPS URL"):
        RemoteMedia(
            remote_id=123,
            destination=PublishingDestination.WORDPRESS,
            source_url="https://example.com/photo.jpg",
            title="Photo",
            thumbnail_url="http://example.com/thumbnail.jpg",
        )