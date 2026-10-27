
from PySide6.QtCore import QObject, QThread, Signal

from socialflow.application.publishing.restore_remote_post import (
    RestoreRemotePost,
)
from socialflow.domain.account.account import Account
from socialflow.ui.workers.remote_post_restoring_worker import (
    RemotePostRestoringWorker,
)


class RemotePostRestoringController(QObject):
    """Manage background restoration of remote posts."""

    post_restored = Signal()
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        restore_remote_post: RestoreRemotePost,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._restore_remote_post = restore_remote_post
        self._thread: QThread | None = None
        self._worker: RemotePostRestoringWorker | None = None
        self._shutting_down = False

    @property
    def is_running(self) -> bool:
        return self._thread is not None

    def start(
        self,
        account: Account,
        post_id: int,
    ) -> None:
        """Restore a remote post asynchronously."""
        if self._shutting_down or self.is_running:
            return

        thread = QThread()

        worker = RemotePostRestoringWorker(
            restore_remote_post=self._restore_remote_post,
            account=account,
            post_id=post_id,
        )

        worker.moveToThread(thread)

        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)

        worker.succeeded.connect(self._on_post_restored)
        worker.failed.connect(self._on_restore_error)

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

    def _on_post_restored(self) -> None:
        """Report success only while the controller is active."""
        if not self._shutting_down:
            self.post_restored.emit()

    def _on_restore_error(self, message: str) -> None:
        """Report errors only while the controller is active."""
        if not self._shutting_down:
            self.error_occurred.emit(message)

    def shutdown(self) -> None:
        """Wait for an active Restore operation before shutting down."""
        self._shutting_down = True

        thread = self._thread

        if thread is None:
            return

        thread.requestInterruption()
        thread.quit()
        thread.wait()

        if self._thread is thread:
            self._on_thread_finished()
