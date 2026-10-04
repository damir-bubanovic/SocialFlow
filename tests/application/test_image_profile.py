import pytest

from socialflow.application.images.image_processor import ImageDimensions
from socialflow.application.images.image_profile import ImageProfile


def test_image_profile_contains_processing_requirements() -> None:
    dimensions = ImageDimensions(
        width=1080,
        height=1350,
    )

    profile = ImageProfile(
        maximum_dimensions=dimensions,
        output_format="JPEG",
    )

    assert profile.maximum_dimensions == dimensions
    assert profile.output_format == "JPEG"


def test_image_profile_rejects_unsupported_output_format() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported output image format",
    ):
        ImageProfile(
            maximum_dimensions=ImageDimensions(
                width=1080,
                height=1080,
            ),
            output_format="BMP",
        )