from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.application.publishing.remote_media_provider import (
    RemoteMediaProvider,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_media import RemoteMedia
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)
from socialflow.infrastructure.wordpress.wordpress_post_client import (
    WordPressPostClient,
)


class WordPressMediaProvider(RemoteMediaProvider):
    """Retrieve WordPress Media Library images for an account."""

    def __init__(
        self,
        client: WordPressPostClient,
        credential_store: CredentialStore,
    ) -> None:
        self._client = client
        self._credential_store = credential_store

    def list_media(
        self,
        account: Account,
        limit: int = 50,
    ) -> tuple[RemoteMedia, ...]:
        """Retrieve and convert recent WordPress image records."""
        if account.destination != PublishingDestination.WORDPRESS:
            raise ValueError("A WordPress account is required.")

        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Media limit must be between 1 and 100.")

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

        records = self._client.list_media(
            site_url=config.site_url,
            username=config.username,
            application_password=application_password,
            limit=limit,
        )

        if not isinstance(records, list):
            raise ValueError("Invalid WordPress media response.")

        return tuple(
            self._convert_record(record)
            for record in records
        )

    @staticmethod
    def _convert_record(record: dict) -> RemoteMedia:
        """Convert one WordPress media record to a domain object."""
        if not isinstance(record, dict):
            raise ValueError("Invalid WordPress media record.")

        media_id = record.get("id")
        source_url = record.get("source_url")
        title_data = record.get("title", {})
        media_details = record.get("media_details", {})

        if type(media_id) is not int or media_id <= 0:
            raise ValueError("Invalid WordPress media ID.")

        if not isinstance(source_url, str):
            raise ValueError("Invalid WordPress media source URL.")

        if not isinstance(title_data, dict):
            raise ValueError("Invalid WordPress media title.")

        title = title_data.get("rendered", "")

        if not isinstance(title, str):
            raise ValueError("Invalid WordPress media title.")

        if not isinstance(media_details, dict):
            raise ValueError("Invalid WordPress media details.")

        thumbnail_url = None
        sizes = media_details.get("sizes", {})

        if not isinstance(sizes, dict):
            raise ValueError("Invalid WordPress media sizes.")

        thumbnail = sizes.get("thumbnail")

        if thumbnail is not None:
            if not isinstance(thumbnail, dict):
                raise ValueError("Invalid WordPress thumbnail.")

            thumbnail_url = thumbnail.get("source_url")

            if not isinstance(thumbnail_url, str):
                raise ValueError("Invalid WordPress thumbnail URL.")

        return RemoteMedia(
            remote_id=media_id,
            destination=PublishingDestination.WORDPRESS,
            source_url=source_url,
            title=title,
            thumbnail_url=thumbnail_url,
        )