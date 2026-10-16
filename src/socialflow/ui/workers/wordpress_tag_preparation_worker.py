from PySide6.QtCore import QObject, Signal, Slot

from socialflow.application.credentials.credential_store import CredentialStore
from socialflow.domain.account.account import Account
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)
from socialflow.infrastructure.wordpress.wordpress_tag_client import (
    WordPressTagClient,
)
from socialflow.infrastructure.wordpress.wordpress_tag_resolver import (
    WordPressTagResolver,
)


class WordPressTagPreparationWorker(QObject):
    """Prepare missing WordPress tags outside the UI thread."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        account: Account,
        selected_tags: tuple[Tag, ...],
        credential_store: CredentialStore,
        tag_client: WordPressTagClient,
    ) -> None:
        super().__init__()

        self._account = account
        self._selected_tags = selected_tags
        self._credential_store = credential_store
        self._tag_client = tag_client

    @Slot()
    def run(self) -> None:
        try:
            plan = self._prepare()
        except Exception as error:
            self.failed.emit(str(error))
            return

        self.finished.emit(plan)

    def _prepare(self):
        if self._account.destination is not PublishingDestination.WORDPRESS:
            raise ValueError("A WordPress account is required.")

        config = self._account.wordpress_config

        if config is None or not config.is_complete():
            raise ValueError("WordPress connection settings are incomplete.")

        config = config.normalized()

        password = self._credential_store.get(
            WordPressCredentialKeys.application_password(self._account)
        )

        if not password:
            raise ValueError("WordPress application password is missing.")

        remote_tags = self._tag_client.list_tags(
            site_url=config.site_url,
            username=config.username,
            application_password=password,
        )

        return WordPressTagResolver.prepare_creation_plan(
            selected_tags=self._selected_tags,
            remote_tags=remote_tags,
        )