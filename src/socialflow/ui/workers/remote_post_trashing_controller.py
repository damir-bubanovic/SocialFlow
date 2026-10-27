
from PySide6.QtCore import QObject, QThread, Signal

from socialflow.application.publishing.trash_remote_post import (
    TrashRemotePost,
)
from socialflow.domain.account.account import Account
from socialflow.ui.workers.remote_post_trashing_worker import (
    RemotePostTrashingWorker,
)


class RemotePostTrashingController(QObject):
    """Manage background moves of remote posts to Trash."""

    post_trashed = Signal()
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        trash_remote_post: TrashRemotePost,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._trash_remote_post = trash_remote_post
        self._thread: QThread | None = None
        self._worker: RemotePostTrashingWorker | None = None
        self._shutting_down = False

    @property
    def is_running(self) -> bool:
        return self._thread is not None

    def start(
        self,
        account: Account,
        post_id: int,
    ) -> None:
        """Start moving a remote post to Trash asynchronously."""
        if self._shutting_down or self.is_running:
            return

        thread = QThread()

        worker = RemotePostTrashingWorker(
            trash_remote_post=self._trash_remote_post,
            account=account,
            post_id=post_id,
        )

        worker.moveToThread(thread)

        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)

        worker.succeeded.connect(self._on_post_trashed)
        worker.failed.connect(self._on_trash_error)

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

    def _on_post_trashed(self) -> None:
        """Report success only while the controller is active."""
        if not self._shutting_down:
            self.post_trashed.emit()

    def _on_trash_error(self, message: str) -> None:
        """Report errors only while the controller is active."""
        if not self._shutting_down:
            self.error_occurred.emit(message)

    def shutdown(self) -> None:
        """Wait for an active Trash operation before shutting down."""
        self._shutting_down = True

        thread = self._thread

        if thread is None:
            return

        thread.requestInterruption()
        thread.quit()
        thread.wait()

        if self._thread is thread:
            self._on_thread_finished()
