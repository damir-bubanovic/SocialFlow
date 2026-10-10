
from PySide6.QtCore import QObject, QThread, Signal

from socialflow.application.connections.connection_verifier import (
    ConnectionVerifier,
)
from socialflow.domain.account.account import Account
from socialflow.ui.accounts.wordpress_verification_worker import (
    WordPressVerificationWorker,
)


class WordPressVerificationController(QObject):
    """Manage the lifetime of a WordPress verification worker."""

    result_ready = Signal(object)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        verifier: ConnectionVerifier,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._verifier = verifier
        self._thread: QThread | None = None
        self._worker: WordPressVerificationWorker | None = None

    @property
    def is_running(self) -> bool:
        """Return whether verification is in progress."""
        return self._thread is not None

    def start(self, account: Account) -> None:
        """Start verification in a background thread."""
        if self.is_running:
            return

        thread = QThread()
        worker = WordPressVerificationWorker(
            self._verifier,
            account,
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
        """Clean up after the worker thread has stopped."""
        thread = self._thread
        if thread is None:
            return

        thread.wait()
        self._worker = None
        self._thread = None

        thread.deleteLater()
        self.finished.emit()

    def shutdown(self) -> None:
        """Wait for an active verification before releasing resources."""
        thread = self._thread
        if thread is None:
            return

        thread.quit()
        thread.wait()
