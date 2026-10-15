from socialflow.infrastructure.wordpress.wordpress_post import (
    WordPressPost,
)
from socialflow.infrastructure.wordpress.wordpress_post_client import (
    WordPressPostClient,
)
from socialflow.infrastructure.wordpress.wordpress_post_parser import (
    WordPressPostParser,
)


class WordPressPostRetriever:
    """Retrieve and parse recent WordPress posts."""

    def __init__(
        self,
        client: WordPressPostClient,
        parser: WordPressPostParser,
    ) -> None:
        self._client = client
        self._parser = parser

    def list_recent_posts(
        self,
        site_url: str,
        username: str,
        application_password: str,
        limit: int = 5,
    ) -> tuple[WordPressPost, ...]:
        """Return recent WordPress posts as typed models."""
        raw_posts = self._client.list_recent_posts(
            site_url=site_url,
            username=username,
            application_password=application_password,
            limit=limit,
        )

        return tuple(
            self._parser.parse(post)
            for post in raw_posts
        )