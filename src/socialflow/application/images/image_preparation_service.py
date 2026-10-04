from pathlib import Path

from socialflow.application.images.destination_image_processor import (
    DestinationImageProcessor,
)
from socialflow.application.images.image_destination import ImageDestination
from socialflow.application.images.image_profile_provider import (
    ImageProfileProvider,
)
from socialflow.domain.post.image_attachment import ImageAttachment


class ImagePreparationService:
    """Prepares image attachments for publishing destinations."""

    def __init__(
        self,
        profile_provider: ImageProfileProvider,
    ) -> None:
        self._profile_provider = profile_provider

    def prepare(
        self,
        attachment: ImageAttachment,
        destination: ImageDestination,
        output_path: Path,
    ) -> Path:
        """Prepare an image according to its destination profile."""
        profile = self._profile_provider.profile_for(destination)

        return DestinationImageProcessor.process(
            attachment=attachment,
            profile=profile,
            output_path=output_path,
        )