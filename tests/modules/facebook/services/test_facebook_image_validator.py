from PIL import Image
from pathlib import Path

import pytest

from socialflow.modules.facebook.services.facebook_image_validator import (
    FacebookImageValidator,
)
from socialflow.modules.posts.models.image_attachment import (
    ImageAttachment,
)


@pytest.mark.parametrize(
    "extension",
    [".jpg", ".jpeg", ".png", ".JPG", ".PNG"],
)
def test_accepts_supported_image_formats(
    tmp_path: Path,
    extension: str,
) -> None:
    path = tmp_path / f"image{extension}"
    path.write_bytes(b"test-image-data")

    attachment = ImageAttachment(path=path)

    assert FacebookImageValidator.validate(attachment) == path


def test_rejects_webp_image(tmp_path: Path) -> None:
    path = tmp_path / "image.webp"
    path.write_bytes(b"test-image-data")

    attachment = ImageAttachment(path=path)

    with pytest.raises(
        ValueError,
        match="supports JPEG and PNG only",
    ):
        FacebookImageValidator.validate(attachment)


def test_rejects_empty_image(tmp_path: Path) -> None:
    path = tmp_path / "empty.jpg"
    path.touch()

    attachment = ImageAttachment(path=path)

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        FacebookImageValidator.validate(attachment)


def test_rejects_deleted_image(tmp_path: Path) -> None:
    path = tmp_path / "deleted.jpg"
    path.write_bytes(b"test-image-data")

    attachment = ImageAttachment(path=path)
    path.unlink()

    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        FacebookImageValidator.validate(attachment)


@pytest.mark.parametrize(
    ("extension", "image_format"),
    [
        (".jpg", "JPEG"),
        (".jpeg", "JPEG"),
        (".png", "PNG"),
        (".JPG", "JPEG"),
        (".PNG", "PNG"),
    ],
)
def test_accepts_valid_image_content(
    tmp_path: Path,
    extension: str,
    image_format: str,
) -> None:
    path = tmp_path / f"valid{extension}"

    Image.new("RGB", (10, 10)).save(
        path,
        format=image_format,
    )

    attachment = ImageAttachment(path=path)

    assert FacebookImageValidator.validate_content(attachment) == path


@pytest.mark.parametrize(
    "extension",
    [".jpg", ".jpeg", ".png"],
)
def test_rejects_invalid_image_content(
    tmp_path: Path,
    extension: str,
) -> None:
    path = tmp_path / f"invalid{extension}"
    path.write_bytes(b"not-a-real-image")

    attachment = ImageAttachment(path=path)

    with pytest.raises(
        ValueError,
        match="invalid or corrupted image data",
    ):
        FacebookImageValidator.validate_content(attachment)


def test_rejects_mismatched_image_format(tmp_path: Path) -> None:
    path = tmp_path / "incorrect.jpg"

    Image.new("RGB", (10, 10)).save(
        path,
        format="PNG",
    )

    attachment = ImageAttachment(path=path)

    with pytest.raises(
        ValueError,
        match="does not match its extension",
    ):
        FacebookImageValidator.validate_content(attachment)


def test_rejects_truncated_image(tmp_path: Path) -> None:
    path = tmp_path / "truncated.png"

    Image.new("RGB", (10, 10)).save(
        path,
        format="PNG",
    )

    data = path.read_bytes()
    path.write_bytes(data[:20])

    attachment = ImageAttachment(path=path)

    with pytest.raises(
        ValueError,
        match="invalid or corrupted image data",
    ):
        FacebookImageValidator.validate_content(attachment)
