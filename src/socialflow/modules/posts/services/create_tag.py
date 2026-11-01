from socialflow.modules.posts.services.tag_provider import TagProvider
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.tag import Tag


class CreateTag:
    """Application service for creating an account tag."""

    def __init__(self, tag_provider: TagProvider) -> None:
        self._tag_provider = tag_provider

    def execute(
        self,
        account: Account,
        name: str,
    ) -> Tag:
        """Create a tag for an account."""
        tag = Tag(name=name)

        return self._tag_provider.create_tag(
            account=account,
            tag=tag,
        )