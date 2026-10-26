from PySide6.QtCore import QObject, QThread, Signal, Slot

from socialflow.application.credentials.credential_store import CredentialStore
from socialflow.domain.account.account import Account
from socialflow.domain.post.tag import Tag
from socialflow.infrastructure.wordpress.wordpress_tag_client import (
    WordPressTagClient,
)
from socialflow.ui.workers.wordpress_tag_preparation_worker import (
    WordPressTagPreparationWorker,
)


class WordPressTagPreparationController(QObject):
    """Manage background preparation of WordPress tag creation plans."""

    plan_ready = Signal(object)
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(
        self,
        credential_store: CredentialStore,
        tag_client: WordPressTagClient,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self._credential_store = credential_store
        self._tag_client = tag_client
        self._thread: QThread | None = None
        self._worker: WordPressTagPreparationWorker | None = None
        self._shutting_down = False

    @property
    def is_running(self) -> bool:
        return self._thread is not None

    def start(
        self,
        account: Account,
        selected_tags: tuple[Tag, ...],
    ) -> None:
        if self._shutting_down or self.is_running:
            return

        thread = QThread()
        worker = WordPressTagPreparationWorker(
            account=account,
            selected_tags=selected_tags,
            credential_store=self._credential_store,
            tag_client=self._tag_client,
        )
        worker.moveToThread(thread)

        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)

        worker.finished.connect(self._on_worker_plan_ready)
        worker.failed.connect(self._on_worker_error)

        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)

        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(self._on_thread_finished)

        thread.start()

    @Slot(object)
    def _on_worker_plan_ready(self, plan: object) -> None:
        """Forward the preparation plan unless shutdown has begun."""
        if self._shutting_down:
            return

        self.plan_ready.emit(plan)

    @Slot(str)
    def _on_worker_error(self, message: str) -> None:
        """Forward the preparation error unless shutdown has begun."""
        if self._shutting_down:
            return

        self.error_occurred.emit(message)

    def _on_thread_finished(self) -> None:
        thread = self._thread

        if thread is None:
            return

        thread.wait()

        self._worker = None
        self._thread = None

        thread.deleteLater()
        self.finished.emit()

    def shutdown(self) -> None:
        self._shutting_down = True

        thread = self._thread

        if thread is None:
            return

        thread.requestInterruption()
        thread.quit()
        thread.wait()

        if self._thread is thread:
            self._on_thread_finished()