from pathlib import Path

from socialflow.application.images.destination_image_processor import (
    DestinationImageProcessor,
)
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.application.images.image_profile_provider import (
    ImageProfileProvider,
)
from socialflow.application.images.prepared_image import PreparedImage
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
        destination: PublishingDestination,
        output_path: Path,
    ) -> Path:
        """Prepare an image according to its destination profile."""
        profile = self._profile_provider.profile_for(destination)

        return DestinationImageProcessor.process(
            attachment=attachment,
            profile=profile,
            output_path=output_path,
        )

    def prepare_all(
            self,
            attachments: tuple[ImageAttachment, ...],
            destination: PublishingDestination,
            output_directory: Path,
    ) -> tuple[PreparedImage, ...]:
        """Prepare multiple images for one publishing destination."""
        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        prepared_images = []

        for index, attachment in enumerate(
            attachments,
            start=1,
        ):
            output_path = output_directory / self._output_filename(
                attachment=attachment,
                destination=destination,
                index=index,
            )

            prepared_path = self.prepare(
                attachment=attachment,
                destination=destination,
                output_path=output_path,
            )

            prepared_images.append(
                PreparedImage(
                    source=attachment,
                    destination=destination,
                    path=prepared_path,
                )
            )

        return tuple(prepared_images)

    def _output_filename(
        self,
        attachment: ImageAttachment,
        destination: PublishingDestination,
        index: int,
    ) -> str:
        """Build a predictable filename for a prepared image."""
        profile = self._profile_provider.profile_for(destination)

        extensions = {
            "JPEG": ".jpg",
            "PNG": ".png",
            "WEBP": ".webp",
        }

        extension = extensions[profile.output_format]

        return (
            f"{attachment.path.stem}-"
            f"{destination.value}-"
            f"{index}"
            f"{extension}"
        )

    @staticmethod
    def cleanup(
            prepared_images: tuple[PreparedImage, ...],
    ) -> None:
        """Remove prepared image files that still exist."""
        for prepared_image in prepared_images:
            prepared_image.path.unlink(missing_ok=True)