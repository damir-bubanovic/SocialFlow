from socialflow.application.images.image_profile import ImageProfile
from socialflow.domain.publishing.destination import PublishingDestination


class ImageProfileProvider:
    """Provides image processing profiles for publishing destinations."""

    def __init__(
        self,
        profiles: dict[PublishingDestination, ImageProfile] | None = None,
    ) -> None:
        self._profiles = profiles or {}

    def profile_for(
        self,
        destination: PublishingDestination,
    ) -> ImageProfile:
        """Return the image profile configured for a destination."""
        try:
            return self._profiles[destination]
        except KeyError as error:
            raise ValueError(
                f"No image profile configured for: {destination.value}"
            ) from error