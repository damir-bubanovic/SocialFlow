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
        """Publish a text-only post to the configured Facebook Page."""
        config = self._account.facebook_config

        if config is None or not config.is_complete():
            raise ValueError(
                "Facebook Page connection settings are incomplete."
            )

        config = config.normalized()

        if post.source.images or post.images:
            raise ValueError(
                "Facebook image publishing is not supported yet."
            )

        if post.source.tags:
            raise ValueError(
                "Facebook tag publishing is not supported yet."
            )

        if not post.source.text.strip():
            raise ValueError("Facebook post text is required.")

        token = self._credential_store.get(
            FacebookCredentialKeys.page_access_token(self._account)
        )

        if not token or not token.strip():
            raise ValueError("Facebook Page access token is missing.")

        self._publishing_service.publish_text(
            page_id=config.page_id,
            access_token=token,
            message=post.source.text,
        )
