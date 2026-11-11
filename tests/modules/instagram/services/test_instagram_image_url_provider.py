
from pathlib import Path
from unittest.mock import Mock

import pytest

from socialflow.modules.instagram.services.instagram_image_url_provider import (
    InstagramImageUrlProvider,
)


def test_image_url_provider_is_abstract() -> None:
    with pytest.raises(TypeError):
        InstagramImageUrlProvider()


def test_image_url_provider_can_be_implemented() -> None:
    class FakeImageUrlProvider(InstagramImageUrlProvider):
        def get_public_url(self, image_path: Path) -> str:
            return "https://example.com/photo.jpg"

    provider = FakeImageUrlProvider()

    result = provider.get_public_url(
        Path("/tmp/photo.jpg")
    )

    assert result == "https://example.com/photo.jpg"


def test_image_url_provider_requires_get_public_url() -> None:
    incomplete_provider_type = type(
        "IncompleteImageUrlProvider",
        (InstagramImageUrlProvider,),
        {},
    )

    with pytest.raises(TypeError):
        incomplete_provider_type()


def test_image_url_provider_accepts_path_objects() -> None:
    class FakeImageUrlProvider(InstagramImageUrlProvider):
        def __init__(self) -> None:
            self.resolve = Mock(
                return_value="https://example.com/photo.jpg"
            )

        def get_public_url(self, image_path: Path) -> str:
            return self.resolve(image_path)

    provider = FakeImageUrlProvider()
    local_image_path = Path("/tmp/photo.jpg")

    result = provider.get_public_url(local_image_path)

    provider.resolve.assert_called_once_with(local_image_path)
    assert result == "https://example.com/photo.jpg"
