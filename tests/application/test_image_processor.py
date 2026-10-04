from pathlib import Path
import pytest
from PIL import Image

from socialflow.application.images.image_processor import (
    ImageDimensions,
    ImageProcessor,
)
from socialflow.domain.post.image_attachment import ImageAttachment


def create_test_image(
    path: Path,
    size: tuple[int, int],
) -> None:
    image = Image.new("RGB", size)
    image.save(path)


def test_image_processor_reads_image_dimensions(
    tmp_path: Path,
) -> None:
    path = tmp_path / "image.png"
    create_test_image(path, (1600, 900))

    attachment = ImageAttachment(path=path)

    dimensions = ImageProcessor.dimensions(attachment)

    assert dimensions == ImageDimensions(
        width=1600,
        height=900,
    )


def test_fit_dimensions_scales_landscape_image() -> None:
    source = ImageDimensions(
        width=2000,
        height=1000,
    )
    maximum = ImageDimensions(
        width=1000,
        height=1000,
    )

    result = ImageProcessor.calculate_fit_dimensions(
        source,
        maximum,
    )

    assert result == ImageDimensions(
        width=1000,
        height=500,
    )


def test_fit_dimensions_scales_portrait_image() -> None:
    source = ImageDimensions(
        width=1000,
        height=2000,
    )
    maximum = ImageDimensions(
        width=1000,
        height=1000,
    )

    result = ImageProcessor.calculate_fit_dimensions(
        source,
        maximum,
    )

    assert result == ImageDimensions(
        width=500,
        height=1000,
    )


def test_fit_dimensions_does_not_enlarge_small_image() -> None:
    source = ImageDimensions(
        width=600,
        height=400,
    )
    maximum = ImageDimensions(
        width=1000,
        height=1000,
    )

    result = ImageProcessor.calculate_fit_dimensions(
        source,
        maximum,
    )

    assert result == source

def test_image_dimensions_reject_zero_width() -> None:
    with pytest.raises(
        ValueError,
        match="Image width must be greater than zero",
    ):
        ImageDimensions(
            width=0,
            height=1000,
        )

def test_image_dimensions_reject_zero_height() -> None:
    with pytest.raises(
        ValueError,
        match="Image height must be greater than zero",
    ):
        ImageDimensions(
            width=1000,
            height=0,
        )

def test_image_dimensions_reject_negative_values() -> None:
    with pytest.raises(ValueError):
        ImageDimensions(
            width=-100,
            height=500,
        )

    with pytest.raises(ValueError):
        ImageDimensions(
            width=500,
            height=-100,
        )