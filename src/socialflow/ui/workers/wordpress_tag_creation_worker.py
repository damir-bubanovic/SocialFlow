from PySide6.QtCore import QObject, Signal, Slot

from socialflow.application.credentials.credential_store import CredentialStore
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)
from socialflow.infrastructure.wordpress.wordpress_tag_client import (
    WordPressTagClient,
)
from socialflow.infrastructure.wordpress.wordpress_tag_creation_plan import (
    WordPressTagCreationPlan,
)
from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag
from socialflow.infrastructure.wordpress.wordpress_tag_name_normalizer import (
    WordPressTagNameNormalizer,
)


class WordPressTagCreationWorker(QObject):
    """Create explicitly approved WordPress tags in a background thread."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        account: Account,
        plan: WordPressTagCreationPlan,
        credential_store: CredentialStore,
        tag_client: WordPressTagClient,
    ) -> None:
        super().__init__()

        self._account = account
        self._plan = plan
        self._credential_store = credential_store
        self._tag_client = tag_client

    @Slot()
    def run(self) -> None:
        try:
            created_tags = self._create_tags()
        except Exception as error:
            self.failed.emit(str(error))
            return

        self.finished.emit(created_tags)

    def _create_tags(self) -> tuple:
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

        created_tags = []

        for name in self._plan.tag_names:
            created_tag = self._tag_client.create_tag(
                site_url=config.site_url,
                username=config.username,
                application_password=password,
                name=name,
            )

            if not isinstance(created_tag, WordPressTag):
                raise ValueError(
                    f"Invalid WordPress tag creation result for '{name}'."
                )

            if (
                WordPressTagNameNormalizer.normalize(created_tag.name)
                != WordPressTagNameNormalizer.normalize(name)
            ):
                raise ValueError(
                    f"Invalid WordPress tag creation result for '{name}': "
                    f"received '{created_tag.name}'."
                )

            created_tags.append(created_tag)

        return tuple(created_tags)