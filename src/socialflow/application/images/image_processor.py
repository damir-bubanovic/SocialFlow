from pathlib import Path
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
    def aspect_ratio(dimensions: ImageDimensions) -> float:
        """Return the width-to-height aspect ratio."""
        return dimensions.width / dimensions.height

    @staticmethod
    def aspect_ratio_is_allowed(
            dimensions: ImageDimensions,
            minimum: float | None,
            maximum: float | None,
    ) -> bool:
        """Return whether dimensions satisfy optional aspect-ratio limits."""
        ratio = ImageProcessor.aspect_ratio(dimensions)

        if minimum is not None and ratio < minimum:
            return False

        if maximum is not None and ratio > maximum:
            return False

        return True

    @staticmethod
    def calculate_aspect_ratio_dimensions(
            source: ImageDimensions,
            minimum: float | None,
            maximum: float | None,
    ) -> ImageDimensions:
        """Return dimensions constrained to optional aspect-ratio limits."""
        ratio = ImageProcessor.aspect_ratio(source)

        if minimum is not None and ratio < minimum:
            return ImageDimensions(
                width=round(source.height * minimum),
                height=source.height,
            )

        if maximum is not None and ratio > maximum:
            return ImageDimensions(
                width=source.width,
                height=round(source.width / maximum),
            )

        return source

    @staticmethod
    def pad_to_dimensions(
            image: Image.Image,
            target: ImageDimensions,
    ) -> Image.Image:
        """Pad an image to target dimensions without stretching it."""
        if image.width > target.width or image.height > target.height:
            raise ValueError(
                "Target dimensions cannot be smaller than the source image."
            )

        if image.width == target.width and image.height == target.height:
            return image.copy()

        padded = Image.new(
            "RGB",
            (target.width, target.height),
            "white",
        )

        x = (target.width - image.width) // 2
        y = (target.height - image.height) // 2

        if image.mode == "RGBA":
            padded.paste(
                image,
                (x, y),
                image,
            )
        else:
            padded.paste(
                image.convert("RGB"),
                (x, y),
            )

        return padded

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

    @staticmethod
    def process(
            attachment: ImageAttachment,
            maximum: ImageDimensions,
            output_path: Path,
            output_format: str,
            minimum_aspect_ratio: float | None = None,
            maximum_aspect_ratio: float | None = None,
    ) -> Path:
        """Process an image and save the result without changing the source."""
        with Image.open(attachment.path) as source:
            image = source.convert("RGB")

            source_dimensions = ImageDimensions(
                width=image.width,
                height=image.height,
            )

            aspect_dimensions = (
                ImageProcessor.calculate_aspect_ratio_dimensions(
                    source_dimensions,
                    minimum=minimum_aspect_ratio,
                    maximum=maximum_aspect_ratio,
                )
            )

            if aspect_dimensions != source_dimensions:
                image = ImageProcessor.pad_to_dimensions(
                    image,
                    aspect_dimensions,
                )

            fitted_dimensions = ImageProcessor.calculate_fit_dimensions(
                ImageDimensions(
                    width=image.width,
                    height=image.height,
                ),
                maximum,
            )

            if (
                    image.width != fitted_dimensions.width
                    or image.height != fitted_dimensions.height
            ):
                image = image.resize(
                    (
                        fitted_dimensions.width,
                        fitted_dimensions.height,
                    ),
                    Image.Resampling.LANCZOS,
                )

            image.save(
                output_path,
                format=output_format,
            )

        return output_path