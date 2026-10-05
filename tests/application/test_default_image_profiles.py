from socialflow.application.images.default_image_profiles import (
    DEFAULT_IMAGE_PROFILES,
)
from socialflow.application.images.image_processor import ImageDimensions
from socialflow.domain.publishing.destination import PublishingDestination


def test_default_profiles_include_all_publishing_destinations() -> None:
    assert set(DEFAULT_IMAGE_PROFILES) == {
        PublishingDestination.FACEBOOK,
        PublishingDestination.INSTAGRAM,
        PublishingDestination.WORDPRESS,
    }


def test_facebook_default_image_profile() -> None:
    profile = DEFAULT_IMAGE_PROFILES[
        PublishingDestination.FACEBOOK
    ]

    assert profile.maximum_dimensions == ImageDimensions(
        width=2048,
        height=2048,
    )
    assert profile.output_format == "JPEG"
    assert profile.minimum_aspect_ratio is None
    assert profile.maximum_aspect_ratio is None


def test_instagram_default_image_profile() -> None:
    profile = DEFAULT_IMAGE_PROFILES[
        PublishingDestination.INSTAGRAM
    ]

    assert profile.maximum_dimensions == ImageDimensions(
        width=1080,
        height=1350,
    )
    assert profile.output_format == "JPEG"
    assert profile.minimum_aspect_ratio == 0.8
    assert profile.maximum_aspect_ratio == 1.91


def test_wordpress_default_image_profile() -> None:
    profile = DEFAULT_IMAGE_PROFILES[
        PublishingDestination.WORDPRESS
    ]

    assert profile.maximum_dimensions == ImageDimensions(
        width=2048,
        height=2048,
    )
    assert profile.output_format == "JPEG"
    assert profile.minimum_aspect_ratio is None
    assert profile.maximum_aspect_ratio is None