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
    ) -> None:
        """Update remote post content and optionally replace its tags."""
