from socialflow.modules.posts.services.tag_provider import TagProvider
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.tag import Tag


class NullTagProvider(TagProvider):
    """Tag provider used when no external platform is connected."""

    def list_tags(self, account: Account) -> tuple[Tag, ...]:
        """Return no external tags."""
        return ()

    def create_tag(self, account: Account, tag: Tag) -> Tag:
        """Return the supplied tag without external persistence."""
        return tag