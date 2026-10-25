from abc import ABC, abstractmethod

from socialflow.domain.account.account import Account


class RemotePostUpdater(ABC):
    """Interface for updating existing posts on remote platforms."""

    @abstractmethod
    def update_post(
            self,
            account: Account,
            post_id: int,
            content: str,
            tags: tuple[int, ...] | None = None,
            featured_media_id: int | None = None,
            status: str | None = None,
    ) -> None:
        """Update post content and optionally tags, featured media, or status."""
