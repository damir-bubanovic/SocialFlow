from dataclasses import dataclass

from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination


@dataclass(frozen=True, slots=True)
class PublishRequest:
    """A post together with its selected publishing destinations."""

    post: Post
    destinations: tuple[PublishingDestination, ...]