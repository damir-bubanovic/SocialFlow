from abc import ABC, abstractmethod

from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.remote_media import RemoteMedia


class RemoteMediaProvider(ABC):
    """Contract for retrieving media from connected platforms."""

    @abstractmethod
    def list_media(
        self,
        account: Account,
        limit: int = 50,
    ) -> tuple[RemoteMedia, ...]:
        """Retrieve recent media for the selected account."""