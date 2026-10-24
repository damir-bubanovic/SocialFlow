from PySide6.QtCore import QObject, Signal, Slot

from socialflow.application.publishing.list_remote_media import (
    ListRemoteMedia,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_media import RemoteMedia


class RemoteMediaLoadingWorker(QObject):
    """Retrieve remote media without blocking the UI thread."""

    finished = Signal(tuple)
    failed = Signal(str)

    def __init__(
        self,
        list_remote_media: ListRemoteMedia,
        account: Account,
        limit: int = 50,
    ) -> None:
        super().__init__()
        self._list_remote_media = list_remote_media
        self._account = account
        self._limit = limit

    @Slot()
    def run(self) -> None:
        """Retrieve media and emit the result or an error."""
        try:
            media: tuple[RemoteMedia, ...] = (
                self._list_remote_media.execute(
                    account=self._account,
                    limit=self._limit,
                )
            )
        except Exception as error:
            self.failed.emit(str(error))
            return

        self.finished.emit(media)