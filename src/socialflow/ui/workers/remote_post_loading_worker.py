from PySide6.QtCore import QObject, Signal, Slot

from socialflow.application.publishing.list_remote_posts import (
    ListRemotePosts,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_post import RemotePost


class RemotePostLoadingWorker(QObject):
    """Retrieve remote posts without blocking the UI thread."""

    finished = Signal(tuple)
    failed = Signal(str)

    def __init__(
        self,
        list_remote_posts: ListRemotePosts,
        account: Account,
    ) -> None:
        super().__init__()
        self._list_remote_posts = list_remote_posts
        self._account = account

    @Slot()
    def run(self) -> None:
        """Retrieve posts and emit the result or an error."""
        try:
            posts: tuple[RemotePost, ...] = (
                self._list_remote_posts.execute(
                    account=self._account,
                    limit=5,
                )
            )
        except Exception as error:
            self.failed.emit(str(error))
            return

        self.finished.emit(posts)