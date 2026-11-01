from socialflow.modules.posts.services.errors import (
    PublisherNotConfiguredError,
)
from socialflow.modules.posts.services.prepared_post import PreparedPost
from socialflow.modules.posts.services.publisher import Publisher


class UnconfiguredPublisher(Publisher):
    """Reject publishing when no external platform is configured."""

    def publish(self, post: PreparedPost) -> None:
        """Prevent an unconfigured destination from reporting success."""
        raise PublisherNotConfiguredError(
            "External publishing is not configured."
        )