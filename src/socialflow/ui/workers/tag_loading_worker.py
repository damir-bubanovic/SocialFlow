
from PySide6.QtCore import QObject, Signal, Slot

from socialflow.application.tags.list_tags import ListTags
from socialflow.domain.account.account import Account
from socialflow.domain.post.tag import Tag


class TagLoadingWorker(QObject):
    """Retrieve account tags without blocking the UI thread."""

    finished = Signal(tuple)
    failed = Signal(str)

    def __init__(
        self,
        list_tags: ListTags,
        account: Account,
    ) -> None:
        super().__init__()
        self._list_tags = list_tags
        self._account = account

    @Slot()
    def run(self) -> None:
        try:
            tags: tuple[Tag, ...] = self._list_tags.execute(
                self._account
            )
        except Exception as error:
            self.failed.emit(str(error))
            return

        self.finished.emit(tags)
