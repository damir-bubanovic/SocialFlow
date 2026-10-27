from abc import ABC, abstractmethod

from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_post import RemotePost


class RemoteTrashedPostProvider(ABC):
    """Contract for retrieving posts currently in Trash."""

    @abstractmethod
    def list_trashed_posts(
        self,
        account: Account,
        limit: int = 50,
    ) -> tuple[RemotePost, ...]:
        """Return trashed posts for a connected account."""
