from PIL import Image

from pathlib import Path

import pytest

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
from socialflow.application.images.prepared_image import PreparedImage


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

def test_cleanup_removes_prepared_image_files(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.jpg"
    prepared_path = tmp_path / "prepared.jpg"

    source_path.touch()
    prepared_path.touch()

    attachment = ImageAttachment(path=source_path)

    prepared_image = PreparedImage(
        source=attachment,
        destination=PublishingDestination.INSTAGRAM,
        path=prepared_path,
    )

    service = ImagePreparationService(
        profile_provider=ImageProfileProvider(
            profiles={}
        )
    )

    service.cleanup((prepared_image,))

    assert not prepared_path.exists()
    assert source_path.exists()

def test_cleanup_ignores_missing_prepared_image_files(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.jpg"
    missing_path = tmp_path / "missing.jpg"

    source_path.touch()

    attachment = ImageAttachment(path=source_path)

    prepared_image = PreparedImage(
        source=attachment,
        destination=PublishingDestination.INSTAGRAM,
        path=missing_path,
    )

    service = ImagePreparationService(
        profile_provider=ImageProfileProvider(
            profiles={}
        )
    )

    service.cleanup((prepared_image,))

    assert source_path.exists()
    assert not missing_path.exists()


def test_prepare_all_cleans_partial_files_when_later_image_fails(
    tmp_path: Path,
) -> None:
    import pytest

    first_source = tmp_path / "first.png"
    second_source = tmp_path / "second.png"

    create_test_image(first_source, (800, 600))
    create_test_image(second_source, (800, 600))

    first_attachment = ImageAttachment(path=first_source)
    second_attachment = ImageAttachment(path=second_source)

    profile_provider = ImageProfileProvider(
        profiles={
            PublishingDestination.FACEBOOK: ImageProfile(
                maximum_dimensions=ImageDimensions(
                    width=800,
                    height=800,
                ),
                output_format="JPEG",
            ),
        }
    )

    class FailingSecondImageService(ImagePreparationService):
        def prepare(
            self,
            attachment: ImageAttachment,
            destination: PublishingDestination,
            output_path: Path,
        ) -> Path:
            if attachment is second_attachment:
                output_path.write_bytes(b"partial image data")
                raise RuntimeError("Second image preparation failed.")

            return super().prepare(
                attachment=attachment,
                destination=destination,
                output_path=output_path,
            )

    service = FailingSecondImageService(
        profile_provider=profile_provider,
    )

    output_directory = tmp_path / "prepared"

    first_output = output_directory / "first-facebook-1.jpg"
    second_output = output_directory / "second-facebook-2.jpg"

    with pytest.raises(
        RuntimeError,
        match="Second image preparation failed.",
    ):
        service.prepare_all(
            attachments=(first_attachment, second_attachment),
            destination=PublishingDestination.FACEBOOK,
            output_directory=output_directory,
        )

    assert not first_output.exists()
    assert not second_output.exists()

    assert first_source.is_file()
    assert second_source.is_file()


def test_prepare_all_does_not_delete_existing_file_on_failure(
    tmp_path: Path,
) -> None:
    from PIL import Image
    import pytest

    source_path = tmp_path / "source.png"
    Image.new("RGB", (800, 600)).save(source_path)

    attachment = ImageAttachment(path=source_path)

    profile_provider = ImageProfileProvider(
        profiles={
            PublishingDestination.FACEBOOK: ImageProfile(
                maximum_dimensions=ImageDimensions(
                    width=800,
                    height=800,
                ),
                output_format="JPEG",
            ),
        }
    )

    output_directory = tmp_path / "prepared"
    output_directory.mkdir()

    existing_path = output_directory / "source-facebook-1.jpg"
    original_content = b"Existing file must be preserved"
    existing_path.write_bytes(original_content)

    class FailingPreparationService(ImagePreparationService):
        # noinspection PyShadowingNames
        def prepare(
                self,
                attachment: ImageAttachment,
                destination: PublishingDestination,
                output_path: Path,
        ) -> Path:
            raise RuntimeError("Preparation failed.")

    service = FailingPreparationService(
        profile_provider=profile_provider,
    )

    with pytest.raises(RuntimeError, match="Preparation failed."):
        service.prepare_all(
            attachments=(attachment,),
            destination=PublishingDestination.FACEBOOK,
            output_directory=output_directory,
        )

    assert existing_path.is_file()
    assert existing_path.read_bytes() == original_content
    assert source_path.is_file()

def test_prepare_all_uses_unique_filename_when_output_exists(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.png"
    Image.new("RGB", (800, 600)).save(source_path)

    attachment = ImageAttachment(path=source_path)

    profile_provider = ImageProfileProvider(
        profiles={
            PublishingDestination.FACEBOOK: ImageProfile(
                maximum_dimensions=ImageDimensions(
                    width=800,
                    height=800,
                ),
                output_format="JPEG",
            ),
        }
    )

    service = ImagePreparationService(
        profile_provider=profile_provider,
    )

    output_directory = tmp_path / "prepared"
    output_directory.mkdir()

    existing_path = output_directory / "source-facebook-1.jpg"
    existing_content = b"Existing image must not be overwritten"
    existing_path.write_bytes(existing_content)

    prepared_images = service.prepare_all(
        attachments=(attachment,),
        destination=PublishingDestination.FACEBOOK,
        output_directory=output_directory,
    )

    assert len(prepared_images) == 1

    prepared_path = prepared_images[0].path

    assert prepared_path != existing_path
    assert prepared_path.is_file()
    assert prepared_path.suffix == ".jpg"

    assert existing_path.read_bytes() == existing_content

    with Image.open(prepared_path) as prepared_image:
        assert prepared_image.format == "JPEG"
        assert prepared_image.size == (800, 600)

    service.cleanup(prepared_images)

    assert not prepared_path.exists()
    assert existing_path.read_bytes() == existing_content
    assert source_path.is_file()


def test_prepare_all_preserves_reserved_output_filename(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.png"
    create_test_image(source_path, (800, 600))

    attachment = ImageAttachment(path=source_path)

    profile_provider = ImageProfileProvider(
        profiles={
            PublishingDestination.FACEBOOK: ImageProfile(
                maximum_dimensions=ImageDimensions(
                    width=800,
                    height=800,
                ),
                output_format="JPEG",
            ),
        }
    )

    service = ImagePreparationService(
        profile_provider=profile_provider,
    )

    output_directory = tmp_path / "prepared"
    output_directory.mkdir()

    reserved_path = output_directory / "source-facebook-1.jpg"

    with reserved_path.open("xb") as reserved_file:
        reserved_file.write(b"Reserved by another operation")

    prepared_images = service.prepare_all(
        attachments=(attachment,),
        destination=PublishingDestination.FACEBOOK,
        output_directory=output_directory,
    )

    assert len(prepared_images) == 1

    prepared_path = prepared_images[0].path

    assert prepared_path != reserved_path
    assert prepared_path.is_file()
    assert reserved_path.read_bytes() == b"Reserved by another operation"

    with Image.open(prepared_path) as image:
        assert image.format == "JPEG"
        assert image.size == (800, 600)

    service.cleanup(prepared_images)

    assert not prepared_path.exists()
    assert reserved_path.read_bytes() == b"Reserved by another operation"
    assert source_path.is_file()


def test_concurrent_preparation_uses_distinct_output_files(
    tmp_path: Path,
) -> None:
    from concurrent.futures import ThreadPoolExecutor

    source_path = tmp_path / "source.png"
    create_test_image(source_path, (800, 600))

    attachment = ImageAttachment(path=source_path)

    profile_provider = ImageProfileProvider(
        profiles={
            PublishingDestination.FACEBOOK: ImageProfile(
                maximum_dimensions=ImageDimensions(
                    width=800,
                    height=800,
                ),
                output_format="JPEG",
            ),
        }
    )

    service = ImagePreparationService(
        profile_provider=profile_provider,
    )

    output_directory = tmp_path / "prepared"

    def prepare_once() -> tuple[PreparedImage, ...]:
        return service.prepare_all(
            attachments=(attachment,),
            destination=PublishingDestination.FACEBOOK,
            output_directory=output_directory,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(prepare_once)
            for _ in range(2)
        ]

        first_result = futures[0].result()
        second_result = futures[1].result()

    first_path = first_result[0].path
    second_path = second_result[0].path

    assert first_path != second_path
    assert first_path.is_file()
    assert second_path.is_file()

    with Image.open(first_path) as first_image:
        assert first_image.format == "JPEG"

    with Image.open(second_path) as second_image:
        assert second_image.format == "JPEG"

    service.cleanup(first_result)
    service.cleanup(second_result)

    assert not first_path.exists()
    assert not second_path.exists()
    assert source_path.is_file()


def test_cleanup_does_not_remove_another_preparation_result(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.png"
    create_test_image(source_path, (800, 600))

    attachment = ImageAttachment(path=source_path)

    profile_provider = ImageProfileProvider(
        profiles={
            PublishingDestination.FACEBOOK: ImageProfile(
                maximum_dimensions=ImageDimensions(
                    width=800,
                    height=800,
                ),
                output_format="JPEG",
            ),
        }
    )

    service = ImagePreparationService(
        profile_provider=profile_provider,
    )

    output_directory = tmp_path / "prepared"

    first_result = service.prepare_all(
        attachments=(attachment,),
        destination=PublishingDestination.FACEBOOK,
        output_directory=output_directory,
    )

    second_result = service.prepare_all(
        attachments=(attachment,),
        destination=PublishingDestination.FACEBOOK,
        output_directory=output_directory,
    )

    first_path = first_result[0].path
    second_path = second_result[0].path

    assert first_path != second_path
    assert first_path.is_file()
    assert second_path.is_file()

    service.cleanup(first_result)

    assert not first_path.exists()
    assert second_path.is_file()

    with Image.open(second_path) as image:
        assert image.format == "JPEG"
        assert image.size == (800, 600)

    service.cleanup(second_result)

    assert not second_path.exists()
    assert source_path.is_file()


def test_cleanup_continues_when_prepared_image_is_missing(
    tmp_path: Path,
) -> None:
    first_source = tmp_path / "first.png"
    second_source = tmp_path / "second.png"

    create_test_image(first_source, (800, 600))
    create_test_image(second_source, (800, 600))

    profile_provider = ImageProfileProvider(
        profiles={
            PublishingDestination.FACEBOOK: ImageProfile(
                maximum_dimensions=ImageDimensions(
                    width=800,
                    height=800,
                ),
                output_format="JPEG",
            ),
        }
    )

    service = ImagePreparationService(
        profile_provider=profile_provider,
    )

    prepared_images = service.prepare_all(
        attachments=(
            ImageAttachment(path=first_source),
            ImageAttachment(path=second_source),
        ),
        destination=PublishingDestination.FACEBOOK,
        output_directory=tmp_path / "prepared",
    )

    first_path = prepared_images[0].path
    second_path = prepared_images[1].path

    assert first_path.is_file()
    assert second_path.is_file()

    first_path.unlink()

    service.cleanup(prepared_images)

    assert not first_path.exists()
    assert not second_path.exists()

    assert first_source.is_file()
    assert second_source.is_file()


def test_cleanup_reports_file_deletion_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source_path = tmp_path / "source.png"
    create_test_image(source_path, (800, 600))

    profile_provider = ImageProfileProvider(
        profiles={
            PublishingDestination.FACEBOOK: ImageProfile(
                maximum_dimensions=ImageDimensions(
                    width=800,
                    height=800,
                ),
                output_format="JPEG",
            ),
        }
    )

    service = ImagePreparationService(
        profile_provider=profile_provider,
    )

    prepared_images = service.prepare_all(
        attachments=(ImageAttachment(path=source_path),),
        destination=PublishingDestination.FACEBOOK,
        output_directory=tmp_path / "prepared",
    )

    prepared_path = prepared_images[0].path

    original_unlink = Path.unlink

    def failing_unlink(
        path: Path,
        missing_ok: bool = False,
    ) -> None:
        if path == prepared_path:
            raise PermissionError("Permission denied")

        original_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", failing_unlink)

    import pytest

    with pytest.raises(PermissionError, match="Permission denied"):
        service.cleanup(prepared_images)

    assert prepared_path.is_file()
    assert source_path.is_file()

def test_preserves_processing_error_when_partial_cleanup_fails(
    tmp_path,
    monkeypatch,
    caplog,
):
    from unittest.mock import Mock

    from socialflow.application.images.image_preparation_service import (
        ImagePreparationService,
    )
    from socialflow.domain.publishing.destination import (
        PublishingDestination,
    )

    service = ImagePreparationService(profile_provider=Mock())

    attachment = Mock()
    attachment.path = tmp_path / "source.jpg"

    expected_error = RuntimeError("Image processing failed.")

    monkeypatch.setattr(
        service,
        "prepare",
        Mock(side_effect=expected_error),
    )

    monkeypatch.setattr(
        service,
        "_output_filename",
        Mock(return_value="prepared.jpg"),
    )

    original_unlink = Path.unlink

    def failing_unlink(path, missing_ok=False):
        if path.name == "prepared.jpg":
            raise OSError("Temporary file deletion failed.")
        return original_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", failing_unlink)

    with pytest.raises(RuntimeError, match="Image processing failed") as exc:
        service.prepare_all(
            attachments=(attachment,),
            destination=PublishingDestination.WORDPRESS,
            output_directory=tmp_path / "prepared",
        )

    assert exc.value is expected_error

    assert "Failed to remove partially prepared image" in caplog.text
    assert "Temporary file deletion failed" in caplog.text

def test_partial_cleanup_continues_after_one_deletion_fails(
    tmp_path: Path,
    monkeypatch,
    caplog,
) -> None:
    from unittest.mock import Mock

    service = ImagePreparationService(
        profile_provider=Mock(),
    )

    first_source = tmp_path / "first.jpg"
    second_source = tmp_path / "second.jpg"

    first_source.touch()
    second_source.touch()

    first_attachment = ImageAttachment(path=first_source)
    second_attachment = ImageAttachment(path=second_source)

    processing_error = RuntimeError("Second image processing failed.")

    prepare_mock = Mock(
        side_effect=[
            tmp_path / "prepared" / "first.jpg",
            processing_error,
        ],
    )

    monkeypatch.setattr(
        service,
        "prepare",
        prepare_mock,
    )

    monkeypatch.setattr(
        service,
        "_output_filename",
        Mock(side_effect=["first.jpg", "second.jpg"]),
    )

    first_output = tmp_path / "prepared" / "first.jpg"
    second_output = tmp_path / "prepared" / "second.jpg"

    original_unlink = Path.unlink
    attempted_deletions: list[Path] = []

    def failing_unlink(
        path: Path,
        missing_ok: bool = False,
    ) -> None:
        attempted_deletions.append(path)

        if path == first_output:
            raise OSError("First temporary image could not be deleted.")

        original_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", failing_unlink)

    with pytest.raises(
        RuntimeError,
        match="Second image processing failed",
    ) as exc:
        service.prepare_all(
            attachments=(first_attachment, second_attachment),
            destination=PublishingDestination.WORDPRESS,
            output_directory=tmp_path / "prepared",
        )

    assert exc.value is processing_error

    assert attempted_deletions == [
        first_output,
        second_output,
    ]

    assert first_output.exists()
    assert not second_output.exists()

    assert "Failed to remove partially prepared image" in caplog.text
    assert "First temporary image could not be deleted" in caplog.text

    assert prepare_mock.call_count == 2