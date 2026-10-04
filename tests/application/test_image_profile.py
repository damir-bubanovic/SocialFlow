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

def test_image_profile_can_contain_aspect_ratio_limits() -> None:
    profile = ImageProfile(
        maximum_dimensions=ImageDimensions(
            width=1080,
            height=1350,
        ),
        output_format="JPEG",
        minimum_aspect_ratio=0.8,
        maximum_aspect_ratio=1.91,
    )

    assert profile.minimum_aspect_ratio == 0.8
    assert profile.maximum_aspect_ratio == 1.91


def test_image_profile_rejects_non_positive_minimum_aspect_ratio() -> None:
    with pytest.raises(
        ValueError,
        match="Minimum aspect ratio must be greater than zero",
    ):
        ImageProfile(
            maximum_dimensions=ImageDimensions(
                width=1080,
                height=1350,
            ),
            output_format="JPEG",
            minimum_aspect_ratio=0,
        )


def test_image_profile_rejects_non_positive_maximum_aspect_ratio() -> None:
    with pytest.raises(
        ValueError,
        match="Maximum aspect ratio must be greater than zero",
    ):
        ImageProfile(
            maximum_dimensions=ImageDimensions(
                width=1080,
                height=1350,
            ),
            output_format="JPEG",
            maximum_aspect_ratio=0,
        )


def test_image_profile_rejects_reversed_aspect_ratio_limits() -> None:
    with pytest.raises(
        ValueError,
        match="Minimum aspect ratio cannot exceed maximum aspect ratio",
    ):
        ImageProfile(
            maximum_dimensions=ImageDimensions(
                width=1080,
                height=1350,
            ),
            output_format="JPEG",
            minimum_aspect_ratio=1.91,
            maximum_aspect_ratio=0.8,
        )