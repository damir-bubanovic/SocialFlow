from socialflow.application.tags.create_tag import CreateTag
from socialflow.application.tags.list_tags import ListTags
from socialflow.application.tags.tag_provider import TagProvider
from socialflow.domain.account.account import Account
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination


class RecordingTagProvider(TagProvider):
    """Test provider that records tag operations."""

    def __init__(self) -> None:
        self.tags = (
            Tag(name="SocialFlow"),
            Tag(name="Python"),
        )
        self.created_account: Account | None = None
        self.created_tag: Tag | None = None

    def list_tags(self, account: Account) -> tuple[Tag, ...]:
        return self.tags

    def create_tag(
        self,
        account: Account,
        tag: Tag,
    ) -> Tag:
        self.created_account = account
        self.created_tag = tag

        return tag


def test_list_tags_returns_provider_tags() -> None:
    provider = RecordingTagProvider()
    service = ListTags(provider)

    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    result = service.execute(account)

    assert result == (
        Tag(name="SocialFlow"),
        Tag(name="Python"),
    )


def test_create_tag_creates_tag_for_account() -> None:
    provider = RecordingTagProvider()
    service = CreateTag(provider)

    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    result = service.execute(
        account=account,
        name="SocialFlow",
    )

    assert result == Tag(name="SocialFlow")
    assert provider.created_account is account
    assert provider.created_tag == Tag(name="SocialFlow")


def test_create_tag_normalizes_tag_name() -> None:
    provider = RecordingTagProvider()
    service = CreateTag(provider)

    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    result = service.execute(
        account=account,
        name="  SocialFlow  ",
    )

    assert result.name == "SocialFlow"
    assert provider.created_tag == Tag(name="SocialFlow")