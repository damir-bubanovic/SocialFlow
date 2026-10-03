from socialflow.application.publishing.publisher import Publisher
from socialflow.domain.post.post import Post
from socialflow.application.publishing.errors import EmptyPostError


class PublishPost:
    """Application service for publishing a post."""

    def __init__(self, publisher: Publisher) -> None:
        self._publisher = publisher

    def execute(self, post: Post) -> None:
        """Publish the provided post."""
        if not post.has_content():
            raise EmptyPostError("Cannot publish a post without content.")

        self._publisher.publish(post)