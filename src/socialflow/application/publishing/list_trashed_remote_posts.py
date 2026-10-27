
from socialflow.application.publishing.remote_trashed_post_provider import (
    RemoteTrashedPostProvider,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_post import RemotePost


class ListTrashedRemotePosts:
    """Retrieve trashed posts from a connected account."""

    def __init__(
        self,
        provider: RemoteTrashedPostProvider,
    ) -> None:
        self._provider = provider

    def execute(
        self,
        account: Account,
        limit: int = 50,
    ) -> tuple[RemotePost, ...]:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError(
                "Post limit must be between 1 and 100."
            )

        return self._provider.list_trashed_posts(
            account=account,
            limit=limit,
        )
