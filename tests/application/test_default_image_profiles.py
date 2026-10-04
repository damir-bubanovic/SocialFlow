from socialflow.application.images.default_image_profiles import (
    DEFAULT_IMAGE_PROFILES,
)
from socialflow.application.images.image_destination import ImageDestination
from socialflow.application.images.image_processor import ImageDimensions


def test_default_profiles_include_instagram() -> None:
    profile = DEFAULT_IMAGE_PROFILES[
        ImageDestination.INSTAGRAM
    ]

    assert profile.maximum_dimensions == ImageDimensions(
        width=1080,
        height=1350,
    )
    assert profile.output_format == "JPEG"


def test_default_profiles_do_not_assume_wordpress_dimensions() -> None:
    assert ImageDestination.WORDPRESS not in DEFAULT_IMAGE_PROFILES