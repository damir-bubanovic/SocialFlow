
from socialflow.application.tags.remote_tag_provider import (
    RemoteTagProvider,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_tag import RemoteTag


class ListRemoteTags:
    """Retrieve tags with their remote IDs for an account."""

    def __init__(self, tag_provider: RemoteTagProvider) -> None:
        self._tag_provider = tag_provider

    def execute(self, account: Account) -> tuple[RemoteTag, ...]:
        """Return the remote tags available for an account."""
        return self._tag_provider.list_remote_tags(account)
