
from PySide6.QtCore import QObject, QThread, Signal

from socialflow.application.tags.list_tags import ListTags
from socialflow.domain.account.account import Account
from socialflow.ui.workers.tag_loading_worker import (
    TagLoadingWorker,
)


class TagLoadingController(QObject):
    """Manage background tag retrieval and worker cleanup."""

    tags_ready = Signal(tuple)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        list_tags: ListTags,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._list_tags = list_tags
        self._thread: QThread | None = None
        self._worker: TagLoadingWorker | None = None
        self._shutting_down = False

    @property
    def is_running(self) -> bool:
        """Return whether tag retrieval is in progress."""
        return self._thread is not None

    def start(self, account: Account) -> None:
        """Start tag retrieval in a background thread."""
        if self._shutting_down or self.is_running:
            return

        thread = QThread()
        worker = TagLoadingWorker(
            list_tags=self._list_tags,
            account=account,
        )
        worker.moveToThread(thread)

        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)

        worker.finished.connect(self.tags_ready.emit)
        worker.failed.connect(self.error_occurred.emit)

        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)

        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_thread_finished)

        thread.start()

    def _on_thread_finished(self) -> None:
        """Release references after the worker thread stops."""
        thread = self._thread
        if thread is None:
            return

        thread.wait()

        self._worker = None
        self._thread = None

        thread.deleteLater()
        self.finished.emit()

    def shutdown(self) -> None:
        """Stop the worker and release its thread safely."""
        self._shutting_down = True

        thread = self._thread
        if thread is None:
            return

        thread.requestInterruption()
        thread.quit()
        thread.wait()

        if self._thread is thread:
            self._on_thread_finished()
