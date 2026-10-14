
from socialflow.application.tags.tag_provider import TagProvider
from socialflow.domain.account.account import Account
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination


class RoutingTagProvider(TagProvider):
    """Route tag operations to destination-specific providers."""

    def __init__(
        self,
        providers: dict[PublishingDestination, TagProvider],
        fallback: TagProvider,
    ) -> None:
        self._providers = dict(providers)
        self._fallback = fallback

    def _provider_for(self, account: Account) -> TagProvider:
        return self._providers.get(
            account.destination,
            self._fallback,
        )

    def list_tags(self, account: Account) -> tuple[Tag, ...]:
        """Retrieve tags using the account's provider."""
        return self._provider_for(account).list_tags(account)

    def create_tag(self, account: Account, tag: Tag) -> Tag:
        """Create a tag using the account's provider."""
        return self._provider_for(account).create_tag(account, tag)
