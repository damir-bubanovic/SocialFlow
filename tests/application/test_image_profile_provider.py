import pytest

from socialflow.application.images.default_image_profiles import (
    DEFAULT_IMAGE_PROFILES,
)
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.application.images.image_processor import ImageDimensions
from socialflow.application.images.image_profile import ImageProfile
from socialflow.application.images.image_profile_provider import (
    ImageProfileProvider,
)


def test_image_profile_provider_returns_configured_profile() -> None:
    profile = ImageProfile(
        maximum_dimensions=ImageDimensions(
            width=1080,
            height=1350,
        ),
        output_format="JPEG",
    )

    provider = ImageProfileProvider(
        profiles={
            PublishingDestination.INSTAGRAM: profile,
        }
    )

    result = provider.profile_for(
        PublishingDestination.INSTAGRAM,
    )

    assert result == profile


def test_image_profile_provider_rejects_unconfigured_destination() -> None:
    provider = ImageProfileProvider()

    with pytest.raises(
        ValueError,
        match="No image profile configured for: wordpress",
    ):
        provider.profile_for(
            PublishingDestination.WORDPRESS,
        )

def test_image_profile_provider_can_use_default_profiles() -> None:
    provider = ImageProfileProvider(
        profiles=DEFAULT_IMAGE_PROFILES,
    )

    profile = provider.profile_for(
        PublishingDestination.INSTAGRAM,
    )

    assert profile.maximum_dimensions == ImageDimensions(
        width=1080,
        height=1350,
    )
    assert profile.output_format == "JPEG"