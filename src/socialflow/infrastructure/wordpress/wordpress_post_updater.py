from socialflow.application.credentials.credential_store import (
    CredentialStore,
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
from socialflow.application.publishing.remote_post_updater import (
    RemotePostUpdater,
)


class WordPressPostUpdater(RemotePostUpdater):
    """Update an existing post for a configured WordPress account."""

    def __init__(
        self,
        client: WordPressPostClient,
        credential_store: CredentialStore,
    ) -> None:
        self._client = client
        self._credential_store = credential_store


    def update_post(
        self,
        account: Account,
        post_id: int,
        content: str,
        tags: tuple[int, ...] | None = None,
    ) -> None:
        if account.destination != PublishingDestination.WORDPRESS:
            raise ValueError("A WordPress account is required.")

        config = account.wordpress_config

        if config is None or not config.is_complete():
            raise ValueError(
                "WordPress connection settings are incomplete."
            )

        if type(post_id) is not int or post_id <= 0:
            raise ValueError("A valid WordPress post ID is required.")

        if not isinstance(content, str) or not content.strip():
            raise ValueError("WordPress post content is required.")

        if tags is not None:
            if not isinstance(tags, tuple) or any(
                type(tag_id) is not int or tag_id <= 0
                for tag_id in tags
            ):
                raise ValueError(
                    "WordPress tag IDs must be positive integers."
                )

        config = config.normalized()

        credential_key = WordPressCredentialKeys.application_password(
            account
        )

        application_password = self._credential_store.get(
            credential_key
        )

        if not application_password:
            raise ValueError(
                "WordPress application password is missing."
            )

        update_kwargs = {
            "site_url": config.site_url,
            "username": config.username,
            "application_password": application_password,
            "post_id": post_id,
            "content": content,
        }

        if tags is not None:
            update_kwargs["tags"] = tags

        status = self._client.update_post(**update_kwargs)

        if status != 200:
            raise RuntimeError(
                f"WordPress post update failed (HTTP {status})."
            )
