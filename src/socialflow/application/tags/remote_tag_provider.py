
from abc import ABC, abstractmethod

from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_tag import RemoteTag


class RemoteTagProvider(ABC):
    """Contract for retrieving tags with remote platform IDs."""

    @abstractmethod
    def list_remote_tags(
        self,
        account: Account,
    ) -> tuple[RemoteTag, ...]:
        """Return the remote tags available for an account."""
