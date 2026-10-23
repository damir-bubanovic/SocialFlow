
from PySide6.QtCore import QObject, Signal, Slot

from socialflow.application.tags.list_remote_tags import (
    ListRemoteTags,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_tag import RemoteTag


class RemoteTagLoadingWorker(QObject):
    """Retrieve remote tags without blocking the UI thread."""

    finished = Signal(tuple)
    failed = Signal(str)

    def __init__(
        self,
        list_remote_tags: ListRemoteTags,
        account: Account,
    ) -> None:
        super().__init__()
        self._list_remote_tags = list_remote_tags
        self._account = account

    @Slot()
    def run(self) -> None:
        """Retrieve tags and emit either the result or an error."""
        try:
            tags: tuple[RemoteTag, ...] = (
                self._list_remote_tags.execute(self._account)
            )
        except Exception as error:
            self.failed.emit(str(error))
            return

        self.finished.emit(tags)
