from socialflow.application.publishing.publisher import Publisher
from socialflow.application.publishing.prepared_post import PreparedPost


class NullPublisher(Publisher):
    """Publisher that intentionally performs no external publishing."""

    def publish(self, post: PreparedPost) -> None:
        """Accept the post without publishing it externally."""