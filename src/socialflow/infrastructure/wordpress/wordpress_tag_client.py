from abc import ABC, abstractmethod

from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag


class WordPressTagClient(ABC):
    """Transport contract for WordPress tag operations."""

    @abstractmethod
    def list_tags(
        self,
        site_url: str,
        username: str,
        application_password: str,
    ) -> tuple[WordPressTag, ...]:
        """Retrieve tags from the WordPress REST API."""

    @abstractmethod
    def create_tag(
        self,
        site_url: str,
        username: str,
        application_password: str,
        name: str,
    ) -> WordPressTag:
        """Create a WordPress tag using the REST API."""