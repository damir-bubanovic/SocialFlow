from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.application.tags.tag_provider import TagProvider
from socialflow.domain.account.account import Account
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)
from socialflow.infrastructure.wordpress.wordpress_tag_client import (
    WordPressTagClient,
)


class WordPressTagProvider(TagProvider):
    """Provide WordPress tags through SocialFlow's tag interface."""

    def __init__(
        self,
        tag_client: WordPressTagClient,
        credential_store: CredentialStore,
    ) -> None:
        self._tag_client = tag_client
        self._credential_store = credential_store

    def list_tags(self, account: Account) -> tuple[Tag, ...]:
        """Retrieve and convert tags for a WordPress account."""
        if account.destination != PublishingDestination.WORDPRESS:
            raise ValueError("A WordPress account is required.")

        config = account.wordpress_config

        if config is None or not config.is_complete():
            raise ValueError("WordPress connection settings are incomplete.")

        config = config.normalized()

        credential_key = WordPressCredentialKeys.application_password(
            account
        )
        application_password = self._credential_store.get(
            credential_key
        )

        if not application_password:
            raise ValueError("WordPress application password is missing.")

        wordpress_tags = self._tag_client.list_tags(
            site_url=config.site_url,
            username=config.username,
            application_password=application_password,
        )

        return tuple(
            Tag(name=wordpress_tag.name)
            for wordpress_tag in wordpress_tags
        )


    def create_tag(self, account: Account, tag: Tag) -> Tag:
        """Create and return a tag for a WordPress account."""
        if account.destination != PublishingDestination.WORDPRESS:
            raise ValueError("A WordPress account is required.")

        config = account.wordpress_config

        if config is None or not config.is_complete():
            raise ValueError("WordPress connection settings are incomplete.")

        config = config.normalized()

        credential_key = WordPressCredentialKeys.application_password(
            account
        )
        application_password = self._credential_store.get(
            credential_key
        )

        if not application_password:
            raise ValueError("WordPress application password is missing.")

        wordpress_tag = self._tag_client.create_tag(
            site_url=config.site_url,
            username=config.username,
            application_password=application_password,
            name=tag.name,
        )

        return Tag(name=wordpress_tag.name)
