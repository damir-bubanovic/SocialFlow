from abc import ABC, abstractmethod

from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_post import RemotePost


class RemotePostProvider(ABC):
    """Contract for retrieving posts from connected platforms."""

    @abstractmethod
    def list_recent_posts(
        self,
        account: Account,
        limit: int = 5,
    ) -> tuple[RemotePost, ...]:
        """Retrieve recent posts for the selected account."""