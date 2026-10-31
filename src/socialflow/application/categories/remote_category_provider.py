from abc import ABC, abstractmethod

from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_category import RemoteCategory


class RemoteCategoryProvider(ABC):
    """Contract for retrieving remote WordPress categories."""

    @abstractmethod
    def list_remote_categories(
        self,
        account: Account,
    ) -> tuple[RemoteCategory, ...]:
        """Return categories available for the account."""