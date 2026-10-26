from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot

from socialflow.application.publishing.publish_post import PublishPost
from socialflow.domain.publishing.publish_request import PublishRequest
from socialflow.ui.posts.publishing_worker import PublishingWorker


class PublishingController(QObject):
    """Manage background publishing and worker lifetime."""

    progress = Signal(object)
    result_ready = Signal(object)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        publish_post: PublishPost,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._publish_post = publish_post
        self._thread: QThread | None = None
        self._worker: PublishingWorker | None = None
        self._shutting_down = False

    @property
    def is_running(self) -> bool:
        """Return whether publishing is in progress."""
        return self._thread is not None

    def start(self, request: PublishRequest) -> None:
        """Start publishing unless an operation is active."""
        if self._shutting_down or self.is_running:
            return

        thread = QThread()
        worker = PublishingWorker(self._publish_post, request)
        worker.moveToThread(thread)

        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)

        worker.progress.connect(self._on_worker_progress)
        worker.finished.connect(self._on_worker_results)
        worker.failed.connect(self._on_worker_error)

        worker.finished.connect(
            thread.quit,
            Qt.ConnectionType.DirectConnection,
        )
        worker.failed.connect(
            thread.quit,
            Qt.ConnectionType.DirectConnection,
        )

        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_thread_finished)

        thread.start()

    @Slot(object)
    def _on_worker_progress(self, result: object) -> None:
        """Forward progress unless shutdown has begun."""
        if self._shutting_down:
            return

        self.progress.emit(result)

    @Slot(object)
    def _on_worker_results(self, results: object) -> None:
        """Forward publishing results unless shutdown has begun."""
        if self._shutting_down:
            return

        self.result_ready.emit(results)

    @Slot(str)
    def _on_worker_error(self, message: str) -> None:
        """Forward publishing errors unless shutdown has begun."""
        if self._shutting_down:
            return

        self.error_occurred.emit(message)

    def _on_thread_finished(self) -> None:
        """Release resources after the thread has stopped."""
        thread = self._thread
        if thread is None:
            return

        thread.wait()
        self._worker = None
        self._thread = None

        thread.deleteLater()
        self.finished.emit()

    def shutdown(self) -> None:
        """Stop publishing and prevent future operations."""
        self._shutting_down = True

        thread = self._thread
        if thread is None:
            return

        thread.quit()
        thread.wait()

        self._on_thread_finished()
