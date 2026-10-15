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
    ) -> None:
        super().__init__()

        self._update_remote_post = update_remote_post
        self._account = account
        self._post_id = post_id
        self._content = content

    @Slot()
    def run(self) -> None:
        """Report the update outcome and always signal completion."""
        try:
            self._update_remote_post.execute(
                account=self._account,
                post_id=self._post_id,
                content=self._content,
            )
        except Exception as error:
            self.failed.emit(str(error))
        else:
            self.succeeded.emit()
        finally:
            self.finished.emit()