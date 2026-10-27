from abc import ABC, abstractmethod

from socialflow.domain.account.account import Account


class RemotePostRestorer(ABC):
    """Interface for restoring a trashed remote post."""

    @abstractmethod
    def restore_post(
        self,
        account: Account,
        post_id: int,
    ) -> None:
        """Restore a trashed post as a draft."""
