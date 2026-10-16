from PySide6.QtCore import QObject, QThread, Qt, Signal

from socialflow.application.credentials.credential_store import CredentialStore
from socialflow.domain.account.account import Account
from socialflow.infrastructure.wordpress.wordpress_tag_client import (
    WordPressTagClient,
)
from socialflow.infrastructure.wordpress.wordpress_tag_creation_plan import (
    WordPressTagCreationPlan,
)
from socialflow.ui.workers.wordpress_tag_creation_worker import (
    WordPressTagCreationWorker,
)


class WordPressTagCreationController(QObject):
    """Manage approved WordPress tag creation in a background thread."""

    tags_created = Signal(object)
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
        self._worker: WordPressTagCreationWorker | None = None
        self._shutting_down = False

    @property
    def is_running(self) -> bool:
        """Return whether a tag creation operation is running."""
        return self._thread is not None

    def start(
        self,
        account: Account,
        plan: WordPressTagCreationPlan,
    ) -> None:
        if self._shutting_down or self.is_running:
            return

        if not plan.requires_confirmation:
            raise ValueError(
                "An approved plan with missing tags is required."
            )

        thread = QThread()
        worker = WordPressTagCreationWorker(
            account=account,
            plan=plan,
            credential_store=self._credential_store,
            tag_client=self._tag_client,
        )
        worker.moveToThread(thread)

        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)

        worker.finished.connect(self.tags_created.emit)
        worker.failed.connect(self.error_occurred.emit)

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