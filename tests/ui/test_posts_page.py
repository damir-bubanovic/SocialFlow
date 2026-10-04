from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.application.accounts.list_accounts import ListAccounts
from socialflow.application.publishing.errors import PublishingError
from socialflow.application.publishing.publisher import Publisher
from socialflow.application.publishing.publisher_router import PublisherRouter
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.domain.account.account import Account
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.ui.posts.post_editor import PostEditor
from socialflow.ui.posts.posts_page import PostsPage
from socialflow.ui.posts.publish_status import PublishStatus
from PySide6.QtWidgets import QWidget


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
        self.published_posts: list[Post] = []

    def publish(self, post: Post) -> None:
        self.published_posts.append(post)


class FailingPublisher(Publisher):
    """Test publisher that always fails."""

    def publish(self, post: Post) -> None:
        raise PublishingError("Publishing failed.")


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

    return PostsPage(
        publish_post=publish_post,
        list_accounts=ListAccounts(repository),
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
    page = PostsPage(
        publish_post=PublishPost(router),
        list_accounts=ListAccounts(repository),
    )
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText("Hello from SocialFlow")
    page.post_editor.destination_selector._checkboxes[0].setChecked(True)
    page.post_editor.publish_button.click()

    assert len(publisher.published_posts) == 1
    assert publisher.published_posts[0].text == "Hello from SocialFlow"


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

    page = PostsPage(
        publish_post=PublishPost(router),
        list_accounts=ListAccounts(repository),
    )
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText("Hello from SocialFlow")
    page.post_editor.destination_selector._checkboxes[0].setChecked(True)
    page.post_editor.publish_button.click()

    assert page.publish_status.text() == "Publish request failed."
    assert page.publish_status.property("status") == "error"


def test_posts_page_refreshes_configured_accounts(qtbot) -> None:
    repository = InMemoryAccountRepository()

    page = PostsPage(
        publish_post=PublishPost(PublisherRouter({})),
        list_accounts=ListAccounts(repository),
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