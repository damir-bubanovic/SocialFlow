from socialflow.application.publishing.remote_media_provider import (
    RemoteMediaProvider,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_media import RemoteMedia


class ListRemoteMedia:
    """Retrieve media from a connected account."""

    def __init__(
        self,
        provider: RemoteMediaProvider,
    ) -> None:
        self._provider = provider

    def execute(
        self,
        account: Account,
        limit: int = 50,
    ) -> tuple[RemoteMedia, ...]:
        """Return recent media for the selected account."""
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError(
                "Media limit must be between 1 and 100."
            )

        return self._provider.list_media(
            account=account,
            limit=limit,
        )