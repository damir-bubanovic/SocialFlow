
from PySide6.QtCore import QObject, QThread, Signal

from socialflow.modules.accounts.workers.facebook_page_discovery_worker import (
    FacebookPageDiscoveryWorker,
)
from socialflow.modules.facebook.services.facebook_page_discovery_service import (
    FacebookPageDiscoveryService,
)


class FacebookPageDiscoveryController(QObject):
    """Manage the lifetime of a Facebook Page discovery worker."""

    result_ready = Signal(object)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        discovery_service: FacebookPageDiscoveryService,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._discovery_service = discovery_service
        self._thread: QThread | None = None
        self._worker: FacebookPageDiscoveryWorker | None = None

    @property
    def is_running(self) -> bool:
        """Return whether Page discovery is in progress."""
        return self._thread is not None

    def start(self, user_access_token: str) -> None:
        """Discover Facebook Pages in a background thread."""
        if self.is_running:
            return

        thread = QThread()
        worker = FacebookPageDiscoveryWorker(
            self._discovery_service,
            user_access_token,
        )
        worker.moveToThread(thread)

        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)

        worker.finished.connect(self.result_ready.emit)
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
        """Wait for active Page discovery before releasing resources."""
        thread = self._thread
        if thread is None:
            return

        thread.quit()
        thread.wait()
