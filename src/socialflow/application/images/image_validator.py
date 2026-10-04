from PIL import Image, UnidentifiedImageError

from socialflow.domain.post.image_attachment import ImageAttachment


class ImageValidator:
    """Validates that image attachments contain readable image data."""

    @staticmethod
    def validate(attachment: ImageAttachment) -> None:
        """Raise ValueError when an attachment is not a readable image."""
        try:
            with Image.open(attachment.path) as image:
                image.verify()
        except (UnidentifiedImageError, OSError) as error:
            raise ValueError(
                f"Unreadable image file: {attachment.path}"
            ) from error