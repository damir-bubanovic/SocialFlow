
from abc import ABC, abstractmethod

from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.remote_tag import RemoteTag


class RemoteTagProvider(ABC):
    """Contract for retrieving tags with remote platform IDs."""

    @abstractmethod
    def list_remote_tags(
        self,
        account: Account,
    ) -> tuple[RemoteTag, ...]:
        """Return the remote tags available for an account."""
