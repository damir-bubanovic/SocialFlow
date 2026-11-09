from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.services.facebook_credential_keys import (
    FacebookCredentialKeys,
)
from socialflow.modules.facebook.api.facebook_publishing_service import (
    FacebookPublishingService,
)
from socialflow.modules.posts.services.prepared_post import PreparedPost
from socialflow.modules.posts.services.publisher import Publisher
from socialflow.modules.posts.services.errors import (
    PublisherNotConfiguredError,
)
from socialflow.modules.posts.models.image_attachment import (
    ImageAttachment,
)


class FacebookPublisher(Publisher):
    """Publish prepared SocialFlow posts to a Facebook Page."""

    def __init__(
        self,
        account: Account,
        credential_store: CredentialStore,
        publishing_service: FacebookPublishingService,
    ) -> None:
        if account.destination is not PublishingDestination.FACEBOOK:
            raise ValueError("A Facebook account is required.")

        self._account = account
        self._credential_store = credential_store
        self._publishing_service = publishing_service


    def publish(self, post: PreparedPost) -> None:
        """Publish a text post or a single photo to a Facebook Page."""
        config = self._account.facebook_config

        if config is None or not config.is_complete():
            raise PublisherNotConfiguredError(
                "Facebook Page connection settings are incomplete."
            )

        config = config.normalized()

        if post.source.tags:
            raise ValueError(
                "Facebook tag publishing is not supported yet."
            )


        attachments: tuple[ImageAttachment, ...]

        if post.images:
            if len(post.images) != len(post.source.images):
                raise ValueError(
                    "Facebook prepared image count does not match source images."
                )

            for prepared, source in zip(
                post.images,
                post.source.images,
            ):
                if prepared.source != source:
                    raise ValueError(
                        "Facebook image attachments are inconsistent."
                    )

                if (
                    prepared.destination
                    is not PublishingDestination.FACEBOOK
                ):
                    raise ValueError(
                        "Prepared image is not intended for Facebook."
                    )

            attachments = tuple(
                ImageAttachment(path=prepared.path)
                for prepared in post.images
            )
        else:
            attachments = post.source.images

        if not attachments and not post.source.text.strip():
            raise ValueError("Facebook post text is required.")

        if len(attachments) > 10:
            raise ValueError(
                "Facebook multiple-photo publishing requires 2 to 10 images."
            )

        token = self._credential_store.get(
            FacebookCredentialKeys.page_access_token(self._account)
        )

        if not token or not token.strip():
            raise ValueError("Facebook Page access token is missing.")

        if len(attachments) > 1:
            self._publishing_service.publish_multiple_photos(
                page_id=config.page_id,
                access_token=token,
                attachments=attachments,
                message=post.source.text,
            )
            return

        if attachments:
            self._publishing_service.publish_photo(
                page_id=config.page_id,
                access_token=token,
                attachment=attachments[0],
                caption=post.source.text,
            )
            return

        self._publishing_service.publish_text(
            page_id=config.page_id,
            access_token=token,
            message=post.source.text,
        )
