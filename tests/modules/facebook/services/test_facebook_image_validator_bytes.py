from io import BytesIO

import pytest
from PIL import Image

from socialflow.modules.facebook.services.facebook_image_validator import (
    FacebookImageValidator,
)


def make_image_bytes(image_format: str) -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (2, 2), color="red")
    image.save(buffer, format=image_format)
    return buffer.getvalue()


@pytest.mark.parametrize(
    ("image_format", "extension"),
    [
        ("JPEG", ".jpg"),
        ("JPEG", ".jpeg"),
        ("PNG", ".png"),
        ("JPEG", ".JPG"),
        ("PNG", ".PNG"),
    ],
)
def test_validate_bytes_accepts_matching_images(
    image_format: str,
    extension: str,
) -> None:
    image_data = make_image_bytes(image_format)

    result = FacebookImageValidator.validate_bytes(
        image_data,
        extension,
    )

    assert result == image_format


@pytest.mark.parametrize(
    ("image_format", "extension"),
    [
        ("JPEG", ".png"),
        ("PNG", ".jpg"),
        ("PNG", ".jpeg"),
    ],
)
def test_validate_bytes_rejects_extension_mismatch(
    image_format: str,
    extension: str,
) -> None:
    image_data = make_image_bytes(image_format)

    with pytest.raises(
        ValueError,
        match="Facebook image content does not match its extension",
    ):
        FacebookImageValidator.validate_bytes(
            image_data,
            extension,
        )


@pytest.mark.parametrize(
    "image_data",
    [
        b"",
        b"not an image",
        b"\\x00\\x01\\x02\\x03",
    ],
)
def test_validate_bytes_rejects_invalid_image_data(
    image_data: bytes,
) -> None:
    with pytest.raises(
        ValueError,
        match="Facebook image contains invalid or corrupted image data",
    ):
        FacebookImageValidator.validate_bytes(
            image_data,
            ".jpg",
        )
