
from abc import ABC, abstractmethod

from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.remote_category import RemoteCategory


class RemoteCategoryProvider(ABC):
    """Contract for retrieving and creating remote categories."""

    @abstractmethod
    def list_remote_categories(
        self,
        account: Account,
    ) -> tuple[RemoteCategory, ...]:
        """Return categories available for the account."""

    @abstractmethod
    def create_category(
        self,
        account: Account,
        name: str,
        parent_id: int = 0,
    ) -> RemoteCategory:
        """Create a remote category or subcategory."""
