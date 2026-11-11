import ipaddress
from urllib.parse import urlsplit

from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.services.instagram_credential_keys import (
    InstagramCredentialKeys,
)
from socialflow.modules.posts.services.errors import (
    PublisherNotConfiguredError,
)
from socialflow.modules.instagram.services.instagram_image_url_provider import (
    InstagramImageUrlProvider,
)
from socialflow.modules.instagram.services.instagram_publishing_service import (
    InstagramPublishingService,
)
from socialflow.modules.posts.services.prepared_post import PreparedPost
from socialflow.modules.posts.services.publisher import Publisher


class InstagramPublisher(Publisher):
    """Publish prepared SocialFlow posts to an Instagram account."""


    def __init__(
        self,
        account: Account,
        credential_store: CredentialStore,
        publishing_service: InstagramPublishingService,
        image_url_provider: InstagramImageUrlProvider | None = None,
    ) -> None:
        if account.destination is not PublishingDestination.INSTAGRAM:
            raise ValueError("Instagram account is required.")

        self._account = account
        self._credential_store = credential_store
        self._publishing_service = publishing_service
        self._image_url_provider = image_url_provider


    def publish(self, post: PreparedPost) -> None:
        """Validate Instagram configuration, post input, and credentials."""
        config = self._account.instagram_config

        if config is None or not config.is_complete():
            raise PublisherNotConfiguredError(
                "Instagram account connection settings are incomplete."
            )

        if post.source.tags:
            raise ValueError(
                "Instagram tag publishing is not supported yet."
            )


        if len(post.source.images) != 1:
            raise ValueError(
                "Instagram publishing requires exactly one image."
            )

        if post.images:
            if len(post.images) != len(post.source.images):
                raise ValueError(
                    "Instagram prepared image count does not match source images."
                )

            for prepared, source in zip(
                post.images,
                post.source.images,
            ):
                if prepared.source != source:
                    raise ValueError(
                        "Instagram prepared image attachments are inconsistent."
                    )

                if (
                    prepared.destination
                    is not PublishingDestination.INSTAGRAM
                ):
                    raise ValueError(
                        "Prepared image is not intended for Instagram."
                    )

        token = self._credential_store.get(

            InstagramCredentialKeys.access_token(self._account)
        )


        if not token or not token.strip():
            raise ValueError(
                "Instagram access token is missing."
            )

        if self._image_url_provider is None:
            raise PublisherNotConfiguredError(
                "Instagram image URL provider is not configured."
            )

        image_path = (
            post.images[0].path
            if post.images
            else post.source.images[0].path
        )

        image_url = self._image_url_provider.get_public_url(
            image_path
        )

        if not isinstance(image_url, str) or not image_url.strip():
            raise ValueError(
                "Instagram image URL must be a public HTTPS URL."
            )

        if image_url != image_url.strip():
            raise ValueError(
                "Instagram image URL must be a public HTTPS URL."
            )

        try:
            parsed_url = urlsplit(image_url)
            hostname = parsed_url.hostname

            valid_url = (
                parsed_url.scheme == "https"
                and bool(hostname)
                and parsed_url.username is None
                and parsed_url.password is None
                and parsed_url.port in (None, 443)
                and not parsed_url.fragment
            )

            if valid_url and hostname:
                normalized_hostname = hostname.rstrip(".").lower()

                if (
                    normalized_hostname == "localhost"
                    or normalized_hostname.endswith(".localhost")
                ):
                    valid_url = False
                else:
                    try:
                        ip_address = ipaddress.ip_address(
                            normalized_hostname
                        )
                    except ValueError:
                        pass
                    else:
                        valid_url = ip_address.is_global

        except ValueError:
            valid_url = False

        if not valid_url:
            raise ValueError(
                "Instagram image URL must be a public HTTPS URL."
            )

        self._publishing_service.publish_image(
            instagram_user_id=config.instagram_user_id.strip(),
            access_token=token,
            image_url=image_url,
            caption=post.source.text,
        )
