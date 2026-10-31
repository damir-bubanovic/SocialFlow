
from PySide6.QtCore import QObject, Signal, Slot

from socialflow.domain.account.account import Account
from socialflow.infrastructure.wordpress.wordpress_category_provider import (
    WordPressCategoryProvider,
)


class WordPressCategoryCreationWorker(QObject):
    """Create one approved WordPress category in a background thread."""

    created = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        category_provider: WordPressCategoryProvider,
        account: Account,
        name: str,
        parent_id: int = 0,
    ) -> None:
        super().__init__()
        self._category_provider = category_provider
        self._account = account
        self._name = name
        self._parent_id = parent_id

    @Slot()
    def run(self) -> None:
        """Create the category and emit the result."""
        try:
            category = self._category_provider.create_category(
                account=self._account,
                name=self._name,
                parent_id=self._parent_id,
            )
        except Exception as error:
            self.failed.emit(str(error))
            return

        self.created.emit(category)
