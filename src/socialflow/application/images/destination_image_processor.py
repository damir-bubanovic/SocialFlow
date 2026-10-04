from pathlib import Path

from socialflow.application.images.image_processor import ImageProcessor
from socialflow.application.images.image_profile import ImageProfile
from socialflow.domain.post.image_attachment import ImageAttachment


class DestinationImageProcessor:
    """Processes an image according to destination requirements."""

    @staticmethod
    def process(
        attachment: ImageAttachment,
        profile: ImageProfile,
        output_path: Path,
    ) -> Path:
        """Process an attachment using the supplied image profile."""
        return ImageProcessor.process(
            attachment=attachment,
            maximum=profile.maximum_dimensions,
            output_path=output_path,
            output_format=profile.output_format,
            minimum_aspect_ratio=profile.minimum_aspect_ratio,
            maximum_aspect_ratio=profile.maximum_aspect_ratio,
        )