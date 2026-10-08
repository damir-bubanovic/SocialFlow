from socialflow.application.publishing.errors import (
    PublisherNotConfiguredError,
)
from socialflow.application.publishing.prepared_post import PreparedPost
from socialflow.application.publishing.publisher import Publisher


class UnconfiguredPublisher(Publisher):
    """Reject publishing when no external platform is configured."""

    def publish(self, post: PreparedPost) -> None:
        """Prevent an unconfigured destination from reporting success."""
        raise PublisherNotConfiguredError(
            "External publishing is not configured."
        )