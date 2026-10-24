from PySide6.QtCore import QObject, QThread, Signal

from socialflow.application.publishing.list_remote_media import (
    ListRemoteMedia,
)
from socialflow.domain.account.account import Account
from socialflow.ui.workers.remote_media_loading_worker import (
    RemoteMediaLoadingWorker,
)


class RemoteMediaLoadingController(QObject):
    """Manage background retrieval of remote media."""

    media_ready = Signal(tuple)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        list_remote_media: ListRemoteMedia,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._list_remote_media = list_remote_media
        self._thread: QThread | None = None
        self._worker: RemoteMediaLoadingWorker | None = None
        self._shutting_down = False

    @property
    def is_running(self) -> bool:
        return self._thread is not None

    def start(self, account: Account, limit: int = 50) -> None:
        """Start retrieving media for an account."""
        if self._shutting_down or self.is_running:
            return

        thread = QThread()
        worker = RemoteMediaLoadingWorker(
            list_remote_media=self._list_remote_media,
            account=account,
            limit=limit,
        )

        worker.moveToThread(thread)

        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)
        worker.finished.connect(self.media_ready.emit)
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
        """Wait for any active worker before shutting down."""
        self._shutting_down = True

        thread = self._thread

        if thread is None:
            return

        thread.requestInterruption()
        thread.quit()
        thread.wait()

        if self._thread is thread:
            self._on_thread_finished()