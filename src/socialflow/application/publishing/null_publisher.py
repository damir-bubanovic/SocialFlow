from socialflow.application.publishing.publisher import Publisher
from socialflow.domain.post.post import Post


class NullPublisher(Publisher):
    """Publisher that intentionally performs no external publishing."""

    def publish(self, post: Post) -> None:
        """Accept the post without publishing it externally."""