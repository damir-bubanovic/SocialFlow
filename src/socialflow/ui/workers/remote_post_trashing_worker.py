
from PySide6.QtCore import QObject, Signal, Slot

from socialflow.application.publishing.trash_remote_post import (
    TrashRemotePost,
)
from socialflow.domain.account.account import Account


class RemotePostTrashingWorker(QObject):
    """Move a remote post to Trash without blocking the UI."""

    succeeded = Signal()
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        trash_remote_post: TrashRemotePost,
        account: Account,
        post_id: int,
    ) -> None:
        super().__init__()

        self._trash_remote_post = trash_remote_post
        self._account = account
        self._post_id = post_id

    @Slot()
    def run(self) -> None:
        """Report success or failure, then always signal completion."""
        try:
            self._trash_remote_post.execute(
                account=self._account,
                post_id=self._post_id,
            )
        except Exception as error:
            self.failed.emit(str(error))
        else:
            self.succeeded.emit()
        finally:
            self.finished.emit()
