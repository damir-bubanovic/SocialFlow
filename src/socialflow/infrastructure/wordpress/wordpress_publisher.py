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


logger = logging.getLogger(__name__)
class WordPressPublisher(Publisher):
    """Publish posts and images using a configured WordPress account."""

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

        if post.source.tags:
            raise ValueError("WordPress tags are not supported yet.")

        if post.source.images and not post.images:
            raise ValueError("WordPress images must be prepared before publishing.")

        if not post.source.text.strip():
            raise ValueError("WordPress post text is required.")

        password = self._credential_store.get(
            WordPressCredentialKeys.application_password(self._account)
        )

        if not password:
            raise ValueError("WordPress application password is missing.")

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
        )

        if status != 201:
            raise RuntimeError(
                f"WordPress publishing failed (HTTP {status})."
            )
