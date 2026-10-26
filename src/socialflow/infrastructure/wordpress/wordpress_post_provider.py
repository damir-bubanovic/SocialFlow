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
from socialflow.infrastructure.wordpress.wordpress_post_retriever import (
    WordPressPostRetriever,
)
from socialflow.application.publishing.remote_post_provider import (
    RemotePostProvider,
)
from socialflow.domain.post.remote_post import RemotePost


class WordPressPostProvider(RemotePostProvider):
    """Retrieve remote posts using a configured WordPress account."""

    def __init__(
        self,
        retriever: WordPressPostRetriever,
        credential_store: CredentialStore,
    ) -> None:
        self._retriever = retriever
        self._credential_store = credential_store

    def list_recent_posts(
            self,
            account: Account,
            limit: int = 5,
    ) -> tuple[RemotePost, ...]:
        """Retrieve recent posts for a WordPress account."""

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

        wordpress_posts = self._retriever.list_recent_posts(
            site_url=config.site_url,
            username=config.username,
            application_password=application_password,
            limit=limit,
        )

        return tuple(
            RemotePost(
                remote_id=str(post.id),
                destination=PublishingDestination.WORDPRESS,
                content=post.content,
                published_at=post.published_at,
                status=post.status,
                tag_ids=post.tag_ids,
                featured_media_id=post.featured_media_id,
                excerpt=post.excerpt,
            )
            for post in wordpress_posts
        )