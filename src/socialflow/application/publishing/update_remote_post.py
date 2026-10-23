
from socialflow.application.publishing.remote_post_updater import (
    RemotePostUpdater,
)
from socialflow.domain.account.account import Account


class UpdateRemotePost:
    """Update an existing post through its remote platform."""

    def __init__(
        self,
        updater: RemotePostUpdater,
    ) -> None:
        self._updater = updater

    def execute(
        self,
        account: Account,
        post_id: int,
        content: str,
        tags: tuple[int, ...] | None = None,
    ) -> None:
        """Update remote post content and optionally its tags."""
        update_kwargs = {
            "account": account,
            "post_id": post_id,
            "content": content,
        }

        if tags is not None:
            update_kwargs["tags"] = tags

        self._updater.update_post(**update_kwargs)
