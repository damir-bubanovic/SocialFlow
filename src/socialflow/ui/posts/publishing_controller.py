
from PySide6.QtCore import QObject, QThread, Signal

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

    @property
    def is_running(self) -> bool:
        """Return whether publishing is in progress."""
        return self._thread is not None

    def start(self, request: PublishRequest) -> None:
        """Start publishing unless an operation is active."""
        if self.is_running:
            return

        thread = QThread()
        worker = PublishingWorker(self._publish_post, request)
        worker.moveToThread(thread)

        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)

        worker.progress.connect(self.progress.emit)
        worker.finished.connect(self.result_ready.emit)
        worker.failed.connect(self.error_occurred.emit)

        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)

        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_thread_finished)

        thread.start()

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
        """Wait for active publishing before releasing resources."""
        thread = self._thread
        if thread is None:
            return

        thread.quit()
        thread.wait()
