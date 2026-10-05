from PySide6.QtWidgets import QWidget

from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.application.accounts.list_accounts import ListAccounts
from socialflow.application.publishing.errors import PublishingError
from socialflow.application.publishing.prepared_post import PreparedPost
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.application.publishing.publisher import Publisher
from socialflow.application.publishing.publisher_router import PublisherRouter
from socialflow.application.tags.create_tag import CreateTag
from socialflow.application.tags.list_tags import ListTags
from socialflow.application.tags.null_tag_provider import NullTagProvider
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.ui.posts.post_editor import PostEditor
from socialflow.ui.posts.posts_page import PostsPage
from socialflow.ui.posts.publish_status import PublishStatus
from socialflow.application.tags.tag_provider import TagProvider
from socialflow.domain.post.tag import Tag


class InMemoryAccountRepository(AccountRepository):
    """Test repository that stores accounts in memory."""

    def __init__(self) -> None:
        self._accounts: list[Account] = []

    def all(self) -> tuple[Account, ...]:
        return tuple(self._accounts)

    def add(self, account: Account) -> None:
        self._accounts.append(account)

    def remove(self, account: Account) -> None:
        self._accounts.remove(account)

    def update(self, current: Account, updated: Account) -> None:
        index = self._accounts.index(current)
        self._accounts[index] = updated


class RecordingPublisher(Publisher):
    """Test publisher that records published posts."""

    def __init__(self) -> None:
        self.published_posts: list[PreparedPost] = []

    def publish(self, post: PreparedPost) -> None:
        self.published_posts.append(post)


class FailingPublisher(Publisher):
    """Test publisher that always fails."""

    def publish(self, post: PreparedPost) -> None:
        raise PublishingError("Publishing failed.")

class AccountTagProvider(TagProvider):
    """Test provider that stores tags for specific accounts."""

    def __init__(
        self,
        tags_by_account: dict[Account, tuple[Tag, ...]],
    ) -> None:
        self._tags_by_account = dict(tags_by_account)
        self.created_tags: list[tuple[Account, Tag]] = []

    def list_tags(self, account: Account) -> tuple[Tag, ...]:
        return self._tags_by_account.get(account, ())

    def create_tag(
        self,
        account: Account,
        tag: Tag,
    ) -> Tag:
        self.created_tags.append((account, tag))

        current_tags = self._tags_by_account.get(account, ())

        if tag not in current_tags:
            self._tags_by_account[account] = (
                *current_tags,
                tag,
            )

        return tag

def create_tag_services() -> tuple[ListTags, CreateTag]:
    """Create tag services for PostsPage tests."""
    provider = NullTagProvider()

    return (
        ListTags(provider),
        CreateTag(provider),
    )


def create_posts_page() -> PostsPage:
    repository = InMemoryAccountRepository()
    repository.add(
        Account(
            name="Main Facebook",
            destination=PublishingDestination.FACEBOOK,
        )
    )

    publisher = RecordingPublisher()
    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: publisher,
        }
    )
    publish_post = PublishPost(router)

    list_tags, create_tag = create_tag_services()

    return PostsPage(
        publish_post=publish_post,
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
    )


def test_posts_page_is_widget(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    assert isinstance(page, QWidget)


def test_posts_page_contains_post_editor(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    assert isinstance(page.post_editor, PostEditor)


def test_posts_page_loads_configured_accounts(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    assert len(page.post_editor.destination_selector._checkboxes) == 1
    assert (
        page.post_editor.destination_selector._checkboxes[0].text()
        == "Main Facebook (Facebook)"
    )


def test_posts_page_delegates_publish_request(qtbot) -> None:
    repository = InMemoryAccountRepository()
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(account)

    publisher = RecordingPublisher()
    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: publisher,
        }
    )

    list_tags, create_tag = create_tag_services()

    page = PostsPage(
        publish_post=PublishPost(router),
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
    )
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText("Hello from SocialFlow")
    page.post_editor.destination_selector._checkboxes[0].setChecked(True)
    page.post_editor.publish_button.click()

    assert len(publisher.published_posts) == 1
    assert (
        publisher.published_posts[0].source.text
        == "Hello from SocialFlow"
    )


def test_posts_page_contains_publish_status(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    assert isinstance(page.publish_status, PublishStatus)


def test_posts_page_shows_status_after_publish(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText("Hello from SocialFlow")
    page.post_editor.destination_selector._checkboxes[0].setChecked(True)
    page.post_editor.publish_button.click()

    assert page.publish_status.text() == "Publish request completed."
    assert page.publish_status.property("status") == "success"


def test_posts_page_shows_error_when_publish_fails(qtbot) -> None:
    repository = InMemoryAccountRepository()
    repository.add(
        Account(
            name="Main Facebook",
            destination=PublishingDestination.FACEBOOK,
        )
    )

    publisher = FailingPublisher()
    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: publisher,
        }
    )

    list_tags, create_tag = create_tag_services()

    page = PostsPage(
        publish_post=PublishPost(router),
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
    )
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText("Hello from SocialFlow")
    page.post_editor.destination_selector._checkboxes[0].setChecked(True)
    page.post_editor.publish_button.click()

    assert page.publish_status.text() == "Publish request failed."
    assert page.publish_status.property("status") == "error"


def test_posts_page_refreshes_configured_accounts(qtbot) -> None:
    repository = InMemoryAccountRepository()

    list_tags, create_tag = create_tag_services()

    page = PostsPage(
        publish_post=PublishPost(PublisherRouter({})),
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
    )
    qtbot.addWidget(page)

    assert page.post_editor.selected_accounts() == ()
    assert len(page.post_editor.destination_selector._checkboxes) == 0

    repository.add(
        Account(
            name="Main WordPress",
            destination=PublishingDestination.WORDPRESS,
        )
    )

    page.refresh_accounts()

    assert len(page.post_editor.destination_selector._checkboxes) == 1
    assert (
        page.post_editor.destination_selector._checkboxes[0].text()
        == "Main WordPress (WordPress)"
    )

def test_posts_page_loads_tags_for_selected_account(qtbot) -> None:
    repository = InMemoryAccountRepository()

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(account)

    provider = AccountTagProvider(
        {
            account: (
                Tag(name="SocialFlow"),
                Tag(name="Python"),
            ),
        }
    )

    page = PostsPage(
        publish_post=PublishPost(PublisherRouter({})),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(provider),
        create_tag=CreateTag(provider),
    )
    qtbot.addWidget(page)

    page.post_editor.destination_selector._checkboxes[0].setChecked(True)

    assert page.post_editor.tag_selector.available_tags() == (
        Tag(name="SocialFlow"),
        Tag(name="Python"),
    )

def test_posts_page_combines_unique_tags_from_selected_accounts(
    qtbot,
) -> None:
    repository = InMemoryAccountRepository()

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    repository.add(facebook)
    repository.add(wordpress)

    provider = AccountTagProvider(
        {
            facebook: (
                Tag(name="SocialFlow"),
                Tag(name="Python"),
            ),
            wordpress: (
                Tag(name="Python"),
                Tag(name="WordPress"),
            ),
        }
    )

    page = PostsPage(
        publish_post=PublishPost(PublisherRouter({})),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(provider),
        create_tag=CreateTag(provider),
    )
    qtbot.addWidget(page)

    page.post_editor.destination_selector._checkboxes[0].setChecked(True)
    page.post_editor.destination_selector._checkboxes[1].setChecked(True)

    assert page.post_editor.tag_selector.available_tags() == (
        Tag(name="SocialFlow"),
        Tag(name="Python"),
        Tag(name="WordPress"),
    )

def test_posts_page_refreshes_tags_when_account_is_deselected(
    qtbot,
) -> None:
    repository = InMemoryAccountRepository()

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    repository.add(facebook)
    repository.add(wordpress)

    provider = AccountTagProvider(
        {
            facebook: (
                Tag(name="FacebookTag"),
            ),
            wordpress: (
                Tag(name="WordPressTag"),
            ),
        }
    )

    page = PostsPage(
        publish_post=PublishPost(PublisherRouter({})),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(provider),
        create_tag=CreateTag(provider),
    )
    qtbot.addWidget(page)

    facebook_checkbox = (
        page.post_editor.destination_selector._checkboxes[0]
    )
    wordpress_checkbox = (
        page.post_editor.destination_selector._checkboxes[1]
    )

    facebook_checkbox.setChecked(True)
    wordpress_checkbox.setChecked(True)

    assert page.post_editor.tag_selector.available_tags() == (
        Tag(name="FacebookTag"),
        Tag(name="WordPressTag"),
    )

    facebook_checkbox.setChecked(False)

    assert page.post_editor.tag_selector.available_tags() == (
        Tag(name="WordPressTag"),
    )

def test_posts_page_creates_new_tag_for_selected_account(
    qtbot,
) -> None:
    repository = InMemoryAccountRepository()

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(account)

    provider = AccountTagProvider({account: ()})

    page = PostsPage(
        publish_post=PublishPost(PublisherRouter({})),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(provider),
        create_tag=CreateTag(provider),
    )
    qtbot.addWidget(page)

    page.post_editor.destination_selector._checkboxes[0].setChecked(True)

    page.post_editor.tag_selector.tag_input.setText("SocialFlow")
    page.post_editor.tag_selector.add_button.click()

    assert provider.created_tags == [
        (
            account,
            Tag(name="SocialFlow"),
        ),
    ]

    assert page.post_editor.tag_selector.available_tags() == (
        Tag(name="SocialFlow"),
    )

def test_posts_page_creates_new_tag_for_all_selected_accounts(
    qtbot,
) -> None:
    repository = InMemoryAccountRepository()

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    repository.add(facebook)
    repository.add(wordpress)

    provider = AccountTagProvider(
        {
            facebook: (),
            wordpress: (),
        }
    )

    page = PostsPage(
        publish_post=PublishPost(PublisherRouter({})),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(provider),
        create_tag=CreateTag(provider),
    )
    qtbot.addWidget(page)

    page.post_editor.destination_selector._checkboxes[0].setChecked(True)
    page.post_editor.destination_selector._checkboxes[1].setChecked(True)

    page.post_editor.tag_selector.tag_input.setText("SocialFlow")
    page.post_editor.tag_selector.add_button.click()

    assert provider.created_tags == [
        (
            facebook,
            Tag(name="SocialFlow"),
        ),
        (
            wordpress,
            Tag(name="SocialFlow"),
        ),
    ]

    assert page.post_editor.tag_selector.available_tags() == (
        Tag(name="SocialFlow"),
    )