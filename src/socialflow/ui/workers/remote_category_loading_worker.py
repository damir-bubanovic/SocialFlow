
from PySide6.QtCore import QObject, Signal, Slot

from socialflow.application.categories.list_remote_categories import (
    ListRemoteCategories,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_category import RemoteCategory


class RemoteCategoryLoadingWorker(QObject):
    """Retrieve WordPress categories outside the UI thread."""

    finished = Signal(tuple)
    failed = Signal(str)

    def __init__(
        self,
        list_remote_categories: ListRemoteCategories,
        account: Account,
    ) -> None:
        super().__init__()
        self._list_remote_categories = list_remote_categories
        self._account = account

    @Slot()
    def run(self) -> None:
        """Emit the retrieved categories or an error."""
        try:
            categories: tuple[RemoteCategory, ...] = (
                self._list_remote_categories.execute(self._account)
            )
        except Exception as error:
            self.failed.emit(str(error))
            return

        self.finished.emit(categories)
