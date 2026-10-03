from abc import ABC, abstractmethod

from socialflow.domain.post.post import Post


class Publisher(ABC):
    """Contract for publishing SocialFlow posts."""

    @abstractmethod
    def publish(self, post: Post) -> None:
        """Publish a post."""