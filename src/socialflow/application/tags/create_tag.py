from socialflow.application.tags.tag_provider import TagProvider
from socialflow.domain.account.account import Account
from socialflow.domain.post.tag import Tag


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