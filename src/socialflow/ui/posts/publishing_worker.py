
"""Qt worker for executing publishing outside the UI thread."""

import logging

from PySide6.QtCore import QObject, Signal, Slot

from socialflow.application.publishing.errors import PublishingError
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.domain.publishing.publish_request import PublishRequest

logger = logging.getLogger(__name__)


class PublishingWorker(QObject):
    """Execute a single publishing request and report its outcome."""

    progress = Signal(object)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        publish_post: PublishPost,
        request: PublishRequest,
    ) -> None:
        super().__init__()
        self._publish_post = publish_post
        self._request = request

    @Slot()
    def run(self) -> None:
        """Execute publishing and emit exactly one completion signal."""
        try:
            results = self._publish_post.execute(
                self._request,
                on_progress=self.progress.emit,
            )
        except PublishingError:
            logger.exception("Background publishing failed")
            self.failed.emit("Publishing could not be completed.")
        else:
            self.finished.emit(results)