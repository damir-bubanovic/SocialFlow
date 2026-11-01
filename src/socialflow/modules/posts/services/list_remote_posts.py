from socialflow.modules.posts.services.remote_post_provider import (
    RemotePostProvider,
)
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.remote_post import RemotePost


class ListRemotePosts:
    """Retrieve recent posts from a connected account."""

    def __init__(
        self,
        provider: RemotePostProvider,
    ) -> None:
        self._provider = provider

    def execute(
        self,
        account: Account,
        limit: int = 5,
    ) -> tuple[RemotePost, ...]:
        """Return recent remote posts for an account."""
        return self._provider.list_recent_posts(
            account=account,
            limit=limit,
        )