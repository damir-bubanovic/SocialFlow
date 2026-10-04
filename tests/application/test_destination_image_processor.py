from pathlib import Path

from PIL import Image

from socialflow.application.images.destination_image_processor import (
    DestinationImageProcessor,
)
from socialflow.application.images.image_processor import ImageDimensions
from socialflow.application.images.image_profile import ImageProfile
from socialflow.domain.post.image_attachment import ImageAttachment


def create_test_image(
    path: Path,
    size: tuple[int, int],
) -> None:
    image = Image.new("RGB", size)
    image.save(path)


def test_destination_processor_applies_profile(
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

    profile = ImageProfile(
        maximum_dimensions=ImageDimensions(
            width=400,
            height=500,
        ),
        output_format="JPEG",
        minimum_aspect_ratio=0.8,
        maximum_aspect_ratio=1.91,
    )

    result = DestinationImageProcessor.process(
        attachment=attachment,
        profile=profile,
        output_path=output_path,
    )

    assert result == output_path
    assert output_path.is_file()

    with Image.open(output_path) as processed:
        assert processed.size == (400, 500)
        assert processed.format == "JPEG"


def test_destination_processor_preserves_source(
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

    profile = ImageProfile(
        maximum_dimensions=ImageDimensions(
            width=800,
            height=800,
        ),
        output_format="JPEG",
    )

    DestinationImageProcessor.process(
        attachment=attachment,
        profile=profile,
        output_path=output_path,
    )

    with Image.open(source_path) as source:
        assert source.size == (1600, 900)
        assert source.format == "PNG"

    with Image.open(output_path) as processed:
        assert processed.size == (800, 450)
        assert processed.format == "JPEG"