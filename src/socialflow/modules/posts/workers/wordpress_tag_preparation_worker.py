
"""Prepare remote tag creation plans outside the UI thread."""

from PySide6.QtCore import QObject, Signal, Slot

from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.tag import Tag
from socialflow.modules.posts.services.remote_tag_creation_service import (
    RemoteTagCreationService,
)
from socialflow.modules.posts.models.remote_tag_creation_plan import (
    RemoteTagCreationPlan,
)


class WordPressTagPreparationWorker(QObject):
    """Prepare missing tags using a platform service."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        account: Account,
        selected_tags: tuple[Tag, ...],
        tag_creation_service: RemoteTagCreationService,
    ) -> None:
        super().__init__()

        self._account = account
        self._selected_tags = selected_tags
        self._tag_creation_service = tag_creation_service

    @Slot()
    def run(self) -> None:
        try:
            plan = self._prepare()
        except Exception as error:
            self.failed.emit(str(error))
            return

        self.finished.emit(plan)

    def _prepare(self) -> RemoteTagCreationPlan:
        missing_tags = self._tag_creation_service.prepare_creation(
            account=self._account,
            selected_tags=self._selected_tags,
        )

        return RemoteTagCreationPlan(
            missing_tags=missing_tags,
        )
