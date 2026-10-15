from PySide6.QtCore import QObject, QThread, Signal

from socialflow.application.publishing.list_remote_posts import (
    ListRemotePosts,
)
from socialflow.domain.account.account import Account
from socialflow.ui.workers.remote_post_loading_worker import (
    RemotePostLoadingWorker,
)


class RemotePostLoadingController(QObject):
    """Manage background retrieval of remote posts."""

    posts_ready = Signal(tuple)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        list_remote_posts: ListRemotePosts,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._list_remote_posts = list_remote_posts
        self._thread: QThread | None = None
        self._worker: RemotePostLoadingWorker | None = None
        self._shutting_down = False

    @property
    def is_running(self) -> bool:
        return self._thread is not None

    def start(self, account: Account) -> None:
        """Start retrieving posts for an account."""
        if self._shutting_down or self.is_running:
            return

        thread = QThread()
        worker = RemotePostLoadingWorker(
            list_remote_posts=self._list_remote_posts,
            account=account,
        )

        worker.moveToThread(thread)

        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)
        worker.finished.connect(self.posts_ready.emit)
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