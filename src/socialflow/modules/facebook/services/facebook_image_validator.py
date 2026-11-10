from io import BytesIO
from PIL import Image, UnidentifiedImageError
from pathlib import Path

from socialflow.modules.posts.models.image_attachment import (
    ImageAttachment,
)


FACEBOOK_SUPPORTED_IMAGE_EXTENSIONS = frozenset({
    ".jpg",
    ".jpeg",
    ".png",
})


class FacebookImageValidator:
    """Validate image attachments for Facebook Page publishing."""

    @staticmethod
    def validate(attachment: ImageAttachment) -> Path:
        """Return a validated image path or raise ValueError."""
        path = attachment.path

        if path.suffix.lower() not in FACEBOOK_SUPPORTED_IMAGE_EXTENSIONS:
            raise ValueError(
                "Facebook image publishing supports JPEG and PNG only."
            )

        if not path.is_file():
            raise ValueError(
                "Facebook image file does not exist."
            )

        if path.stat().st_size == 0:
            raise ValueError(
                "Facebook image file must not be empty."
            )

        return path


    @staticmethod
    def validate_content(attachment: ImageAttachment) -> Path:
        """Verify that an attachment contains a valid JPEG or PNG."""
        path = FacebookImageValidator.validate(attachment)

        try:
            image_data = path.read_bytes()
        except OSError:
            raise ValueError(
                "Facebook image file could not be read."
            ) from None

        FacebookImageValidator.validate_bytes(
            image_data,
            path.suffix.lower(),
        )

        return path

    @staticmethod
    def validate_bytes(image_data: bytes, extension: str) -> str:
        """Validate exact JPEG/PNG bytes and return the image format."""
        expected_formats = {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
        }

        expected_format = expected_formats[extension.lower()]

        try:
            with Image.open(BytesIO(image_data)) as image:
                actual_format = image.format
                image.verify()
        except (
            UnidentifiedImageError,
            OSError,
            SyntaxError,
            ValueError,
        ):
            raise ValueError(
                "Facebook image contains invalid or corrupted image data."
            ) from None

        if actual_format != expected_format:
            raise ValueError(
                "Facebook image content does not match its extension."
            )

        return expected_format
