
from socialflow.modules.posts.services.remote_tag_provider import (
    RemoteTagProvider,
)
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.remote_tag import RemoteTag


class ListRemoteTags:
    """Retrieve tags with their remote IDs for an account."""

    def __init__(self, tag_provider: RemoteTagProvider) -> None:
        self._tag_provider = tag_provider

    def execute(self, account: Account) -> tuple[RemoteTag, ...]:
        """Return the remote tags available for an account."""
        return self._tag_provider.list_remote_tags(account)
