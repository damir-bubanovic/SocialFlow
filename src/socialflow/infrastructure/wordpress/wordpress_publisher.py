import logging
from html import escape
from urllib.parse import urlsplit

from socialflow.application.credentials.credential_store import CredentialStore
from socialflow.application.publishing.prepared_post import PreparedPost
from socialflow.application.publishing.publisher import Publisher
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_credential_keys import WordPressCredentialKeys
from socialflow.infrastructure.wordpress.wordpress_post_client import WordPressPostClient
from socialflow.infrastructure.wordpress.wordpress_tag_client import (
    WordPressTagClient,
)
from socialflow.infrastructure.wordpress.wordpress_tag_resolver import (
    WordPressTagResolver,
)


logger = logging.getLogger(__name__)
class WordPressPublisher(Publisher):
    """Publish posts and images using a configured WordPress account."""

    def __init__(
        self,
        account: Account,
        credential_store: CredentialStore,
        post_client: WordPressPostClient,
        tag_client: WordPressTagClient | None = None,
        tag_resolver: WordPressTagResolver | None = None,
    ) -> None:
        if account.destination is not PublishingDestination.WORDPRESS:
            raise ValueError("A WordPress account is required.")

        self._account = account
        self._credential_store = credential_store
        self._post_client = post_client
        self._tag_client = tag_client
        self._tag_resolver = tag_resolver or WordPressTagResolver()

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

        if post.source.tags and self._tag_client is None:
            raise ValueError(
                "WordPress tag client is required when publishing tags."
            )

        if post.source.images and not post.images:
            raise ValueError("WordPress images must be prepared before publishing.")

        if not post.source.text.strip():
            raise ValueError("WordPress post text is required.")

        if not post.source.title.strip():
            raise ValueError("WordPress post title is required.")

        password = self._credential_store.get(
            WordPressCredentialKeys.application_password(self._account)
        )

        if not password:
            raise ValueError("WordPress application password is missing.")

        tag_ids: tuple[int, ...] = ()

        if post.source.tags:
            assert self._tag_client is not None

            remote_tags = self._tag_client.list_tags(
                site_url=config.site_url,
                username=config.username,
                application_password=password,
            )

            tag_ids = self._tag_resolver.resolve(
                selected_tags=post.source.tags,
                remote_tags=remote_tags,
            )
        content = post.source.text
        uploaded_media_ids: list[int] = []

        try:
            for image in post.images:
                media = self._post_client.upload_media(
                    site_url=config.site_url,
                    username=config.username,
                    application_password=password,
                    image_path=image.path,
                )

                uploaded_media_ids.append(media.media_id)

                escaped_url = escape(media.source_url, quote=True)

                content += (
                    f'\n\n<!-- wp:image {{"id":{media.media_id}}} -->'
                    f'\n<figure class="wp-block-image">'
                    f'<img src="{escaped_url}" '
                    f'class="wp-image-{media.media_id}" />'
                    f'\n</figure>'
                    f'\n<!-- /wp:image -->'
                )

        except Exception:
            for media_id in reversed(uploaded_media_ids):
                try:
                    self._post_client.delete_media(
                        site_url=config.site_url,
                        username=config.username,
                        application_password=password,
                        media_id=media_id,
                    )
                except (OSError, RuntimeError, ValueError):
                    logger.exception(
                        "Failed to delete WordPress media %s for account %s",
                        media_id,
                        self._account.id,
                    )

            raise

        status = self._post_client.create_post(
            site_url=config.site_url,
            username=config.username,
            application_password=password,
            content=content,
            tags=tag_ids,
            title=post.source.title.strip(),
        )

        if status != 201:
            raise RuntimeError(
                f"WordPress publishing failed (HTTP {status})."
            )
