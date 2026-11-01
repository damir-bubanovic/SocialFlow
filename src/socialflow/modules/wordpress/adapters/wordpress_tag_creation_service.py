
"""WordPress implementation of the remote tag creation workflow."""

from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.services.wordpress_credential_keys import (
    WordPressCredentialKeys,
)
from socialflow.modules.posts.models.remote_tag import RemoteTag
from socialflow.modules.posts.models.tag import Tag
from socialflow.modules.posts.services.remote_tag_creation_service import (
    RemoteTagCreationService,
)
from socialflow.modules.wordpress.adapters.wordpress_tag_resolver import (
    WordPressTagResolver,
)
from socialflow.modules.wordpress.api.wordpress_tag_client import (
    WordPressTagClient,
)
from socialflow.modules.wordpress.mappers.wordpress_tag_name_normalizer import (
    WordPressTagNameNormalizer,
)
from socialflow.modules.wordpress.models.wordpress_tag import WordPressTag


class WordPressTagCreationService(RemoteTagCreationService):
    """Prepare and create tags using the WordPress REST API."""

    def __init__(
        self,
        tag_client: WordPressTagClient,
        credential_store: CredentialStore,
    ) -> None:
        self._tag_client = tag_client
        self._credential_store = credential_store

    def _connection_details(
        self,
        account: Account,
    ) -> tuple[str, str, str]:
        if account.destination is not PublishingDestination.WORDPRESS:
            raise ValueError("A WordPress account is required.")

        config = account.wordpress_config

        if config is None or not config.is_complete():
            raise ValueError(
                "WordPress connection settings are incomplete."
            )

        config = config.normalized()

        password = self._credential_store.get(
            WordPressCredentialKeys.application_password(account)
        )

        if not password:
            raise ValueError(
                "WordPress application password is missing."
            )

        return config.site_url, config.username, password

    def prepare_creation(
        self,
        account: Account,
        selected_tags: tuple[Tag, ...],
    ) -> tuple[Tag, ...]:
        site_url, username, password = self._connection_details(account)

        remote_tags = self._tag_client.list_tags(
            site_url=site_url,
            username=username,
            application_password=password,
        )

        plan = WordPressTagResolver.prepare_creation_plan(
            selected_tags=selected_tags,
            remote_tags=remote_tags,
        )

        return plan.missing_tags

    def create_approved_tags(
        self,
        account: Account,
        approved_tags: tuple[Tag, ...],
    ) -> tuple[RemoteTag, ...]:
        site_url, username, password = self._connection_details(account)

        created_tags: list[RemoteTag] = []

        for tag in approved_tags:
            created_tag = self._tag_client.create_tag(
                site_url=site_url,
                username=username,
                application_password=password,
                name=tag.name,
            )

            if not isinstance(created_tag, WordPressTag):
                raise ValueError(
                    f"Invalid WordPress tag creation result for '{tag.name}'."
                )

            if (
                WordPressTagNameNormalizer.normalize(created_tag.name)
                != WordPressTagNameNormalizer.normalize(tag.name)
            ):
                raise ValueError(
                    f"Invalid WordPress tag creation result for '{tag.name}': "
                    f"received '{created_tag.name}'."
                )

            created_tags.append(
                RemoteTag(
                    remote_id=created_tag.id,
                    name=created_tag.name,
                )
            )

        return tuple(created_tags)
