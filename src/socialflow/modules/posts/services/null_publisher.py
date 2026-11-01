from socialflow.modules.posts.services.publisher import Publisher
from socialflow.modules.posts.services.prepared_post import PreparedPost


class NullPublisher(Publisher):
    """Publisher that intentionally performs no external publishing."""

    def publish(self, post: PreparedPost) -> None:
        """Accept the post without publishing it externally."""