from datetime import datetime

from socialflow.infrastructure.wordpress.wordpress_post import (
    WordPressPost,
)


class WordPressPostParser:
    """Convert WordPress REST API data into typed post models."""

    @staticmethod
    def parse(data: dict) -> WordPressPost:
        """Parse a single WordPress post, including its tag IDs."""
        raw_tags = data.get("tags", [])

        if not isinstance(raw_tags, list) or any(
            type(tag_id) is not int or tag_id <= 0
            for tag_id in raw_tags
        ):
            raise ValueError(
                "WordPress post tags must be positive integer IDs."
            )

        return WordPressPost(
            id=int(data["id"]),
            content=str(data["content"]["rendered"]),
            published_at=datetime.fromisoformat(data["date"]),
            status=str(data["status"]),
            tag_ids=tuple(raw_tags),
        )
