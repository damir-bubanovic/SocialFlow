
from PySide6.QtCore import (
    QObject,
    QThread,
    Qt,
    Signal,
    Slot,
)

from socialflow.domain.account.account import Account
from socialflow.infrastructure.wordpress.wordpress_category_provider import (
    WordPressCategoryProvider,
)
from socialflow.ui.workers.wordpress_category_creation_worker import (
    WordPressCategoryCreationWorker,
)


class WordPressCategoryCreationController(QObject):
    """Manage background WordPress category creation."""

    category_created = Signal(object)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        category_provider: WordPressCategoryProvider,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._category_provider = category_provider
        self._thread: QThread | None = None
        self._worker: WordPressCategoryCreationWorker | None = None
        self._shutting_down = False

    @property
    def is_running(self) -> bool:
        return self._thread is not None

    def start(
        self,
        account: Account,
        name: str,
        parent_id: int = 0,
    ) -> None:
        """Start an approved category creation request."""
        if self._shutting_down or self.is_running:
            return

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError("Category name is required.")

        if type(parent_id) is not int or parent_id < 0:
            raise ValueError(
                "Parent category ID must be a non-negative integer."
            )

        thread = QThread()
        worker = WordPressCategoryCreationWorker(
            category_provider=self._category_provider,
            account=account,
            name=normalized_name,
            parent_id=parent_id,
        )
        worker.moveToThread(thread)

        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)

        worker.created.connect(self._on_created)
        worker.failed.connect(self._on_error)

        worker.created.connect(
            thread.quit,
            Qt.ConnectionType.DirectConnection,
        )
        worker.failed.connect(
            thread.quit,
            Qt.ConnectionType.DirectConnection,
        )

        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_thread_finished)

        thread.start()

    @Slot(object)
    def _on_created(self, category: object) -> None:
        if not self._shutting_down:
            self.category_created.emit(category)

    @Slot(str)
    def _on_error(self, message: str) -> None:
        if not self._shutting_down:
            self.error_occurred.emit(message)

    def _on_thread_finished(self) -> None:
        thread = self._thread

        if thread is None:
            return

        thread.wait()

        self._worker = None
        self._thread = None

        thread.deleteLater()
        self.finished.emit()

    def shutdown(self) -> None:
        """Wait for any active request to finish."""
        self._shutting_down = True

        thread = self._thread

        if thread is None:
            return

        thread.requestInterruption()
        thread.quit()
        thread.wait()

        if self._thread is thread:
            self._on_thread_finished()
