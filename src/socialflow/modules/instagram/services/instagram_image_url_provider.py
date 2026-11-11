
from abc import ABC, abstractmethod
from pathlib import Path


class InstagramImageUrlProvider(ABC):
    """Provide public HTTPS URLs for local Instagram images."""

    @abstractmethod
    def get_public_url(self, image_path: Path) -> str:
        """Return a publicly accessible HTTPS URL for an image.

        Implementations are responsible for making the image
        accessible to Instagram's servers before returning.

        Args:
            image_path: Local filesystem path of the image.

        Returns:
            A public HTTPS URL for the image.

        Raises:
            Exception: If the image cannot be made publicly accessible.
        """
        raise NotImplementedError
