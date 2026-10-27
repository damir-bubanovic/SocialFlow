
from abc import ABC, abstractmethod

from socialflow.domain.account.account import Account


class RemotePostTrasher(ABC):
    """Interface for moving an existing remote post to Trash."""

    @abstractmethod
    def trash_post(
        self,
        account: Account,
        post_id: int,
    ) -> None:
        """Move the post to Trash without permanently deleting it."""
