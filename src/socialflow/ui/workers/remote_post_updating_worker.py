
from PySide6.QtCore import QObject, Signal, Slot

from socialflow.application.publishing.update_remote_post import (
    UpdateRemotePost,
)
from socialflow.domain.account.account import Account


class RemotePostUpdatingWorker(QObject):
    """Update an existing remote post without blocking the UI thread."""

    succeeded = Signal()
    finished = Signal()
    failed = Signal(str)

    def __init__(
            self,
            update_remote_post: UpdateRemotePost,
            account: Account,
            post_id: int,
            content: str,
            tags: tuple[int, ...] | None = None,
            featured_media_id: int | None = None,
            status: str | None = None,
            excerpt: str | None = None,
    ) -> None:
        super().__init__()

        self._update_remote_post = update_remote_post
        self._account = account
        self._post_id = post_id
        self._content = content
        self._tags = tags
        self._featured_media_id = featured_media_id
        self._status = status
        self._excerpt = excerpt

    @Slot()
    def run(self) -> None:
        """Report the update outcome and always signal completion."""
        try:
            update_kwargs = {
                "account": self._account,
                "post_id": self._post_id,
                "content": self._content,
            }

            if self._tags is not None:
                update_kwargs["tags"] = self._tags

            if self._featured_media_id is not None:
                update_kwargs["featured_media_id"] = (
                    self._featured_media_id
                )

            if self._status is not None:
                update_kwargs["status"] = self._status

            if self._excerpt is not None:
                update_kwargs["excerpt"] = self._excerpt

            self._update_remote_post.execute(**update_kwargs)
        except Exception as error:
            self.failed.emit(str(error))
        else:
            self.succeeded.emit()
        finally:
            self.finished.emit()
