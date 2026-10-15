from PySide6.QtCore import QObject, QThread, Signal

from socialflow.application.publishing.update_remote_post import (
    UpdateRemotePost,
)
from socialflow.domain.account.account import Account
from socialflow.ui.workers.remote_post_updating_worker import (
    RemotePostUpdatingWorker,
)


class RemotePostUpdatingController(QObject):
    """Manage background updates of existing remote posts."""

    post_updated = Signal()
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        update_remote_post: UpdateRemotePost,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._update_remote_post = update_remote_post
        self._thread: QThread | None = None
        self._worker: RemotePostUpdatingWorker | None = None
        self._shutting_down = False

    @property
    def is_running(self) -> bool:
        return self._thread is not None

    def start(
        self,
        account: Account,
        post_id: int,
        content: str,
    ) -> None:
        """Start updating an existing remote post."""
        if self._shutting_down or self.is_running:
            return

        thread = QThread()
        worker = RemotePostUpdatingWorker(
            update_remote_post=self._update_remote_post,
            account=account,
            post_id=post_id,
            content=content,
        )

        worker.moveToThread(thread)

        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)

        worker.succeeded.connect(self._on_post_updated)
        worker.failed.connect(self._on_update_error)

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

    def _on_post_updated(self) -> None:
        """Report success only while the controller is active."""
        if not self._shutting_down:
            self.post_updated.emit()

    def _on_update_error(self, message: str) -> None:
        """Report errors only while the controller is active."""
        if not self._shutting_down:
            self.error_occurred.emit(message)

    def shutdown(self) -> None:
        """Wait for an active update before shutting down."""
        self._shutting_down = True

        thread = self._thread

        if thread is None:
            return

        thread.requestInterruption()
        thread.quit()
        thread.wait()

        if self._thread is thread:
            self._on_thread_finished()