from dataclasses import dataclass

from PIL import Image

from socialflow.domain.post.image_attachment import ImageAttachment


@dataclass(frozen=True, slots=True)
class ImageDimensions:
    """Width and height of an image in pixels."""

    width: int
    height: int

    def __post_init__(self) -> None:
        """Ensure image dimensions contain positive values."""
        if self.width <= 0:
            raise ValueError("Image width must be greater than zero.")

        if self.height <= 0:
            raise ValueError("Image height must be greater than zero.")


class ImageProcessor:
    """Provides platform-independent image processing operations."""

    @staticmethod
    def dimensions(
        attachment: ImageAttachment,
    ) -> ImageDimensions:
        """Return the original dimensions of an image."""
        with Image.open(attachment.path) as image:
            width, height = image.size

        return ImageDimensions(
            width=width,
            height=height,
        )

    @staticmethod
    def calculate_fit_dimensions(
        source: ImageDimensions,
        maximum: ImageDimensions,
    ) -> ImageDimensions:
        """Fit dimensions inside a maximum size without distortion."""
        if source.width <= maximum.width and source.height <= maximum.height:
            return source

        scale = min(
            maximum.width / source.width,
            maximum.height / source.height,
        )

        return ImageDimensions(
            width=round(source.width * scale),
            height=round(source.height * scale),
        )