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

def test_aspect_ratio_for_square_image() -> None:
    dimensions = ImageDimensions(
        width=1000,
        height=1000,
    )

    result = ImageProcessor.aspect_ratio(dimensions)

    assert result == 1.0


def test_aspect_ratio_for_portrait_image() -> None:
    dimensions = ImageDimensions(
        width=800,
        height=1000,
    )

    result = ImageProcessor.aspect_ratio(dimensions)

    assert result == 0.8


def test_aspect_ratio_for_landscape_image() -> None:
    dimensions = ImageDimensions(
        width=1910,
        height=1000,
    )

    result = ImageProcessor.aspect_ratio(dimensions)

    assert result == 1.91

def test_aspect_ratio_is_allowed_inside_limits() -> None:
    dimensions = ImageDimensions(
        width=1080,
        height=1080,
    )

    assert ImageProcessor.aspect_ratio_is_allowed(
        dimensions,
        minimum=0.8,
        maximum=1.91,
    )


def test_aspect_ratio_is_not_allowed_below_minimum() -> None:
    dimensions = ImageDimensions(
        width=600,
        height=1000,
    )

    assert not ImageProcessor.aspect_ratio_is_allowed(
        dimensions,
        minimum=0.8,
        maximum=1.91,
    )


def test_aspect_ratio_is_not_allowed_above_maximum() -> None:
    dimensions = ImageDimensions(
        width=2000,
        height=1000,
    )

    assert not ImageProcessor.aspect_ratio_is_allowed(
        dimensions,
        minimum=0.8,
        maximum=1.91,
    )


def test_aspect_ratio_is_allowed_without_limits() -> None:
    dimensions = ImageDimensions(
        width=3000,
        height=500,
    )

    assert ImageProcessor.aspect_ratio_is_allowed(
        dimensions,
        minimum=None,
        maximum=None,
    )

def test_aspect_ratio_dimensions_expand_narrow_image() -> None:
    source = ImageDimensions(
        width=600,
        height=1000,
    )

    result = ImageProcessor.calculate_aspect_ratio_dimensions(
        source,
        minimum=0.8,
        maximum=1.91,
    )

    assert result == ImageDimensions(
        width=800,
        height=1000,
    )


def test_aspect_ratio_dimensions_expand_short_image() -> None:
    source = ImageDimensions(
        width=2000,
        height=1000,
    )

    result = ImageProcessor.calculate_aspect_ratio_dimensions(
        source,
        minimum=0.8,
        maximum=1.5,
    )

    assert result == ImageDimensions(
        width=2000,
        height=1333,
    )


def test_aspect_ratio_dimensions_keep_allowed_image() -> None:
    source = ImageDimensions(
        width=1080,
        height=1080,
    )

    result = ImageProcessor.calculate_aspect_ratio_dimensions(
        source,
        minimum=0.8,
        maximum=1.91,
    )

    assert result == source


def test_aspect_ratio_dimensions_work_without_limits() -> None:
    source = ImageDimensions(
        width=2400,
        height=800,
    )

    result = ImageProcessor.calculate_aspect_ratio_dimensions(
        source,
        minimum=None,
        maximum=None,
    )

    assert result == source

def test_pad_to_dimensions_expands_image_canvas() -> None:
    image = Image.new(
        "RGB",
        (600, 1000),
    )

    result = ImageProcessor.pad_to_dimensions(
        image,
        ImageDimensions(
            width=800,
            height=1000,
        ),
    )

    assert result.size == (800, 1000)
    assert image.size == (600, 1000)

def test_pad_to_dimensions_centers_original_image() -> None:
    image = Image.new(
        "RGB",
        (600, 1000),
        "black",
    )

    result = ImageProcessor.pad_to_dimensions(
        image,
        ImageDimensions(
            width=800,
            height=1000,
        ),
    )

    assert result.getpixel((0, 500)) == (255, 255, 255)
    assert result.getpixel((100, 500)) == (0, 0, 0)
    assert result.getpixel((799, 500)) == (255, 255, 255)

def test_pad_to_dimensions_copies_image_when_size_matches() -> None:
    image = Image.new(
        "RGB",
        (800, 1000),
    )

    result = ImageProcessor.pad_to_dimensions(
        image,
        ImageDimensions(
            width=800,
            height=1000,
        ),
    )

    assert result.size == image.size
    assert result is not image

def test_pad_to_dimensions_rejects_smaller_target() -> None:
    image = Image.new(
        "RGB",
        (1000, 1000),
    )

    with pytest.raises(
        ValueError,
        match="Target dimensions cannot be smaller",
    ):
        ImageProcessor.pad_to_dimensions(
            image,
            ImageDimensions(
                width=800,
                height=1000,
            ),
        )

def test_process_creates_separate_output_file(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.png"
    output_path = tmp_path / "processed.jpg"

    create_test_image(
        source_path,
        (1600, 900),
    )

    attachment = ImageAttachment(
        path=source_path,
    )

    result = ImageProcessor.process(
        attachment=attachment,
        maximum=ImageDimensions(
            width=1000,
            height=1000,
        ),
        output_path=output_path,
        output_format="JPEG",
    )

    assert result == output_path
    assert output_path.is_file()
    assert source_path.is_file()

def test_process_resizes_image_to_maximum_dimensions(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.png"
    output_path = tmp_path / "processed.jpg"

    create_test_image(
        source_path,
        (2000, 1000),
    )

    attachment = ImageAttachment(
        path=source_path,
    )

    ImageProcessor.process(
        attachment=attachment,
        maximum=ImageDimensions(
            width=1000,
            height=1000,
        ),
        output_path=output_path,
        output_format="JPEG",
    )

    with Image.open(output_path) as result:
        assert result.size == (1000, 500)

def test_process_applies_aspect_ratio_padding_before_resize(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.png"
    output_path = tmp_path / "processed.jpg"

    create_test_image(
        source_path,
        (600, 1000),
    )

    attachment = ImageAttachment(
        path=source_path,
    )

    ImageProcessor.process(
        attachment=attachment,
        maximum=ImageDimensions(
            width=400,
            height=500,
        ),
        output_path=output_path,
        output_format="JPEG",
        minimum_aspect_ratio=0.8,
        maximum_aspect_ratio=1.91,
    )

    with Image.open(output_path) as result:
        assert result.size == (400, 500)

def test_process_does_not_modify_source_image(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.png"
    output_path = tmp_path / "processed.jpg"

    create_test_image(
        source_path,
        (2000, 1000),
    )

    attachment = ImageAttachment(
        path=source_path,
    )

    ImageProcessor.process(
        attachment=attachment,
        maximum=ImageDimensions(
            width=1000,
            height=1000,
        ),
        output_path=output_path,
        output_format="JPEG",
    )

    with Image.open(source_path) as source:
        assert source.size == (2000, 1000)

    with Image.open(output_path) as result:
        assert result.size == (1000, 500)