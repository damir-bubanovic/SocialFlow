from socialflow.application.categories.remote_category_provider import (
    RemoteCategoryProvider,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_category import RemoteCategory


class ListRemoteCategories:
    """Retrieve WordPress categories with their remote IDs."""

    def __init__(
        self,
        category_provider: RemoteCategoryProvider,
    ) -> None:
        self._category_provider = category_provider

    def execute(
        self,
        account: Account,
    ) -> tuple[RemoteCategory, ...]:
        """Return categories for the selected account."""
        return self._category_provider.list_remote_categories(account)