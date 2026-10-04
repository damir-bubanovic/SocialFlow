from dataclasses import dataclass

from socialflow.application.images.image_processor import ImageDimensions


@dataclass(frozen=True, slots=True)
class ImageProfile:
    """Image processing requirements for a publishing destination."""

    maximum_dimensions: ImageDimensions
    output_format: str
    minimum_aspect_ratio: float | None = None
    maximum_aspect_ratio: float | None = None

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

        if (
                self.minimum_aspect_ratio is not None
                and self.minimum_aspect_ratio <= 0
        ):
            raise ValueError(
                "Minimum aspect ratio must be greater than zero."
            )

        if (
                self.maximum_aspect_ratio is not None
                and self.maximum_aspect_ratio <= 0
        ):
            raise ValueError(
                "Maximum aspect ratio must be greater than zero."
            )

        if (
                self.minimum_aspect_ratio is not None
                and self.maximum_aspect_ratio is not None
                and self.minimum_aspect_ratio > self.maximum_aspect_ratio
        ):
            raise ValueError(
                "Minimum aspect ratio cannot exceed maximum aspect ratio."
            )