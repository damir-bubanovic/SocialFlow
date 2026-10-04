from pathlib import Path

from PIL import Image

from socialflow.application.images.image_destination import ImageDestination
from socialflow.application.images.image_preparation_service import (
    ImagePreparationService,
)
from socialflow.application.images.image_processor import ImageDimensions
from socialflow.application.images.image_profile import ImageProfile
from socialflow.application.images.image_profile_provider import (
    ImageProfileProvider,
)
from socialflow.domain.post.image_attachment import ImageAttachment


def create_test_image(
    path: Path,
    size: tuple[int, int],
) -> None:
    image = Image.new("RGB", size)
    image.save(path)


def test_image_preparation_service_uses_destination_profile(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.png"
    output_path = tmp_path / "prepared.jpg"

    create_test_image(
        source_path,
        (600, 1000),
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

    provider = ImageProfileProvider(
        profiles={
            ImageDestination.INSTAGRAM: profile,
        }
    )

    service = ImagePreparationService(
        profile_provider=provider,
    )

    attachment = ImageAttachment(
        path=source_path,
    )

    result = service.prepare(
        attachment=attachment,
        destination=ImageDestination.INSTAGRAM,
        output_path=output_path,
    )

    assert result == output_path
    assert output_path.is_file()

    with Image.open(output_path) as prepared:
        assert prepared.size == (400, 500)
        assert prepared.format == "JPEG"


def test_image_preparation_service_preserves_original(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.png"
    output_path = tmp_path / "prepared.jpg"

    create_test_image(
        source_path,
        (1600, 900),
    )

    profile = ImageProfile(
        maximum_dimensions=ImageDimensions(
            width=800,
            height=800,
        ),
        output_format="JPEG",
    )

    provider = ImageProfileProvider(
        profiles={
            ImageDestination.INSTAGRAM: profile,
        }
    )

    service = ImagePreparationService(
        profile_provider=provider,
    )

    attachment = ImageAttachment(
        path=source_path,
    )

    service.prepare(
        attachment=attachment,
        destination=ImageDestination.INSTAGRAM,
        output_path=output_path,
    )

    with Image.open(source_path) as original:
        assert original.size == (1600, 900)
        assert original.format == "PNG"

def test_image_preparation_service_rejects_unconfigured_destination(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.png"
    output_path = tmp_path / "prepared.jpg"

    create_test_image(
        source_path,
        (1000, 1000),
    )

    service = ImagePreparationService(
        profile_provider=ImageProfileProvider(),
    )

    attachment = ImageAttachment(
        path=source_path,
    )

    try:
        service.prepare(
            attachment=attachment,
            destination=ImageDestination.WORDPRESS,
            output_path=output_path,
        )
    except ValueError as error:
        assert str(error) == "No image profile configured for: wordpress"
    else:
        raise AssertionError("Expected ValueError")