from pathlib import Path

from PIL import Image

from socialflow.domain.publishing.destination import PublishingDestination
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
            PublishingDestination.INSTAGRAM: profile,
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
        destination=PublishingDestination.INSTAGRAM,
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
            PublishingDestination.INSTAGRAM: profile,
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
        destination=PublishingDestination.INSTAGRAM,
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
            destination=PublishingDestination.WORDPRESS,
            output_path=output_path,
        )
    except ValueError as error:
        assert str(error) == "No image profile configured for: wordpress"
    else:
        raise AssertionError("Expected ValueError")

def test_image_preparation_service_prepares_multiple_images(
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "first.png"
    second_path = tmp_path / "second.png"
    output_directory = tmp_path / "prepared"

    create_test_image(
        first_path,
        (1600, 900),
    )
    create_test_image(
        second_path,
        (1200, 1200),
    )

    profile = ImageProfile(
        maximum_dimensions=ImageDimensions(
            width=800,
            height=800,
        ),
        output_format="JPEG",
    )

    service = ImagePreparationService(
        profile_provider=ImageProfileProvider(
            profiles={
                PublishingDestination.INSTAGRAM: profile,
            }
        ),
    )

    result = service.prepare_all(
        attachments=(
            ImageAttachment(path=first_path),
            ImageAttachment(path=second_path),
        ),
        destination=PublishingDestination.INSTAGRAM,
        output_directory=output_directory,
    )

    assert len(result) == 2

    assert result[0].source.path == first_path
    assert result[0].destination == PublishingDestination.INSTAGRAM
    assert result[0].path == (
            output_directory / "first-instagram-1.jpg"
    )

    assert result[1].source.path == second_path
    assert result[1].destination == PublishingDestination.INSTAGRAM
    assert result[1].path == (
            output_directory / "second-instagram-2.jpg"
    )

    assert all(
        prepared.path.is_file()
        for prepared in result
    )

def test_prepare_all_applies_profile_to_each_image(
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "first.png"
    second_path = tmp_path / "second.png"
    output_directory = tmp_path / "prepared"

    create_test_image(
        first_path,
        (1600, 800),
    )
    create_test_image(
        second_path,
        (800, 1600),
    )

    profile = ImageProfile(
        maximum_dimensions=ImageDimensions(
            width=800,
            height=800,
        ),
        output_format="JPEG",
    )

    service = ImagePreparationService(
        profile_provider=ImageProfileProvider(
            profiles={
                PublishingDestination.INSTAGRAM: profile,
            }
        ),
    )

    result = service.prepare_all(
        attachments=(
            ImageAttachment(path=first_path),
            ImageAttachment(path=second_path),
        ),
        destination=PublishingDestination.INSTAGRAM,
        output_directory=output_directory,
    )

    with Image.open(result[0].path) as first:
        assert first.size == (800, 400)
        assert first.format == "JPEG"

    with Image.open(result[1].path) as second:
        assert second.size == (400, 800)
        assert second.format == "JPEG"

def test_prepare_all_accepts_no_images(
    tmp_path: Path,
) -> None:
    output_directory = tmp_path / "prepared"

    profile = ImageProfile(
        maximum_dimensions=ImageDimensions(
            width=800,
            height=800,
        ),
        output_format="JPEG",
    )

    service = ImagePreparationService(
        profile_provider=ImageProfileProvider(
            profiles={
                PublishingDestination.INSTAGRAM: profile,
            }
        ),
    )

    result = service.prepare_all(
        attachments=(),
        destination=PublishingDestination.INSTAGRAM,
        output_directory=output_directory,
    )

    assert result == ()