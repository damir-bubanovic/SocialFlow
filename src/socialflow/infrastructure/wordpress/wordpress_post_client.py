from abc import ABC, abstractmethod
from pathlib import Path

from socialflow.infrastructure.wordpress.wordpress_media import (
    WordPressMedia,
)


class WordPressPostClient(ABC):
    """Transport contract for WordPress posts and media."""

    @abstractmethod
    def list_recent_posts(
            self,
            site_url: str,
            username: str,
            application_password: str,
            limit: int = 5,
    ) -> list[dict]:
        """Retrieve recent WordPress posts, newest first."""

    @abstractmethod
    def list_trashed_posts(
            self,
            site_url: str,
            username: str,
            application_password: str,
            limit: int = 50,
    ) -> list[dict]:
        """Retrieve WordPress posts currently in Trash."""

    @abstractmethod
    def list_media(
        self,
        site_url: str,
        username: str,
        application_password: str,
        limit: int = 50,
    ) -> list[dict]:
        """Retrieve recent WordPress media library items."""

    @abstractmethod
    def create_post(
            self,
            site_url: str,
            username: str,
            application_password: str,
            content: str,
            tags: tuple[int, ...] = (),
            title: str = "",
            categories: tuple[int, ...] = (),
    ) -> int:
        """Return the HTTP status code from the create-post request."""

    @abstractmethod
    def update_post(
            self,
            site_url: str,
            username: str,
            application_password: str,
            post_id: int,
            content: str,
            tags: tuple[int, ...] | None = None,
            featured_media_id: int | None = None,
            status: str | None = None,
            excerpt: str | None = None,
            title: str | None = None,
    ) -> int:
        """Update post content and optional WordPress metadata."""

    @abstractmethod
    def trash_post(
            self,
            site_url: str,
            username: str,
            application_password: str,
            post_id: int,
    ) -> int:
        """Move a WordPress post to Trash and return the HTTP status."""

    @abstractmethod
    def restore_post(
            self,
            site_url: str,
            username: str,
            application_password: str,
            post_id: int,
    ) -> int:
        """Restore a trashed WordPress post as a draft."""

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