
"""Create approved remote tags outside the UI thread."""

from PySide6.QtCore import QObject, QThread, Signal, Slot

from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.remote_tag import RemoteTag
from socialflow.modules.posts.services.remote_tag_creation_service import (
    RemoteTagCreationService,
)
from socialflow.modules.posts.models.remote_tag_creation_plan import (
    RemoteTagCreationPlan,
)


class WordPressTagCreationWorker(QObject):
    """Create approved tags while respecting thread interruption."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        account: Account,
        plan: RemoteTagCreationPlan,
        tag_creation_service: RemoteTagCreationService,
    ) -> None:
        super().__init__()

        self._account = account
        self._plan = plan
        self._tag_creation_service = tag_creation_service

    @Slot()
    def run(self) -> None:
        try:
            created_tags = self._create_tags()
        except Exception as error:
            self.failed.emit(str(error))
            return

        self.finished.emit(created_tags)

    def _create_tags(self) -> tuple[RemoteTag, ...]:
        created_tags: list[RemoteTag] = []

        for tag in self._plan.missing_tags:
            thread = QThread.currentThread()

            if thread.isInterruptionRequested():
                raise InterruptedError(
                    "WordPress tag creation was interrupted."
                )

            result = self._tag_creation_service.create_approved_tags(
                account=self._account,
                approved_tags=(tag,),
            )

            if len(result) != 1 or not isinstance(result[0], RemoteTag):
                raise ValueError(
                    f"Invalid remote tag creation result for '{tag.name}'."
                )

            created_tags.append(result[0])

        return tuple(created_tags)
