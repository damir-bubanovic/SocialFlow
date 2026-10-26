from datetime import datetime

from socialflow.infrastructure.wordpress.wordpress_post import (
    WordPressPost,
)


class WordPressPostParser:
    """Convert WordPress REST API data into typed post models."""

    @staticmethod
    def parse(data: dict) -> WordPressPost:
        """Parse a WordPress post, including tags and featured media."""

        raw_tags = data.get("tags", [])

        if not isinstance(raw_tags, list) or any(
            type(tag_id) is not int or tag_id <= 0
            for tag_id in raw_tags
        ):
            raise ValueError(
                "WordPress post tags must be positive integer IDs."
            )

        featured_media_id = data.get("featured_media", 0)

        if (
            type(featured_media_id) is not int
            or featured_media_id < 0
        ):
            raise ValueError(
                "WordPress featured media ID must be a "
                "non-negative integer."
            )


        excerpt_data = data.get("excerpt", {})

        if not isinstance(excerpt_data, dict):
            raise ValueError(
                "WordPress post excerpt must be an object."
            )

        excerpt = excerpt_data.get("raw")

        if excerpt is None:
            excerpt = excerpt_data.get("rendered", "")

        if not isinstance(excerpt, str):
            raise ValueError(
                "WordPress post excerpt must be a string."
            )


        return WordPressPost(
            id=int(data["id"]),
            content=str(data["content"]["rendered"]),
            published_at=datetime.fromisoformat(data["date"]),
            status=str(data["status"]),
            tag_ids=tuple(raw_tags),
            featured_media_id=featured_media_id,
            excerpt=excerpt,
        )