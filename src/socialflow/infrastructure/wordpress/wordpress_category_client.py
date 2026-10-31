
from abc import ABC, abstractmethod

from socialflow.infrastructure.wordpress.wordpress_category import (
    WordPressCategory,
)


class WordPressCategoryClient(ABC):
    """Transport contract for WordPress category operations."""

    @abstractmethod
    def list_categories(
        self,
        site_url: str,
        username: str,
        application_password: str,
    ) -> tuple[WordPressCategory, ...]:
        """Retrieve categories from the WordPress REST API."""

    @abstractmethod
    def create_category(
        self,
        site_url: str,
        username: str,
        application_password: str,
        name: str,
        parent_id: int = 0,
    ) -> WordPressCategory:
        """Create a top-level category or subcategory."""
