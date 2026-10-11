from abc import ABC, abstractmethod
from pathlib import Path

from socialflow.infrastructure.wordpress.wordpress_media import (
    WordPressMedia,
)


class WordPressPostClient(ABC):
    """Transport contract for WordPress posts and media."""

    @abstractmethod
    def create_post(
        self,
        site_url: str,
        username: str,
        application_password: str,
        content: str,
    ) -> int:
        """Return the HTTP status code from the create-post request."""

    @abstractmethod
    def upload_media(
            self,
            site_url: str,
            username: str,
            application_password: str,
            image_path: Path,
    ) -> WordPressMedia:
        """Upload an image and return its WordPress media information."""

    @abstractmethod
    def delete_media(
            self,
            site_url: str,
            username: str,
            application_password: str,
            media_id: int,
    ) -> None:
        """Permanently delete an uploaded WordPress media item."""