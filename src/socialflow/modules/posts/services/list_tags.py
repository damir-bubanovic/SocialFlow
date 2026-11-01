from socialflow.modules.posts.services.tag_provider import TagProvider
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.tag import Tag


class ListTags:
    """Application service for retrieving available account tags."""

    def __init__(self, tag_provider: TagProvider) -> None:
        self._tag_provider = tag_provider

    def execute(self, account: Account) -> tuple[Tag, ...]:
        """Return the tags available for an account."""
        return self._tag_provider.list_tags(account)