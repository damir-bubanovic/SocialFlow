from datetime import datetime

from socialflow.infrastructure.wordpress.wordpress_post import (
    WordPressPost,
)


class WordPressPostParser:
    """Convert WordPress REST API data into typed post models."""

    @staticmethod
    def parse(data: dict) -> WordPressPost:
        """Parse a single WordPress post."""

        return WordPressPost(
            id=int(data["id"]),
            content=str(data["content"]["rendered"]),
            published_at=datetime.fromisoformat(data["date"]),
            status=str(data["status"]),
        )