
from PySide6.QtCore import QObject, QThread, Signal

from socialflow.application.categories.list_remote_categories import (
    ListRemoteCategories,
)
from socialflow.domain.account.account import Account
from socialflow.ui.workers.remote_category_loading_worker import (
    RemoteCategoryLoadingWorker,
)


class RemoteCategoryLoadingController(QObject):
    """Manage asynchronous WordPress category retrieval."""

    categories_ready = Signal(tuple)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        list_remote_categories: ListRemoteCategories,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._list_remote_categories = list_remote_categories
        self._thread: QThread | None = None
        self._worker: RemoteCategoryLoadingWorker | None = None
        self._shutting_down = False

    @property
    def is_running(self) -> bool:
        return self._thread is not None

    def start(self, account: Account) -> None:
        """Start a request if no category request is running."""
        if self._shutting_down or self.is_running:
            return

        thread = QThread()
        worker = RemoteCategoryLoadingWorker(
            list_remote_categories=self._list_remote_categories,
            account=account,
        )
        worker.moveToThread(thread)

        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)

        worker.finished.connect(self.categories_ready.emit)
        worker.failed.connect(self.error_occurred.emit)

        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)

        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_thread_finished)

        thread.start()

    def _on_thread_finished(self) -> None:
        """Release the completed worker and notify listeners."""
        thread = self._thread

        if thread is None:
            return

        thread.wait()

        self._worker = None
        self._thread = None

        thread.deleteLater()
        self.finished.emit()

    def shutdown(self) -> None:
        """Wait for the active request before releasing its thread."""
        self._shutting_down = True

        thread = self._thread

        if thread is None:
            return

        thread.requestInterruption()
        thread.quit()
        thread.wait()

        if self._thread is thread:
            self._on_thread_finished()
