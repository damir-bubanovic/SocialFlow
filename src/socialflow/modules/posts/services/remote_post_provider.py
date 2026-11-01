from abc import ABC, abstractmethod

from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.remote_post import RemotePost


class RemotePostProvider(ABC):
    """Contract for retrieving posts from connected platforms."""

    @abstractmethod
    def list_recent_posts(
        self,
        account: Account,
        limit: int = 5,
    ) -> tuple[RemotePost, ...]:
        """Retrieve recent posts for the selected account."""