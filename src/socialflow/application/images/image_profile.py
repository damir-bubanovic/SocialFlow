from dataclasses import dataclass

from socialflow.application.images.image_processor import ImageDimensions


@dataclass(frozen=True, slots=True)
class ImageProfile:
    """Image processing requirements for a publishing destination."""

    maximum_dimensions: ImageDimensions
    output_format: str

    def __post_init__(self) -> None:
        """Validate the configured output image format."""
        supported_formats = {
            "JPEG",
            "PNG",
            "WEBP",
        }

        if self.output_format not in supported_formats:
            raise ValueError(
                f"Unsupported output image format: {self.output_format}"
            )