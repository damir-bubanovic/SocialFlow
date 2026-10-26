
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
            featured_media_id: int | None = None,
            status: str | None = None,
            excerpt: str | None = None,
            title: str | None = None,
    ) -> None:
        """Update a remote post without changing omitted metadata."""
        update_kwargs = {
            "account": account,
            "post_id": post_id,
            "content": content,
        }

        if tags is not None:
            update_kwargs["tags"] = tags

        if featured_media_id is not None:
            update_kwargs["featured_media_id"] = featured_media_id

        if status is not None:
            update_kwargs["status"] = status

        if excerpt is not None:
            update_kwargs["excerpt"] = excerpt

        if title is not None:
            update_kwargs["title"] = title

        self._updater.update_post(**update_kwargs)
