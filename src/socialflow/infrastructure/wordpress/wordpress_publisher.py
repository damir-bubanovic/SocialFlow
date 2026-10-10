
from urllib.parse import urlsplit

from socialflow.application.credentials.credential_store import CredentialStore
from socialflow.application.publishing.prepared_post import PreparedPost
from socialflow.application.publishing.publisher import Publisher
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_credential_keys import WordPressCredentialKeys
from socialflow.infrastructure.wordpress.wordpress_post_client import WordPressPostClient


class WordPressPublisher(Publisher):
    """Publish text-only posts using a configured WordPress account."""

    def __init__(
        self,
        account: Account,
        credential_store: CredentialStore,
        post_client: WordPressPostClient,
    ) -> None:
        if account.destination is not PublishingDestination.WORDPRESS:
            raise ValueError("A WordPress account is required.")

        self._account = account
        self._credential_store = credential_store
        self._post_client = post_client

    def publish(self, post: PreparedPost) -> None:
        config = self._account.wordpress_config

        if config is None or not config.is_complete():
            raise ValueError("WordPress connection settings are incomplete.")

        config = config.normalized()
        parsed = urlsplit(config.site_url)

        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("A valid HTTPS WordPress site URL is required.")

        if post.source.images or post.images or post.source.tags:
            raise ValueError("WordPress images and tags are not supported yet.")

        if not post.source.text.strip():
            raise ValueError("WordPress post text is required.")

        password = self._credential_store.get(
            WordPressCredentialKeys.application_password(self._account)
        )

        if not password:
            raise ValueError("WordPress application password is missing.")

        status = self._post_client.create_post(
            site_url=config.site_url,
            username=config.username,
            application_password=password,
            content=post.source.text,
        )

        if status != 201:
            raise RuntimeError(
                f"WordPress publishing failed (HTTP {status})."
            )
