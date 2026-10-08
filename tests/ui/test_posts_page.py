from datetime import datetime
from uuid import UUID

from PySide6.QtWidgets import QWidget

from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.application.accounts.list_accounts import ListAccounts
from socialflow.application.publishing.errors import PublishingError
from socialflow.application.publishing.list_recent_publications import (
    ListRecentPublications,
)
from socialflow.application.publishing.publication_id_generator import (
    PublicationIdGenerator,
)
from socialflow.application.publishing.prepared_post import PreparedPost
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.application.publishing.publisher import Publisher
from socialflow.application.publishing.publisher_router import PublisherRouter
from socialflow.application.tags.create_tag import CreateTag
from socialflow.application.tags.list_tags import ListTags
from socialflow.application.tags.null_tag_provider import NullTagProvider
from socialflow.application.tags.tag_provider import TagProvider
from socialflow.application.time.clock import Clock
from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publication import Publication
from socialflow.domain.publishing.publication_id import PublicationId
from socialflow.infrastructure.publishing.in_memory_publication_repository import (
    InMemoryPublicationRepository,
)
from socialflow.ui.posts.post_editor import PostEditor
from socialflow.ui.posts.posts_page import PostsPage
from socialflow.ui.posts.publish_status import PublishStatus
from socialflow.domain.post.image_attachment import ImageAttachment


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


class PublishButtonStateRecordingPublisher(Publisher):
    """Publisher that records the publish button state during publishing."""

    def __init__(self) -> None:
        self.publish_button = None
        self.button_was_enabled_during_publish: bool | None = None

    def publish(self, post: PreparedPost) -> None:
        self.button_was_enabled_during_publish = (
            self.publish_button.isEnabled()
        )


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


class FixedClock(Clock):
    """Clock that always returns the same time."""

    def __init__(self, current_time: datetime) -> None:
        self._current_time = current_time

    def now(self) -> datetime:
        return self._current_time


class SequentialPublicationIdGenerator(PublicationIdGenerator):
    """Generate deterministic publication IDs for tests."""

    def __init__(self) -> None:
        self._next_value = 1

    def generate(self) -> PublicationId:
        publication_id = PublicationId(UUID(int=self._next_value))
        self._next_value += 1
        return publication_id


def create_publication_id_generator(
) -> SequentialPublicationIdGenerator:
    """Create a deterministic publication ID generator for tests."""
    return SequentialPublicationIdGenerator()


def create_tag_services() -> tuple[ListTags, CreateTag]:
    """Create tag services for PostsPage tests."""
    provider = NullTagProvider()

    return (
        ListTags(provider),
        CreateTag(provider),
    )


def create_list_recent_publications() -> ListRecentPublications:
    """Create an isolated recent-publications service."""
    return ListRecentPublications(
        InMemoryPublicationRepository()
    )


def create_posts_page() -> PostsPage:
    """Create a PostsPage with standard test dependencies."""
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

    list_tags, create_tag = create_tag_services()

    return PostsPage(
        publish_post=PublishPost(
            publisher_router=router,
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=create_list_recent_publications(),
    )


def create_publication(
    account: Account,
    text: str,
    published_at: datetime | None = None,
    publication_id: UUID | None = None,
) -> Publication:
    """Create a publication for PostsPage history tests."""
    return Publication(
        id=PublicationId(
            publication_id
            or UUID("12345678-1234-5678-1234-567812345678")
        ),
        account=account,
        post=Post(
            text=text,
            language=Language.ENGLISH,
        ),
        published_at=published_at
        or datetime(2026, 10, 6, 0, 0),
    )


# Basic structure


def test_posts_page_is_widget(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    assert isinstance(page, QWidget)


def test_posts_page_contains_post_editor(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    assert isinstance(page.post_editor, PostEditor)


def test_posts_page_contains_publish_status(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    assert isinstance(page.publish_status, PublishStatus)


def test_posts_page_loads_configured_accounts(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    assert len(page.post_editor.destination_selector._checkboxes) == 1
    assert (
        page.post_editor.destination_selector._checkboxes[0].text()
        == "Main Facebook (Facebook)"
    )


def test_posts_page_refreshes_configured_accounts(qtbot) -> None:
    repository = InMemoryAccountRepository()

    list_tags, create_tag = create_tag_services()

    page = PostsPage(
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=create_list_recent_publications(),
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


# Publishing


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
        publish_post=PublishPost(
            publisher_router=router,
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=create_list_recent_publications(),
    )
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText(
        "Hello from SocialFlow"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )
    page.post_editor.publish_button.click()

    assert len(publisher.published_posts) == 1
    assert (
        publisher.published_posts[0].source.text
        == "Hello from SocialFlow"
    )


def test_posts_page_shows_status_after_publish(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText(
        "Hello from SocialFlow"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )
    page.post_editor.publish_button.click()

    assert page.publish_status.text() == "Main Facebook — Published"
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
        publish_post=PublishPost(
            publisher_router=router,
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=create_list_recent_publications(),
    )
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText(
        "Hello from SocialFlow"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )
    page.post_editor.publish_button.click()

    assert page.publish_status.text() == "Main Facebook — Failed"
    assert page.publish_status.property("status") == "error"


def test_posts_page_shows_result_for_each_destination_when_one_fails(
    qtbot,
) -> None:
    repository = InMemoryAccountRepository()

    facebook_account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress_account = Account(
        name="Main Website",
        destination=PublishingDestination.WORDPRESS,
    )

    repository.add(facebook_account)
    repository.add(wordpress_account)

    facebook_publisher = FailingPublisher()
    wordpress_publisher = RecordingPublisher()

    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: facebook_publisher,
            PublishingDestination.WORDPRESS: wordpress_publisher,
        }
    )

    list_tags, create_tag = create_tag_services()

    page = PostsPage(
        publish_post=PublishPost(
            publisher_router=router,
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=create_list_recent_publications(),
    )
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText(
        "Hello from SocialFlow"
    )

    for checkbox in (
        page.post_editor.destination_selector._checkboxes
    ):
        checkbox.setChecked(True)

    page.post_editor.publish_button.click()

    assert page.publish_status.text() == (
        "Main Facebook — Failed\n"
        "Main Website — Published"
    )
    assert page.publish_status.property("status") == "error"
    assert len(wordpress_publisher.published_posts) == 1


# Publish button state


def test_posts_page_reenables_publish_button_after_publish(
    qtbot,
) -> None:
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

    list_tags, create_tag = create_tag_services()

    page = PostsPage(
        publish_post=PublishPost(
            publisher_router=router,
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=create_list_recent_publications(),
    )
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText(
        "Hello from SocialFlow"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )

    page.post_editor.publish_button.click()

    assert page.post_editor.publish_button.isEnabled()


def test_posts_page_reenables_publish_button_after_failure(
    qtbot,
) -> None:
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
        publish_post=PublishPost(
            publisher_router=router,
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=create_list_recent_publications(),
    )
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText(
        "Hello from SocialFlow"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )

    page.post_editor.publish_button.click()

    assert page.post_editor.publish_button.isEnabled()


def test_posts_page_disables_publish_button_during_publish(
    qtbot,
) -> None:
    repository = InMemoryAccountRepository()
    repository.add(
        Account(
            name="Main Facebook",
            destination=PublishingDestination.FACEBOOK,
        )
    )

    publisher = PublishButtonStateRecordingPublisher()
    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: publisher,
        }
    )

    list_tags, create_tag = create_tag_services()

    page = PostsPage(
        publish_post=PublishPost(
            publisher_router=router,
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=create_list_recent_publications(),
    )
    qtbot.addWidget(page)

    publisher.publish_button = page.post_editor.publish_button

    page.post_editor.text_editor.setPlainText(
        "Hello from SocialFlow"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )

    page.post_editor.publish_button.click()

    assert publisher.button_was_enabled_during_publish is False
    assert page.post_editor.publish_button.isEnabled()


# Tags


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
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(provider),
        create_tag=CreateTag(provider),
        list_recent_publications=create_list_recent_publications(),
    )
    qtbot.addWidget(page)

    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )

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
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(provider),
        create_tag=CreateTag(provider),
        list_recent_publications=create_list_recent_publications(),
    )
    qtbot.addWidget(page)

    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )
    page.post_editor.destination_selector._checkboxes[1].setChecked(
        True
    )

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
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(provider),
        create_tag=CreateTag(provider),
        list_recent_publications=create_list_recent_publications(),
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
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(provider),
        create_tag=CreateTag(provider),
        list_recent_publications=create_list_recent_publications(),
    )
    qtbot.addWidget(page)

    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )

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
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(provider),
        create_tag=CreateTag(provider),
        list_recent_publications=create_list_recent_publications(),
    )
    qtbot.addWidget(page)

    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )
    page.post_editor.destination_selector._checkboxes[1].setChecked(
        True
    )

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


# Recent publication history


def test_posts_page_shows_history_for_selected_account(qtbot) -> None:
    account_repository = InMemoryAccountRepository()
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    account_repository.add(account)

    publication_repository = InMemoryPublicationRepository()
    publication_repository.add(
        create_publication(
            account,
            "Previous publication",
        )
    )

    list_tags, create_tag = create_tag_services()

    page = PostsPage(
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(account_repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=ListRecentPublications(
            publication_repository
        ),
    )
    qtbot.addWidget(page)

    assert page.recent_posts_panel.recent_posts_list.count() == 0

    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )

    assert page.recent_posts_panel.recent_posts_list.count() == 1
    assert (
            page.recent_posts_panel.recent_posts_list.item(0).text()
            == (
                "06 Oct 2026 00:00 · Facebook\n"
                "Main Facebook — Previous publication"
            )
    )


def test_posts_page_clears_history_when_account_is_deselected(
    qtbot,
) -> None:
    account_repository = InMemoryAccountRepository()
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    account_repository.add(account)

    publication_repository = InMemoryPublicationRepository()
    publication_repository.add(
        create_publication(
            account,
            "Previous publication",
        )
    )

    list_tags, create_tag = create_tag_services()

    page = PostsPage(
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(account_repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=ListRecentPublications(
            publication_repository
        ),
    )
    qtbot.addWidget(page)

    checkbox = page.post_editor.destination_selector._checkboxes[0]

    checkbox.setChecked(True)

    assert page.recent_posts_panel.recent_posts_list.count() == 1

    checkbox.setChecked(False)

    assert page.recent_posts_panel.recent_posts_list.count() == 0


def test_posts_page_refreshes_history_after_successful_publish(
    qtbot,
) -> None:
    account_repository = InMemoryAccountRepository()
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    account_repository.add(account)

    publication_repository = InMemoryPublicationRepository()

    publisher = RecordingPublisher()
    router = PublisherRouter(
        {
            PublishingDestination.FACEBOOK: publisher,
        }
    )

    clock = FixedClock(
        datetime(2026, 10, 6, 0, 0)
    )

    publish_post = PublishPost(
        publisher_router=router,
        publication_id_generator=create_publication_id_generator(),
        publication_repository=publication_repository,
        clock=clock,
    )

    list_tags, create_tag = create_tag_services()

    page = PostsPage(
        publish_post=publish_post,
        list_accounts=ListAccounts(account_repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=ListRecentPublications(
            publication_repository
        ),
    )
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText(
        "New publication"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )

    assert page.recent_posts_panel.recent_posts_list.count() == 0

    page.post_editor.publish_button.click()

    assert page.recent_posts_panel.recent_posts_list.count() == 1
    assert (
            page.recent_posts_panel.recent_posts_list.item(0).text()
            == (
                "06 Oct 2026 00:00 · Facebook\n"
                "Main Facebook — New publication"
            )
    )


def test_posts_page_shows_history_for_first_selected_account(
    qtbot,
) -> None:
    account_repository = InMemoryAccountRepository()

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    account_repository.add(facebook)
    account_repository.add(wordpress)

    publication_repository = InMemoryPublicationRepository()

    publication_repository.add(
        create_publication(
            facebook,
            "Facebook history",
            datetime(2026, 10, 6, 0, 0),
        )
    )
    publication_repository.add(
        create_publication(
            wordpress,
            "WordPress history",
            datetime(2026, 10, 6, 0, 1),
        )
    )

    list_tags, create_tag = create_tag_services()

    page = PostsPage(
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(account_repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=ListRecentPublications(
            publication_repository
        ),
    )
    qtbot.addWidget(page)

    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )
    page.post_editor.destination_selector._checkboxes[1].setChecked(
        True
    )

def test_new_post_button_clears_editor(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText(
        "We are publishing important news today."
    )

    page.new_post_button.click()

    assert page.post_editor.post_text() == ""
    assert page.post_editor.selected_language() is Language.CROATIAN


def test_new_post_button_resets_editor_after_selecting_history(
    qtbot,
) -> None:
    account_repository = InMemoryAccountRepository()
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    account_repository.add(account)

    publication_repository = InMemoryPublicationRepository()
    publication_repository.add(
        create_publication(
            account,
            "Previous publication",
        )
    )

    list_tags, create_tag = create_tag_services()

    page = PostsPage(
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(account_repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=ListRecentPublications(
            publication_repository
        ),
    )
    qtbot.addWidget(page)

    checkbox = page.post_editor.destination_selector._checkboxes[0]
    checkbox.setChecked(True)

    history_list = page.recent_posts_panel.recent_posts_list
    assert history_list.count() == 1

    history_list.setCurrentRow(0)

    assert page.post_editor.post_text() == "Previous publication"
    assert page.post_editor.selected_language() is Language.ENGLISH

    page.new_post_button.click()

    assert page.post_editor.post_text() == ""
    assert page.post_editor.selected_language() is Language.CROATIAN
    assert page.post_editor.image_selector.selected_images() == ()
    assert page.post_editor.tag_selector.selected_tags() == ()
    assert page.post_editor.selected_accounts() == (account,)
    assert not page.post_editor.publish_button.isEnabled()

    page.post_editor.text_editor.setPlainText(
        "We are publishing important news today."
    )

    assert page.post_editor.selected_language() is Language.ENGLISH
