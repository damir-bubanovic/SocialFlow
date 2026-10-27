
from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.application.publishing.remote_post_trasher import (
    RemotePostTrasher,
)
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)
from socialflow.infrastructure.wordpress.wordpress_post_client import (
    WordPressPostClient,
)


class WordPressPostTrasher(RemotePostTrasher):
    """Move WordPress posts to Trash using stored credentials."""

    def __init__(
        self,
        client: WordPressPostClient,
        credential_store: CredentialStore,
    ) -> None:
        self._client = client
        self._credential_store = credential_store

    def trash_post(
        self,
        account: Account,
        post_id: int,
    ) -> None:
        if account.destination != PublishingDestination.WORDPRESS:
            raise ValueError("A WordPress account is required.")

        config = account.wordpress_config

        if config is None or not config.is_complete():
            raise ValueError(
                "WordPress connection settings are incomplete."
            )

        if type(post_id) is not int or post_id <= 0:
            raise ValueError(
                "A valid WordPress post ID is required."
            )

        config = config.normalized()

        credential_key = (
            WordPressCredentialKeys.application_password(account)
        )

        application_password = self._credential_store.get(
            credential_key
        )

        if not application_password:
            raise ValueError(
                "WordPress application password is missing."
            )

        status = self._client.trash_post(
            site_url=config.site_url,
            username=config.username,
            application_password=application_password,
            post_id=post_id,
        )

        if status != 200:
            raise RuntimeError(
                f"WordPress post trash failed (HTTP {status})."
            )
