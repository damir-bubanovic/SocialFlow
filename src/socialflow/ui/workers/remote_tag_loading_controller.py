
from PySide6.QtCore import QObject, QThread, Signal

from socialflow.application.tags.list_remote_tags import (
    ListRemoteTags,
)
from socialflow.domain.account.account import Account
from socialflow.ui.workers.remote_tag_loading_worker import (
    RemoteTagLoadingWorker,
)


class RemoteTagLoadingController(QObject):
    """Manage background retrieval of remote tags."""

    tags_ready = Signal(tuple)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        list_remote_tags: ListRemoteTags,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._list_remote_tags = list_remote_tags
        self._thread: QThread | None = None
        self._worker: RemoteTagLoadingWorker | None = None
        self._shutting_down = False

    @property
    def is_running(self) -> bool:
        """Return whether a remote-tag request is active."""
        return self._thread is not None

    def start(self, account: Account) -> None:
        """Start remote-tag retrieval in a background thread."""
        if self._shutting_down or self.is_running:
            return

        thread = QThread()
        worker = RemoteTagLoadingWorker(
            list_remote_tags=self._list_remote_tags,
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
