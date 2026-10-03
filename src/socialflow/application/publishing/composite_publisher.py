from collections.abc import Iterable

from socialflow.application.publishing.publisher import Publisher
from socialflow.domain.post.post import Post


class CompositePublisher(Publisher):
    """Publishes a post through multiple publishers."""

    def __init__(self, publishers: Iterable[Publisher]) -> None:
        self._publishers = tuple(publishers)

    def publish(self, post: Post) -> None:
        """Publish the post through every configured publisher."""
        for publisher in self._publishers:
            publisher.publish(post)