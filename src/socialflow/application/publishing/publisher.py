from abc import ABC, abstractmethod

from socialflow.application.publishing.prepared_post import PreparedPost


class Publisher(ABC):
    """Contract for publishing prepared SocialFlow posts."""

    @abstractmethod
    def publish(self, post: PreparedPost) -> None:
        """Publish a prepared post."""