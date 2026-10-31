
from socialflow.application.categories.remote_category_provider import (
    RemoteCategoryProvider,
)
from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_category import RemoteCategory
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_category_client import (
    WordPressCategoryClient,
)
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)


class WordPressCategoryProvider(RemoteCategoryProvider):
    """Provide WordPress categories using saved account credentials."""

    def __init__(
        self,
        category_client: WordPressCategoryClient,
        credential_store: CredentialStore,
    ) -> None:
        self._category_client = category_client
        self._credential_store = credential_store

    def _connection(self, account: Account) -> tuple[str, str, str]:
        if account.destination != PublishingDestination.WORDPRESS:
            raise ValueError("A WordPress account is required.")

        config = account.wordpress_config

        if config is None or not config.is_complete():
            raise ValueError(
                "WordPress connection settings are incomplete."
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

        return (
            config.site_url,
            config.username,
            application_password,
        )

    def list_remote_categories(
        self,
        account: Account,
    ) -> tuple[RemoteCategory, ...]:
        """Retrieve categories with their IDs and parent relationships."""
        site_url, username, password = self._connection(account)

        wordpress_categories = self._category_client.list_categories(
            site_url=site_url,
            username=username,
            application_password=password,
        )

        return tuple(
            RemoteCategory(
                remote_id=category.id,
                name=category.name,
                parent_id=category.parent_id,
            )
            for category in wordpress_categories
        )

    def create_category(
        self,
        account: Account,
        name: str,
        parent_id: int = 0,
    ) -> RemoteCategory:
        """Create a category or subcategory on WordPress."""
        site_url, username, password = self._connection(account)

        wordpress_category = self._category_client.create_category(
            site_url=site_url,
            username=username,
            application_password=password,
            name=name,
            parent_id=parent_id,
        )

        return RemoteCategory(
            remote_id=wordpress_category.id,
            name=wordpress_category.name,
            parent_id=wordpress_category.parent_id,
        )
