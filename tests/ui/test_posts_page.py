from datetime import datetime
from uuid import UUID
from PySide6.QtWidgets import QCheckBox

from PySide6.QtWidgets import QWidget

from socialflow.domain.post.remote_media import RemoteMedia
from socialflow.domain.post.image_attachment import ImageAttachment
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
from threading import Event
from socialflow.application.publishing.publish_result import PublishResult
from socialflow.domain.publishing.publish_request import PublishRequest
from unittest.mock import Mock
from socialflow.domain.post.remote_post import RemotePost
from socialflow.application.tags.list_remote_tags import ListRemoteTags
from socialflow.domain.post.remote_tag import RemoteTag
from socialflow.ui.posts.remote_media_selection_dialog import (
    RemoteMediaSelectionDialog,
)


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
    """Publisher that pauses until the test releases it."""

    def __init__(self) -> None:
        self.started = Event()
        self.release = Event()
        self.publish_count = 0

    def publish(self, post: PreparedPost) -> None:
        self.publish_count += 1
        self.started.set()
        if not self.release.wait(timeout=5):
            raise PublishingError("Test publisher timed out.")


class FailingPublisher(Publisher):
    """Test publisher that always fails."""

    def __init__(self) -> None:
        self.publish_count = 0

    def publish(self, post: PreparedPost) -> None:
        self.publish_count += 1
        raise PublishingError("Publishing failed.")

class FailOncePublisher(Publisher):
    """Fail on the first attempt and succeed on subsequent attempts."""

    def __init__(self) -> None:
        self.publish_count = 0

    def publish(self, post: PreparedPost) -> None:
        self.publish_count += 1

        if self.publish_count == 1:
            raise PublishingError("Temporary publishing failure.")


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
    with qtbot.waitSignal(
            page.publishing_finished,
            timeout=5000,
    ):
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
    with qtbot.waitSignal(
            page.publishing_finished,
            timeout=5000,
    ):
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
    with qtbot.waitSignal(
            page.publishing_finished,
            timeout=5000,
    ):
        page.post_editor.publish_button.click()

    assert page.publish_status.text() == (
        "Main Facebook — Failed: Publishing failed. Please check the details."
    )
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
    page.post_editor.title_editor.setText(
        "WordPress Test Title"
    )

    for checkbox in (
            page.post_editor.destination_selector._checkboxes
    ):
        checkbox.setChecked(True)

    with qtbot.waitSignal(
            page.publishing_finished,
            timeout=5000,
    ):
        page.post_editor.publish_button.click()

    assert page.publish_status.text() == (
        "Main Facebook — Failed: Publishing failed. Please check the details.\n"
        "Main Website — Published"
    )
    assert page.publish_status.property("status") == "error"
    assert len(wordpress_publisher.published_posts) == 1


def test_posts_page_updates_progress_for_each_account(qtbot) -> None:
    """Display per-account progress and final publishing results."""
    repository = InMemoryAccountRepository()

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress = Account(
        name="Main Website",
        destination=PublishingDestination.WORDPRESS,
    )

    repository.add(facebook)
    repository.add(wordpress)

    facebook_publisher = RecordingPublisher()
    wordpress_publisher = FailingPublisher()

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
        "Publishing progress test"
    )
    page.post_editor.title_editor.setText(
        "WordPress Test Title"
    )

    for checkbox in page.post_editor.destination_selector._checkboxes:
        checkbox.setChecked(True)

    progress_messages = []

    def record_progress(_result) -> None:
        progress_messages.append(page.publish_status.text())

    page._publishing_controller.progress.connect(record_progress)

    with qtbot.waitSignal(page.publishing_finished, timeout=5000):
        page.post_editor.publish_button.click()

        assert page.publish_status.text() == (
            "Publishing 0 of 2 accounts..."
        )
        assert not page.post_editor.publish_button.isEnabled()

    assert progress_messages == [
        "Publishing 1 of 2 accounts...\n"
        "Main Facebook — Published",
        "Publishing 2 of 2 accounts...\n"
        "Main Website — Failed",
    ]

    assert page.publish_status.text() == (
        "Main Facebook — Published\n"
        "Main Website — Failed: Publishing failed. Please check the details."
    )
    assert page.publish_status.property("status") == "error"
    assert page.post_editor.publish_button.isEnabled()


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

    with qtbot.waitSignal(
            page.publishing_finished,
            timeout=5000,
    ):
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

    with qtbot.waitSignal(
            page.publishing_finished,
            timeout=5000,
    ):
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

    page.post_editor.text_editor.setPlainText(
        "Hello from SocialFlow"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )

    try:
        with qtbot.waitSignal(
            page.publishing_finished,
            timeout=5000,
        ):
            page.post_editor.publish_button.click()

            assert publisher.started.wait(timeout=2)
            assert page.publishing_is_running
            assert not page.post_editor.publish_button.isEnabled()

            publisher.release.set()
    finally:
        publisher.release.set()
        page.shutdown()

    assert not page.publishing_is_running
    assert page.post_editor.publish_button.isEnabled()

def test_posts_page_prevents_duplicate_publish_clicks(qtbot) -> None:
    """Repeated clicks must not start another publishing operation."""
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

    page.post_editor.text_editor.setPlainText(
        "Duplicate publishing protection test"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )

    try:
        with qtbot.waitSignal(page.publishing_finished, timeout=5000):
            page.post_editor.publish_button.click()

            assert publisher.started.wait(timeout=2)
            assert page.publishing_is_running
            assert not page.post_editor.publish_button.isEnabled()

            page.post_editor.publish_button.click()
            page.post_editor.publish_button.click()

            assert page.publishing_is_running

            publisher.release.set()
    finally:
        publisher.release.set()
        page.shutdown()

    assert not page.publishing_is_running
    assert page.post_editor.publish_button.isEnabled()
    assert publisher.publish_count == 1

def test_posts_page_allows_retry_after_failed_publish(qtbot) -> None:
    """A failed publication must not block another attempt."""
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
        "Publishing retry test"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )

    for attempt in range(2):
        with qtbot.waitSignal(
            page.publishing_finished,
            timeout=5000,
        ):
            page.post_editor.publish_button.click()

        assert page.publish_status.text() == (
            "Main Facebook — Failed: Publishing failed. Please check the details."
        )
        assert page.publish_status.property("status") == "error"
        assert page.post_editor.publish_button.isEnabled()
        assert not page.publishing_is_running

    assert publisher.publish_count == 2

def test_posts_page_stores_original_request_and_results(qtbot) -> None:
    """Preserve publishing state for a subsequent selective retry."""
    repository = InMemoryAccountRepository()

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress = Account(
        name="Main Website",
        destination=PublishingDestination.WORDPRESS,
    )

    repository.add(facebook)
    repository.add(wordpress)

    facebook_publisher = RecordingPublisher()
    wordpress_publisher = FailingPublisher()

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
        "Selective retry state test"
    )
    page.post_editor.title_editor.setText(
        "WordPress Test Title"
    )

    for checkbox in page.post_editor.destination_selector._checkboxes:
        checkbox.setChecked(True)

    with qtbot.waitSignal(page.publishing_finished, timeout=5000):
        page.post_editor.publish_button.click()

    request = page._last_publish_request
    results = page._last_publish_results

    assert request is not None
    assert request.post.text == "Selective retry state test"
    assert request.accounts == (facebook, wordpress)

    assert len(results) == 2
    assert results[0].account == facebook
    assert results[0].succeeded

    assert results[1].account == wordpress
    assert not results[1].succeeded

    assert len(facebook_publisher.published_posts) == 1
    assert wordpress_publisher.publish_count == 1

def test_posts_page_builds_retry_for_failed_accounts(qtbot) -> None:
    """Only failed accounts should appear in the retry request."""
    page = create_posts_page()
    qtbot.addWidget(page)

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress = Account(
        name="Main Website",
        destination=PublishingDestination.WORDPRESS,
    )

    original_request = PublishRequest(
        post=Post(
            text="Selective retry test",
            language=Language.ENGLISH,
        ),
        accounts=(facebook, wordpress),
    )

    page._last_publish_request = original_request
    page._last_publish_results = (
        PublishResult(account=facebook, succeeded=True),
        PublishResult(
            account=wordpress,
            succeeded=False,
            error=PublishingError("WordPress publishing failed."),
        ),
    )

    retry_request = page._build_failed_retry_request()

    assert retry_request is not None
    assert retry_request.post is original_request.post
    assert retry_request.accounts == (wordpress,)

def test_retry_failed_button_is_initially_disabled(qtbot) -> None:
    """Retry must be unavailable before publishing."""
    page = create_posts_page()
    qtbot.addWidget(page)

    assert not page.retry_failed_button.isEnabled()

def test_retry_remains_disabled_when_all_accounts_succeed(qtbot) -> None:
    """Successful publishing must not create a retry request."""
    page = create_posts_page()
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText(
        "Successful publication without retry"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )

    with qtbot.waitSignal(page.publishing_finished, timeout=5000):
        page.post_editor.publish_button.click()

    assert len(page._last_publish_results) == 1
    assert page._last_publish_results[0].succeeded

    assert page._build_failed_retry_request() is None
    assert not page.retry_failed_button.isEnabled()
    assert not page.publishing_is_running

def test_retry_is_blocked_while_publishing_is_running(qtbot) -> None:
    """Retry must not start another operation during active publishing."""
    repository = InMemoryAccountRepository()

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(account)

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

    page.post_editor.text_editor.setPlainText(
        "Retry concurrency protection test"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )

    try:
        with qtbot.waitSignal(page.publishing_finished, timeout=5000):
            page.post_editor.publish_button.click()

            assert publisher.started.wait(timeout=2)
            assert page.publishing_is_running
            assert not page.retry_failed_button.isEnabled()

            # Invoke the retry handler directly to verify its guard.
            page._retry_failed_publications()

            assert publisher.publish_count == 1
            assert page.publishing_is_running

            publisher.release.set()
    finally:
        publisher.release.set()
        page.shutdown()

    assert publisher.publish_count == 1
    assert not page.publishing_is_running
    assert not page.retry_failed_button.isEnabled()

def test_retry_failed_publishes_only_failed_accounts(qtbot) -> None:
    """Retry must not republish accounts that already succeeded."""
    repository = InMemoryAccountRepository()

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress = Account(
        name="Main Website",
        destination=PublishingDestination.WORDPRESS,
    )

    repository.add(facebook)
    repository.add(wordpress)

    facebook_publisher = RecordingPublisher()
    wordpress_publisher = FailingPublisher()

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
        "Selective retry integration test"
    )
    page.post_editor.title_editor.setText(
        "WordPress Test Title"
    )

    for checkbox in page.post_editor.destination_selector._checkboxes:
        checkbox.setChecked(True)

    # First attempt: Facebook succeeds, WordPress fails.
    with qtbot.waitSignal(page.publishing_finished, timeout=5000):
        page.post_editor.publish_button.click()

    assert len(facebook_publisher.published_posts) == 1
    assert wordpress_publisher.publish_count == 1
    assert page.retry_failed_button.isEnabled()

    # Second attempt: retry only WordPress.
    with qtbot.waitSignal(page.publishing_finished, timeout=5000):
        page.retry_failed_button.click()

    assert len(facebook_publisher.published_posts) == 1
    assert wordpress_publisher.publish_count == 2

    assert page._last_publish_request is not None
    assert page._last_publish_request.accounts == (wordpress,)

    assert page.retry_failed_button.isEnabled()
    assert not page.publishing_is_running

def test_retry_success_disables_retry_button(qtbot) -> None:
    """A successful retry must not leave failed accounts to retry."""
    repository = InMemoryAccountRepository()

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(account)

    publisher = FailOncePublisher()

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
        "Retry recovery test"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )

    # First attempt fails.
    with qtbot.waitSignal(page.publishing_finished, timeout=5000):
        page.post_editor.publish_button.click()

    assert publisher.publish_count == 1
    assert page.retry_failed_button.isEnabled()
    assert not page._last_publish_results[0].succeeded

    # Retry succeeds.
    with qtbot.waitSignal(page.publishing_finished, timeout=5000):
        page.retry_failed_button.click()

    assert publisher.publish_count == 2
    assert page._last_publish_results[0].succeeded
    assert not page.retry_failed_button.isEnabled()
    assert page._build_failed_retry_request() is None
    assert not page.publishing_is_running

def test_selective_retry_recovers_failed_account_without_republishing_successful_account(
    qtbot,
) -> None:
    """Retry only the failed account and finish with no remaining failures."""
    repository = InMemoryAccountRepository()

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress = Account(
        name="Main Website",
        destination=PublishingDestination.WORDPRESS,
    )

    repository.add(facebook)
    repository.add(wordpress)

    facebook_publisher = RecordingPublisher()
    wordpress_publisher = FailOncePublisher()

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
        "Multi-account retry recovery test"
    )
    page.post_editor.title_editor.setText(
        "WordPress Test Title"
    )

    for checkbox in page.post_editor.destination_selector._checkboxes:
        checkbox.setChecked(True)

    # First attempt: Facebook succeeds, WordPress fails.
    with qtbot.waitSignal(page.publishing_finished, timeout=5000):
        page.post_editor.publish_button.click()

    assert len(facebook_publisher.published_posts) == 1
    assert wordpress_publisher.publish_count == 1

    assert len(page._last_publish_results) == 2
    assert page._last_publish_results[0].account == facebook
    assert page._last_publish_results[0].succeeded
    assert page._last_publish_results[1].account == wordpress
    assert not page._last_publish_results[1].succeeded

    assert page.retry_failed_button.isEnabled()

    retry_request = page._build_failed_retry_request()
    assert retry_request is not None
    assert retry_request.accounts == (wordpress,)

    # Second attempt: only WordPress is retried and succeeds.
    with qtbot.waitSignal(page.publishing_finished, timeout=5000):
        page.retry_failed_button.click()

    assert len(facebook_publisher.published_posts) == 1
    assert wordpress_publisher.publish_count == 2

    assert page._last_publish_request is not None
    assert page._last_publish_request.accounts == (wordpress,)

    assert len(page._last_publish_results) == 1
    assert page._last_publish_results[0].account == wordpress
    assert page._last_publish_results[0].succeeded

    assert page._build_failed_retry_request() is None
    assert not page.retry_failed_button.isEnabled()
    assert not page.publishing_is_running
    assert page.post_editor.publish_button.isEnabled()

def test_editing_post_text_invalidates_retry(qtbot) -> None:
    """Editing the draft must discard the previous retry request."""
    page = create_posts_page()
    qtbot.addWidget(page)

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    page._last_publish_request = PublishRequest(
        post=Post(
            text="Original text",
            language=Language.ENGLISH,
        ),
        accounts=(account,),
    )
    page._last_publish_results = (
        PublishResult(
            account=account,
            succeeded=False,
            error=PublishingError("Publishing failed."),
        ),
    )
    page.retry_failed_button.setEnabled(True)

    page.post_editor.text_editor.setPlainText("Edited text")

    assert page._last_publish_request is None
    assert page._last_publish_results == ()
    assert not page.retry_failed_button.isEnabled()

def test_changing_wordpress_title_invalidates_retry(qtbot) -> None:
    """Editing the WordPress title must discard previous retry state."""
    page = create_posts_page()
    qtbot.addWidget(page)

    account = Account(
        name="Main Website",
        destination=PublishingDestination.WORDPRESS,
    )

    page._last_publish_request = PublishRequest(
        post=Post(
            text="Original text",
            language=Language.ENGLISH,
            title="Original WordPress Title",
        ),
        accounts=(account,),
    )
    page._last_publish_results = (
        PublishResult(
            account=account,
            succeeded=False,
            error=PublishingError("Publishing failed."),
        ),
    )
    page.retry_failed_button.setEnabled(True)

    page.post_editor.title_editor.setText(
        "Updated WordPress Title"
    )

    assert page._last_publish_request is None
    assert page._last_publish_results == ()
    assert not page.retry_failed_button.isEnabled()

def test_changing_post_language_invalidates_retry(qtbot) -> None:
    """Changing the selected language must discard retry state."""
    page = create_posts_page()
    qtbot.addWidget(page)

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    page._last_publish_request = PublishRequest(
        post=Post(
            text="Original text",
            language=Language.ENGLISH,
        ),
        accounts=(account,),
    )
    page._last_publish_results = (
        PublishResult(
            account=account,
            succeeded=False,
            error=PublishingError("Publishing failed."),
        ),
    )
    page.retry_failed_button.setEnabled(True)

    selector = page.post_editor.language_controls.selector
    original_index = selector.currentIndex()

    new_index = next(
        index
        for index in range(selector.count())
        if index != original_index
    )
    selector.setCurrentIndex(new_index)

    assert page._last_publish_request is None
    assert page._last_publish_results == ()
    assert not page.retry_failed_button.isEnabled()

def test_changing_post_images_invalidates_retry(qtbot, tmp_path) -> None:
    """Changing image attachments must discard retry state."""
    page = create_posts_page()
    qtbot.addWidget(page)

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    page._last_publish_request = PublishRequest(
        post=Post(
            text="Original text",
            language=Language.ENGLISH,
        ),
        accounts=(account,),
    )
    page._last_publish_results = (
        PublishResult(
            account=account,
            succeeded=False,
            error=PublishingError("Publishing failed."),
        ),
    )
    page.retry_failed_button.setEnabled(True)

    image_path = tmp_path / "example.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    page.post_editor.image_selector.set_selected_images(
        (
            ImageAttachment(path=image_path),
        )
    )

    assert page._last_publish_request is None
    assert page._last_publish_results == ()
    assert not page.retry_failed_button.isEnabled()

def test_changing_post_tags_invalidates_retry(qtbot) -> None:
    """Changing selected tags must discard retry state."""
    page = create_posts_page()
    qtbot.addWidget(page)

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    page._last_publish_request = PublishRequest(
        post=Post(
            text="Original text",
            language=Language.ENGLISH,
        ),
        accounts=(account,),
    )
    page._last_publish_results = (
        PublishResult(
            account=account,
            succeeded=False,
            error=PublishingError("Publishing failed."),
        ),
    )
    page.retry_failed_button.setEnabled(True)

    page.post_editor.tag_selector.set_selected_tags(
        (Tag(name="SocialFlow"),)
    )

    assert page.post_editor.tag_selector.selected_tags() == (
        Tag(name="SocialFlow"),
    )
    assert page._last_publish_request is None
    assert page._last_publish_results == ()
    assert not page.retry_failed_button.isEnabled()


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

    qtbot.waitUntil(
        lambda: page.post_editor.tag_selector.available_tags()
                == (
                    Tag(name="SocialFlow"),
                    Tag(name="Python"),
                    Tag(name="WordPress"),
                ),
        timeout=5000,
    )
    qtbot.waitUntil(
        lambda: not page._tag_loading_controller.is_running,
        timeout=5000,
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

    qtbot.waitUntil(
        lambda: page.post_editor.tag_selector.available_tags()
                == (
                    Tag(name="FacebookTag"),
                    Tag(name="WordPressTag"),
                ),
        timeout=5000,
    )
    qtbot.waitUntil(
        lambda: not page._tag_loading_controller.is_running,
        timeout=5000,
    )

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

    qtbot.waitUntil(
        lambda: page.post_editor.tag_selector.available_tags()
                == (Tag(name="SocialFlow"),),
        timeout=5000,
    )

    qtbot.waitUntil(
        lambda: not page._tag_loading_controller.is_running,
        timeout=5000,
    )

    assert page.post_editor.tag_selector.available_tags() == (
        Tag(name="SocialFlow"),
    )

    page.shutdown()


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

    with qtbot.waitSignal(
            page.publishing_finished,
            timeout=5000,
    ):
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

    qtbot.waitUntil(
        lambda: not page._tag_loading_controller.is_running,
        timeout=5000,
    )

    page.shutdown()

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

def test_posts_page_ignores_tags_without_active_loading_account(
    qtbot,
) -> None:
    """Ignore background results when no account owns the request."""
    page = create_posts_page()
    qtbot.addWidget(page)

    page.post_editor.destination_selector._checkboxes[0].setChecked(
        True
    )

    assert page._tag_loading_account is None

    page._tag_loading_controller.tags_ready.emit(
        (Tag(name="Unexpected"),)
    )

    assert page.post_editor.tag_selector.available_tags() == ()


def test_posts_page_ignores_tags_after_account_deselection(
    qtbot,
) -> None:
    """Do not display results for an account that was deselected."""
    page = create_posts_page()
    qtbot.addWidget(page)

    checkbox = page.post_editor.destination_selector._checkboxes[0]
    checkbox.setChecked(True)

    account = page.post_editor.selected_accounts()[0]
    page._tag_loading_account = account

    checkbox.setChecked(False)

    page._tag_loading_controller.tags_ready.emit(
        (Tag(name="StaleTag"),)
    )

    assert page.post_editor.tag_selector.available_tags() == ()

def test_posts_page_loads_queued_wordpress_tags_in_background(
    qtbot,
) -> None:
    repository = InMemoryAccountRepository()
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    repository.add(account)

    expected_tags = (
        Tag(name="Python"),
        Tag(name="WordPress"),
    )
    provider = AccountTagProvider({account: expected_tags})

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

    with qtbot.waitSignal(
            page._tag_loading_controller.finished,
            timeout=5000,
    ):
        page.post_editor.destination_selector._checkboxes[0].setChecked(
            True
        )

    assert page.post_editor.tag_selector.available_tags() == expected_tags
    assert page._pending_tag_accounts == []
    assert not page._tag_loading_controller.is_running

    page.shutdown()

def test_posts_page_starts_wordpress_tag_loading_automatically(
    qtbot,
) -> None:
    """Selecting WordPress must start background tag loading."""
    repository = InMemoryAccountRepository()
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    repository.add(account)

    expected_tags = (
        Tag(name="Python"),
        Tag(name="WordPress"),
    )
    provider = AccountTagProvider({account: expected_tags})

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

    try:
        with qtbot.waitSignal(
            page._tag_loading_controller.finished,
            timeout=5000,
        ):
            page.post_editor.destination_selector._checkboxes[0].setChecked(
                True
            )

        assert page.post_editor.tag_selector.available_tags() == expected_tags
        assert not page._tag_loading_controller.is_running
    finally:
        page.shutdown()

def test_posts_page_shutdown_prevents_queued_tag_loading(qtbot) -> None:
    """Shutdown must clear pending requests and prevent new workers."""
    page = create_posts_page()
    qtbot.addWidget(page)

    page.post_editor.destination_selector._checkboxes[0].setChecked(True)
    account = page.post_editor.selected_accounts()[0]
    page._pending_tag_accounts.append(account)

    assert page._pending_tag_accounts == [account]

    page.shutdown()

    assert page._tag_loading_shutting_down
    assert page._pending_tag_accounts == []

    page._start_next_tag_loading()

    assert not page._tag_loading_controller.is_running
    assert page._tag_loading_controller._thread is None

def test_posts_page_loads_remote_wordpress_posts(qtbot):
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    repository = InMemoryAccountRepository()
    repository.add(account)

    remote_post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Remote WordPress test post",
        title="Remote WordPress test title",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
    )

    list_remote_posts = Mock()
    list_remote_posts.execute.return_value = (remote_post,)

    page = PostsPage(
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(AccountTagProvider({account: ()})),
        create_tag=CreateTag(AccountTagProvider({account: ()})),
        list_recent_publications=create_list_recent_publications(),
        list_remote_posts=list_remote_posts,
    )
    qtbot.addWidget(page)

    try:
        with qtbot.waitSignal(
            page._remote_post_loading_controller.posts_ready,
            timeout=5000,
        ):
            page.post_editor.destination_selector._checkboxes[0].setChecked(
                True
            )

        qtbot.waitUntil(
            lambda: page.remote_posts_panel.posts_list.count() == 1,
            timeout=5000,
        )

        assert (
                "Remote WordPress test title"
                in page.remote_posts_panel.posts_list.item(0).text()
        )

        list_remote_posts.execute.assert_called_once_with(
            account=account,
            limit=5,
        )
    finally:
        page.shutdown()

def test_posts_page_ignores_outdated_remote_posts(qtbot):
    first_account = Account(
        name="First WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    second_account = Account(
        name="Second WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    repository = InMemoryAccountRepository()
    repository.add(first_account)
    repository.add(second_account)

    first_started = Event()
    release_first = Event()

    def retrieve_posts(**kwargs):
        selected_account = kwargs["account"]

        if selected_account == first_account:
            first_started.set()

            if not release_first.wait(timeout=5):
                raise TimeoutError("First request was not released")

            return (
                RemotePost(
                    remote_id="101",
                    destination=PublishingDestination.WORDPRESS,
                    content="Outdated first account post",
                    title="Outdated first account title",
                    published_at=datetime(2026, 10, 15, 12, 0),
                    status="publish",
                ),
            )

        return (
            RemotePost(
                remote_id="202",
                destination=PublishingDestination.WORDPRESS,
                content="Current second account post",
                title="Current second account title",
                published_at=datetime(2026, 10, 15, 13, 0),
                status="publish",
            ),
        )

    list_remote_posts = Mock()
    list_remote_posts.execute.side_effect = retrieve_posts

    tag_provider = AccountTagProvider({
        first_account: (),
        second_account: (),
    })

    page = PostsPage(
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(tag_provider),
        create_tag=CreateTag(tag_provider),
        list_recent_publications=create_list_recent_publications(),
        list_remote_posts=list_remote_posts,
    )
    qtbot.addWidget(page)

    try:
        page.post_editor.destination_selector._checkboxes[0].setChecked(
            True
        )

        qtbot.waitUntil(first_started.is_set, timeout=5000)

        selector = page.post_editor.destination_selector

        first_index = selector._accounts.index(first_account)
        second_index = selector._accounts.index(second_account)

        selector._checkboxes[first_index].setChecked(False)
        selector._checkboxes[second_index].setChecked(True)

        assert page.post_editor.selected_accounts() == (second_account,)

        release_first.set()

        qtbot.waitUntil(
            lambda: (
                page.remote_posts_panel.posts_list.count() == 1
                and "Current second account title"
                in page.remote_posts_panel.posts_list.item(0).text()
            ),
            timeout=5000,
        )

        assert "Outdated first account title" not in (
            page.remote_posts_panel.posts_list.item(0).text()
        )
    finally:
        release_first.set()
        page.shutdown()

def test_posts_page_shows_remote_post_retrieval_error(qtbot):
    account = Account(
        name="WordPress Error Test",
        destination=PublishingDestination.WORDPRESS,
    )

    repository = InMemoryAccountRepository()
    repository.add(account)

    list_remote_posts = Mock()
    list_remote_posts.execute.side_effect = RuntimeError(
        "WordPress server unavailable"
    )

    tag_provider = AccountTagProvider({
        account: (),
    })

    page = PostsPage(
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(tag_provider),
        create_tag=CreateTag(tag_provider),
        list_recent_publications=create_list_recent_publications(),
        list_remote_posts=list_remote_posts,
    )
    qtbot.addWidget(page)

    try:
        page.post_editor.destination_selector._checkboxes[0].setChecked(
            True
        )

        qtbot.waitUntil(
            lambda: (
                "WordPress server unavailable"
                in page.remote_posts_panel.status_label.text()
            ),
            timeout=5000,
        )

        assert page.remote_posts_panel.posts_list.count() == 0

        list_remote_posts.execute.assert_called_once_with(
            account=account,
            limit=5,
        )
    finally:
        page.shutdown()


def test_posts_page_clears_retry_state_after_unexpected_publishing_error(
    qtbot,
) -> None:
    repository = InMemoryAccountRepository()
    repository.add(
        Account(
            name="Main Facebook",
            destination=PublishingDestination.FACEBOOK,
        )
    )

    list_tags, create_tag = create_tag_services()

    page = PostsPage(
        publish_post=PublishPost(
            publisher_router=PublisherRouter(
                {
                    PublishingDestination.FACEBOOK: FailingPublisher(),
                }
            ),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=create_list_recent_publications(),
    )
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText("Hello from SocialFlow")
    page.post_editor.destination_selector._checkboxes[0].setChecked(True)

    with qtbot.waitSignal(page.publishing_finished, timeout=5000):
        page.post_editor.publish_button.click()

    assert page.retry_failed_button.isEnabled()
    assert page._last_publish_request is not None
    assert page._last_publish_results

    page._on_publish_error("Publishing could not be completed.")

    assert page._last_publish_request is None
    assert page._last_publish_results == ()
    assert not page.retry_failed_button.isEnabled()
    assert page.publish_status.text() == "Publish request failed."
    assert page.publish_status.property("status") == "error"

    page.shutdown()


def test_posts_page_recovers_after_unexpected_worker_failure(
    qtbot,
) -> None:
    from unittest.mock import patch

    repository = InMemoryAccountRepository()
    repository.add(
        Account(
            name="Main Facebook",
            destination=PublishingDestination.FACEBOOK,
        )
    )

    publisher = RecordingPublisher()
    list_tags, create_tag = create_tag_services()

    publish_post = PublishPost(
        publisher_router=PublisherRouter(
            {
                PublishingDestination.FACEBOOK: publisher,
            }
        ),
        publication_id_generator=create_publication_id_generator(),
    )

    original_execute = publish_post.execute
    attempts = 0

    def execute(request, *, on_progress=None):
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            raise RuntimeError("Unexpected internal publishing failure")

        return original_execute(
            request,
            on_progress=on_progress,
        )

    page = PostsPage(
        publish_post=publish_post,
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=create_list_recent_publications(),
    )
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText(
        "Hello from SocialFlow"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(True)

    try:
        with patch.object(publish_post, "execute", side_effect=execute):
            with qtbot.waitSignal(page.publishing_finished, timeout=5000):
                page.post_editor.publish_button.click()

            assert attempts == 1
            assert page.post_editor.publish_button.isEnabled()
            assert page._last_publish_request is None
            assert page._last_publish_results == ()
            assert not page.retry_failed_button.isEnabled()
            assert page.publish_status.property("status") == "error"

            with qtbot.waitSignal(page.publishing_finished, timeout=5000):
                page.post_editor.publish_button.click()

            assert attempts == 2
            assert len(publisher.published_posts) == 1
            assert page.post_editor.publish_button.isEnabled()
            assert not page._publishing_controller.is_running

            assert (
                publisher.published_posts[0].source.text
                == "Hello from SocialFlow"
            )

    finally:
        page.shutdown()


def create_remote_tag_posts_page(
    accounts: tuple[Account, ...],
    list_remote_tags: Mock,
) -> PostsPage:
    """Create a PostsPage with remote-tag loading enabled."""
    repository = InMemoryAccountRepository()

    for account in accounts:
        repository.add(account)

    tag_provider = AccountTagProvider({
        account: ()
        for account in accounts
    })

    return PostsPage(
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(tag_provider),
        create_tag=CreateTag(tag_provider),
        list_recent_publications=create_list_recent_publications(),
        list_remote_tags=list_remote_tags,
    )



def test_posts_page_loads_remote_tags_for_selected_wordpress_account(
    qtbot,
) -> None:
    """Retrieve remote tag IDs and names in the background."""
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    expected_tags = (
        RemoteTag(remote_id=12, name="Python"),
        RemoteTag(remote_id=34, name="SocialFlow"),
    )

    list_remote_tags = Mock(spec=ListRemoteTags)
    list_remote_tags.execute.return_value = expected_tags

    page = create_remote_tag_posts_page(
        (account,),
        list_remote_tags,
    )
    qtbot.addWidget(page)

    try:
        page.post_editor.destination_selector._checkboxes[0].setChecked(
            True
        )

        qtbot.waitUntil(
            lambda: (
                page._loaded_remote_tags_account == account
                and page._loaded_remote_tags == expected_tags
            ),
            timeout=5000,
        )

        qtbot.waitUntil(
            lambda: not page._remote_tag_loading_controller.is_running,
            timeout=5000,
        )

        assert page._remote_tags_error is None
        list_remote_tags.execute.assert_called_once_with(account)
    finally:
        page.shutdown()


def test_posts_page_ignores_outdated_remote_tag_results(
    qtbot,
) -> None:
    """A previous account's tags must not replace current tags."""
    first_account = Account(
        name="First WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    second_account = Account(
        name="Second WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    first_started = Event()
    release_first = Event()

    first_tags = (
        RemoteTag(remote_id=11, name="Outdated"),
    )
    second_tags = (
        RemoteTag(remote_id=22, name="Current"),
    )

    def retrieve_tags(account: Account) -> tuple[RemoteTag, ...]:
        if account == first_account:
            first_started.set()

            if not release_first.wait(timeout=5):
                raise TimeoutError("First tag request was not released")

            return first_tags

        return second_tags

    list_remote_tags = Mock(spec=ListRemoteTags)
    list_remote_tags.execute.side_effect = retrieve_tags

    page = create_remote_tag_posts_page(
        (first_account, second_account),
        list_remote_tags,
    )
    qtbot.addWidget(page)

    try:
        selector = page.post_editor.destination_selector
        first_checkbox = selector._checkboxes[0]
        second_checkbox = selector._checkboxes[1]

        first_checkbox.setChecked(True)
        qtbot.waitUntil(first_started.is_set, timeout=5000)

        first_checkbox.setChecked(False)
        second_checkbox.setChecked(True)

        assert page.post_editor.selected_accounts() == (
            second_account,
        )

        release_first.set()

        qtbot.waitUntil(
            lambda: (
                page._loaded_remote_tags_account == second_account
                and page._loaded_remote_tags == second_tags
            ),
            timeout=5000,
        )

        qtbot.waitUntil(
            lambda: not page._remote_tag_loading_controller.is_running,
            timeout=5000,
        )

        assert page._loaded_remote_tags != first_tags
        assert list_remote_tags.execute.call_count == 2
    finally:
        release_first.set()
        page.shutdown()


def test_posts_page_stores_remote_tag_loading_error(
    qtbot,
) -> None:
    """Store retrieval errors without modifying publishing tags."""
    account = Account(
        name="WordPress Error Test",
        destination=PublishingDestination.WORDPRESS,
    )

    list_remote_tags = Mock(spec=ListRemoteTags)
    list_remote_tags.execute.side_effect = RuntimeError(
        "WordPress tags unavailable"
    )

    page = create_remote_tag_posts_page(
        (account,),
        list_remote_tags,
    )
    qtbot.addWidget(page)

    try:
        page.post_editor.destination_selector._checkboxes[0].setChecked(
            True
        )

        qtbot.waitUntil(
            lambda: (
                page._remote_tags_error
                == "WordPress tags unavailable"
            ),
            timeout=5000,
        )

        assert page._loaded_remote_tags == ()
        assert page._loaded_remote_tags_account is None
        assert page.post_editor.tag_selector.available_tags() == ()

        list_remote_tags.execute.assert_called_once_with(account)
    finally:
        page.shutdown()


def test_posts_page_shutdown_prevents_remote_tag_loading(
    qtbot,
) -> None:
    """Shutdown clears queued requests and prevents new workers."""
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    list_remote_tags = Mock(spec=ListRemoteTags)

    page = create_remote_tag_posts_page(
        (account,),
        list_remote_tags,
    )
    qtbot.addWidget(page)

    controller = page._remote_tag_loading_controller
    assert controller is not None

    page._pending_remote_tag_account = account

    page.shutdown()

    assert page._remote_tag_loading_shutting_down
    assert page._pending_remote_tag_account is None
    assert page._loaded_remote_tags == ()
    assert page._loaded_remote_tags_account is None

    page._refresh_remote_tags()
    page._start_remote_tag_loading()

    assert not controller.is_running
    list_remote_tags.execute.assert_not_called()


def test_switching_wordpress_accounts_clears_visible_remote_tag_names(
    qtbot,
) -> None:
    """Old account tag names disappear before new tags finish loading."""
    first_account = Account(
        name="First WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    second_account = Account(
        name="Second WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    first_tags = (
        RemoteTag(remote_id=11, name="First Account Tag"),
    )
    second_tags = (
        RemoteTag(remote_id=22, name="Second Account Tag"),
    )

    second_started = Event()
    release_second = Event()

    def retrieve_tags(account: Account) -> tuple[RemoteTag, ...]:
        if account == first_account:
            return first_tags

        second_started.set()

        if not release_second.wait(timeout=5):
            raise TimeoutError("Second tag request was not released")

        return second_tags

    list_remote_tags = Mock(spec=ListRemoteTags)
    list_remote_tags.execute.side_effect = retrieve_tags

    page = create_remote_tag_posts_page(
        (first_account, second_account),
        list_remote_tags,
    )
    qtbot.addWidget(page)

    try:
        account_selector = page.post_editor.destination_selector
        first_checkbox = account_selector._checkboxes[0]
        second_checkbox = account_selector._checkboxes[1]

        first_checkbox.setChecked(True)

        qtbot.waitUntil(
            lambda: page._loaded_remote_tags_account == first_account,
            timeout=5000,
        )

        tag_selector = page.remote_posts_panel.remote_tag_selector

        assert tag_selector.available_tags() == first_tags
        assert tag_selector.tags_list.item(0).text() == (
            "First Account Tag"
        )

        first_checkbox.setChecked(False)
        second_checkbox.setChecked(True)

        # The previous account's names must disappear immediately,
        # before the second request finishes.
        assert tag_selector.available_tags() == ()
        assert page._loaded_remote_tags_account is None

        qtbot.waitUntil(second_started.is_set, timeout=5000)

        assert tag_selector.available_tags() == ()

        release_second.set()

        qtbot.waitUntil(
            lambda: (
                page._loaded_remote_tags_account == second_account
                and tag_selector.available_tags() == second_tags
            ),
            timeout=5000,
        )

        assert tag_selector.tags_list.count() == 1
        assert tag_selector.tags_list.item(0).text() == (
            "Second Account Tag"
        )

    finally:
        release_second.set()
        page.shutdown()


def _create_featured_media_test_page(qtbot):
    """Build a PostsPage with one loaded WordPress post."""
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    repository = InMemoryAccountRepository()
    repository.add(account)

    remote_post = RemotePost(
        remote_id="123",
        destination=PublishingDestination.WORDPRESS,
        content="Original content",
        published_at=datetime(2026, 10, 15, 12, 0),
        status="publish",
        featured_media_id=456,
    )

    update_remote_post = Mock()

    page = PostsPage(
        publish_post=PublishPost(
            publisher_router=PublisherRouter({}),
            publication_id_generator=create_publication_id_generator(),
        ),
        list_accounts=ListAccounts(repository),
        list_tags=ListTags(NullTagProvider()),
        create_tag=CreateTag(NullTagProvider()),
        list_recent_publications=create_list_recent_publications(),
        update_remote_post=update_remote_post,
    )
    qtbot.addWidget(page)

    # Select the WordPress destination using Qt's public widget API.
    selector = page.post_editor.destination_selector
    checkboxes = selector.findChildren(QCheckBox)

    assert len(checkboxes) == 1
    checkboxes[0].setChecked(True)

    # Simulate the state after remote posts have finished loading.
    page._loaded_remote_posts_account = account
    page._loaded_remote_posts = (remote_post,)

    page.remote_posts_panel.show_posts((remote_post,))
    page.remote_posts_panel.posts_list.setCurrentRow(0)

    return page, account, update_remote_post

# noinspection PyProtectedMember
def _open_test_media_dialog(page, account):
    """Simulate an open picker for the currently selected post."""
    dialog = RemoteMediaSelectionDialog(page)

    page._remote_media_dialog = dialog
    page._remote_media_loading_account = account
    page._remote_media_loading_generation = (
        page._remote_posts_generation
    )
    page._remote_media_loading_shutting_down = False

    selected_row = page.remote_posts_panel.posts_list.currentRow()
    page._remote_media_selected_post_id = (
        page._loaded_remote_posts[selected_row].remote_id
    )

    dialog.finished.connect(page._on_remote_media_dialog_finished)

    return dialog

def test_posts_page_assigns_featured_media(qtbot):
    page, account, update_remote_post = (
        _create_featured_media_test_page(qtbot)
    )

    try:
        panel = page.remote_posts_panel

        panel.featured_media_checkbox.setChecked(True)
        panel.featured_media_input.setValue(789)

        assert panel.save_button.isEnabled()

        with qtbot.waitSignal(
            page._remote_post_updating_controller.post_updated,
            timeout=5000,
        ):
            panel.save_button.click()

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Original content",
            featured_media_id=789,
        )
    finally:
        page.shutdown()


def test_posts_page_removes_featured_media(qtbot):
    page, account, update_remote_post = (
        _create_featured_media_test_page(qtbot)
    )

    try:
        panel = page.remote_posts_panel

        panel.featured_media_checkbox.setChecked(True)
        panel.featured_media_input.setValue(0)

        assert panel.save_button.isEnabled()

        with qtbot.waitSignal(
            page._remote_post_updating_controller.post_updated,
            timeout=5000,
        ):
            panel.save_button.click()

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Original content",
            featured_media_id=0,
        )
    finally:
        page.shutdown()

def test_posts_page_preserves_featured_media_after_update_error(qtbot):
    page, account, update_remote_post = (
        _create_featured_media_test_page(qtbot)
    )

    update_remote_post.execute.side_effect = RuntimeError(
        "WordPress update failed"
    )

    try:
        panel = page.remote_posts_panel

        panel.featured_media_checkbox.setChecked(True)
        panel.featured_media_input.setValue(789)

        assert panel.save_button.isEnabled()

        with qtbot.waitSignal(
            page._remote_post_updating_controller.error_occurred,
            timeout=5000,
        ):
            panel.save_button.click()

        assert panel.featured_media_checkbox.isChecked()
        assert panel.featured_media_input.value() == 789

        assert panel.content_editor.isEnabled()
        assert panel.featured_media_checkbox.isEnabled()
        assert panel.featured_media_input.isEnabled()
        assert panel.save_button.isEnabled()

        assert (
            "WordPress update failed"
            in panel.status_label.text()
        )

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Original content",
            featured_media_id=789,
        )
    finally:
        page.shutdown()

def test_posts_page_rejects_invalid_featured_media_id(qtbot):
    page, _, update_remote_post = (
        _create_featured_media_test_page(qtbot)
    )

    try:
        page._handle_remote_post_save_with_media(
            remote_id="123",
            content="Original content",
            tags=None,
            featured_media_id=-1,
        )

        update_remote_post.execute.assert_not_called()

        assert (
            "non-negative integer"
            in page.remote_posts_panel.status_label.text()
        )

        assert page.remote_posts_panel.content_editor.isEnabled()
    finally:
        page.shutdown()

def test_media_dialog_does_not_apply_cancelled_selection(qtbot):
    page = create_posts_page()
    qtbot.addWidget(page)

    dialog = RemoteMediaSelectionDialog(page)
    page._remote_media_dialog = dialog

    dialog.finished.connect(page._on_remote_media_dialog_finished)

    dialog.reject()

    assert page._remote_media_dialog is None
    assert not page.remote_posts_panel.featured_media_checkbox.isChecked()

def test_media_selection_applies_selected_image(qtbot):
    page, account, _ = _create_featured_media_test_page(qtbot)

    try:
        dialog = _open_test_media_dialog(page, account)

        media = RemoteMedia(
            remote_id=789,
            destination=PublishingDestination.WORDPRESS,
            source_url="https://example.com/image.jpg",
            title="Featured image",
        )

        page._on_remote_media_loaded((media,))

        assert dialog.media_list.count() == 1

        dialog.media_list.setCurrentRow(0)
        dialog.accept()

        assert page._remote_media_dialog is None
        assert page.remote_posts_panel.featured_media_checkbox.isChecked()
        assert page.remote_posts_panel.featured_media_input.value() == 789
    finally:
        page.shutdown()


def test_media_selection_does_not_apply_to_different_post(qtbot):
    page, account, _ = _create_featured_media_test_page(qtbot)

    try:
        dialog = _open_test_media_dialog(page, account)

        media = RemoteMedia(
            remote_id=789,
            destination=PublishingDestination.WORDPRESS,
            source_url="https://example.com/image.jpg",
            title="Featured image",
        )

        page._on_remote_media_loaded((media,))
        dialog.media_list.setCurrentRow(0)

        second_post = RemotePost(
            remote_id="124",
            destination=PublishingDestination.WORDPRESS,
            content="Second post",
            published_at=datetime(2026, 10, 16, 12, 0),
            status="publish",
            featured_media_id=555,
        )

        page._loaded_remote_posts = (
            page._loaded_remote_posts[0],
            second_post,
        )

        page.remote_posts_panel.show_posts(page._loaded_remote_posts)
        page.remote_posts_panel.posts_list.setCurrentRow(1)

        dialog.accept()

        assert page._remote_media_dialog is None
        assert page.remote_posts_panel.featured_media_input.value() == 555
        assert not page.remote_posts_panel.featured_media_checkbox.isChecked()
    finally:
        page.shutdown()


def test_media_loading_error_preserves_featured_image(qtbot):
    page, account, _ = _create_featured_media_test_page(qtbot)

    try:
        dialog = _open_test_media_dialog(page, account)

        page._on_remote_media_error("HTTP 403")

        assert (
            "HTTP 403"
            in dialog.status_label.text()
        )
        assert dialog.media_list.count() == 0
        assert not dialog.select_button.isEnabled()

        dialog.reject()

        assert page._remote_media_dialog is None
        assert page.remote_posts_panel.featured_media_input.value() == 456
        assert not page.remote_posts_panel.featured_media_checkbox.isChecked()
    finally:
        page.shutdown()

def test_posts_page_saves_wordpress_status_only(qtbot):
    page, account, update_remote_post = (
        _create_featured_media_test_page(qtbot)
    )

    try:
        panel = page.remote_posts_panel

        panel.post_status_selector.setCurrentIndex(
            panel.post_status_selector.findData("draft")
        )

        with qtbot.waitSignal(
            page._remote_post_updating_controller.post_updated,
            timeout=5000,
        ):
            panel.save_button.click()

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Original content",
            status="draft",
        )
    finally:
        page.shutdown()


def test_posts_page_saves_status_with_featured_media(qtbot):
    page, account, update_remote_post = (
        _create_featured_media_test_page(qtbot)
    )

    try:
        panel = page.remote_posts_panel

        panel.featured_media_checkbox.setChecked(True)
        panel.featured_media_input.setValue(789)
        panel.post_status_selector.setCurrentIndex(
            panel.post_status_selector.findData("draft")
        )

        with qtbot.waitSignal(
            page._remote_post_updating_controller.post_updated,
            timeout=5000,
        ):
            panel.save_button.click()

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Original content",
            featured_media_id=789,
            status="draft",
        )
    finally:
        page.shutdown()


def test_posts_page_preserves_status_after_update_error(qtbot):
    page, account, update_remote_post = (
        _create_featured_media_test_page(qtbot)
    )

    update_remote_post.execute.side_effect = RuntimeError(
        "WordPress update failed"
    )

    try:
        panel = page.remote_posts_panel

        panel.post_status_selector.setCurrentIndex(
            panel.post_status_selector.findData("draft")
        )

        with qtbot.waitSignal(
            page._remote_post_updating_controller.error_occurred,
            timeout=5000,
        ):
            panel.save_button.click()

        assert panel.post_status_selector.isEnabled()
        assert panel.post_status_selector.currentData() == "draft"
        assert panel.save_button.isEnabled()
        assert "WordPress update failed" in panel.status_label.text()

        update_remote_post.execute.assert_called_once_with(
            account=account,
            post_id=123,
            content="Original content",
            status="draft",
        )
    finally:
        page.shutdown()

def test_shutdown_ignores_late_remote_post_update_success(qtbot):
    page, account, update_remote_post = (
        _create_featured_media_test_page(qtbot)
    )

    try:
        page._remote_post_updating_account = account
        page._remote_post_update_succeeded = False

        page.shutdown()

        page._on_remote_post_updated()
        page._on_remote_post_update_finished()

        assert not page._remote_post_update_succeeded
        assert page._remote_post_updating_shutting_down
    finally:
        page.shutdown()


def test_shutdown_ignores_late_remote_post_update_error(qtbot):
    page, account, update_remote_post = (
        _create_featured_media_test_page(qtbot)
    )

    try:
        page._remote_post_updating_account = account

        original_status = page.remote_posts_panel.status_label.text()

        page.shutdown()

        page._on_remote_post_update_error(
            "Late WordPress update failure"
        )

        assert (
            page.remote_posts_panel.status_label.text()
            == original_status
        )
        assert page._remote_post_updating_shutting_down
    finally:
        page.shutdown()

def test_remote_post_update_error_ignores_previous_account(qtbot):
    page, account, update_remote_post = (
        _create_featured_media_test_page(qtbot)
    )

    try:
        page._remote_post_updating_account = account

        # Simulate switching away from the account that started the save.
        page._loaded_remote_posts_account = None
        page._loaded_remote_posts = ()
        page.remote_posts_panel.show_empty()

        original_status = page.remote_posts_panel.status_label.text()

        page._on_remote_post_update_error(
            "Old account WordPress failure"
        )

        assert page.remote_posts_panel.status_label.text() == original_status
        assert page.remote_posts_panel.posts_list.count() == 0
        assert not page.remote_posts_panel.content_editor.isEnabled()
        assert not page.remote_posts_panel.save_button.isEnabled()
    finally:
        page.shutdown()


def test_remote_post_update_success_does_not_refresh_previous_account(
    qtbot,
    monkeypatch,
):
    page, account, update_remote_post = (
        _create_featured_media_test_page(qtbot)
    )

    refresh_calls = []
    monkeypatch.setattr(
        page,
        "_refresh_remote_posts",
        lambda: refresh_calls.append(True),
    )

    try:
        page._remote_post_updating_account = account
        page._remote_post_update_succeeded = True

        # The active account has changed before the update completes.
        page._loaded_remote_posts_account = None
        page._loaded_remote_posts = ()
        page.remote_posts_panel.show_empty()

        page._on_remote_post_update_finished()

        assert refresh_calls == []
        assert page._remote_post_updating_account is None
        assert not page._remote_post_update_succeeded
        assert page.remote_posts_panel.posts_list.count() == 0
    finally:
        page.shutdown()


def test_remote_post_update_failure_does_not_restore_new_account_editor(
    qtbot,
    monkeypatch,
):
    page, account, update_remote_post = (
        _create_featured_media_test_page(qtbot)
    )

    restore_calls = []
    monkeypatch.setattr(
        page.remote_posts_panel,
        "restore_editing",
        lambda: restore_calls.append(True),
    )

    try:
        page._remote_post_updating_account = account
        page._remote_post_update_succeeded = False

        # The previous save finishes after its account was deselected.
        page._loaded_remote_posts_account = None
        page._loaded_remote_posts = ()
        page.remote_posts_panel.show_empty()

        page._on_remote_post_update_finished()

        assert restore_calls == []
        assert page._remote_post_updating_account is None
        assert not page._remote_post_update_succeeded
    finally:
        page.shutdown()


def test_remote_post_update_success_ignores_reselected_same_account(
    qtbot,
    monkeypatch,
):
    page, account, update_remote_post = (
        _create_featured_media_test_page(qtbot)
    )

    refresh_calls = []
    monkeypatch.setattr(
        page,
        "_refresh_remote_posts",
        lambda: refresh_calls.append(True),
    )

    try:
        # An update started in the original account session.
        page._remote_post_updating_account = account
        page._remote_post_updating_generation = (
            page._remote_posts_generation
        )
        page._remote_post_update_succeeded = True

        # Switching away invalidates the original session.
        page._remote_posts_generation += 1
        page._loaded_remote_posts_account = None
        page._loaded_remote_posts = ()
        page.remote_posts_panel.show_empty()

        # The user returns to the same account.
        page._remote_posts_generation += 1
        page._loaded_remote_posts_account = account

        page._on_remote_post_update_finished()

        assert refresh_calls == []
        assert page._remote_post_updating_account is None
        assert not page._remote_post_update_succeeded
    finally:
        page.shutdown()

def test_remote_post_update_error_ignores_reselected_same_account(
    qtbot,
    monkeypatch,
):
    page, account, update_remote_post = (
        _create_featured_media_test_page(qtbot)
    )

    restore_calls = []
    monkeypatch.setattr(
        page.remote_posts_panel,
        "restore_editing",
        lambda: restore_calls.append(True),
    )

    try:
        page._remote_post_updating_account = account
        page._remote_post_updating_generation = (
            page._remote_posts_generation
        )

        # Leave the original session.
        page._remote_posts_generation += 1
        page._loaded_remote_posts_account = None
        page._loaded_remote_posts = ()
        page.remote_posts_panel.show_empty()

        # Return to the same account in a different session.
        page._remote_posts_generation += 1
        page._loaded_remote_posts_account = account

        original_status = (
            page.remote_posts_panel.status_label.text()
        )

        page._on_remote_post_update_error(
            "Failure from the previous account session"
        )

        assert restore_calls == []
        assert (
            page.remote_posts_panel.status_label.text()
            == original_status
        )
    finally:
        page.shutdown()


def test_remote_post_update_success_accepts_current_generation(
    qtbot,
    monkeypatch,
):
    page, account, _ = _create_featured_media_test_page(qtbot)
    refresh_calls = []

    monkeypatch.setattr(
        page,
        "_refresh_remote_posts",
        lambda: refresh_calls.append(True),
    )

    try:
        page._remote_post_updating_account = account
        page._remote_post_updating_generation = (
            page._remote_posts_generation
        )
        page._remote_post_update_succeeded = True

        page._on_remote_post_update_finished()

        assert refresh_calls == [True]
        assert page.remote_posts_panel.status_label.text() == (
            "WordPress post updated successfully."
        )
        assert page._remote_post_updating_account is None
        assert page._remote_post_updating_generation is None
        assert not page._remote_post_update_succeeded
    finally:
        page.shutdown()


def test_remote_post_update_error_accepts_current_generation(
    qtbot,
    monkeypatch,
):
    page, account, _ = _create_featured_media_test_page(qtbot)
    restore_calls = []

    monkeypatch.setattr(
        page.remote_posts_panel,
        "restore_editing",
        lambda: restore_calls.append(True),
    )

    try:
        page._remote_post_updating_account = account
        page._remote_post_updating_generation = (
            page._remote_posts_generation
        )

        page._on_remote_post_update_error(
            "WordPress permission denied"
        )

        assert page.remote_posts_panel.status_label.text() == (
            "Unable to update WordPress post: "
            "WordPress permission denied"
        )
        assert restore_calls == [True]
    finally:
        page.shutdown()


def test_remote_post_update_failure_accepts_current_generation(
    qtbot,
    monkeypatch,
):
    page, account, _ = _create_featured_media_test_page(qtbot)
    restore_calls = []

    monkeypatch.setattr(
        page.remote_posts_panel,
        "restore_editing",
        lambda: restore_calls.append(True),
    )

    try:
        page._remote_post_updating_account = account
        page._remote_post_updating_generation = (
            page._remote_posts_generation
        )
        page._remote_post_update_succeeded = False

        page._on_remote_post_update_finished()

        assert restore_calls == [True]
        assert page._remote_post_updating_account is None
        assert page._remote_post_updating_generation is None
        assert not page._remote_post_update_succeeded
    finally:
        page.shutdown()


def test_remote_posts_loading_ignores_reselected_same_account(
    qtbot,
    monkeypatch,
):
    """An old A request must not populate a newly selected A session."""
    page, account, _ = _create_featured_media_test_page(qtbot)

    stale_posts = (
        RemotePost(
            remote_id="999",
            destination=PublishingDestination.WORDPRESS,
            content="Outdated response",
            published_at=datetime(2026, 10, 15, 12, 0),
            status="publish",
        ),
    )

    displayed_posts = []
    monkeypatch.setattr(
        page.remote_posts_panel,
        "show_posts",
        lambda posts: displayed_posts.append(posts),
    )

    try:
        # The original request started for account A.
        page._remote_post_loading_account = account
        original_generation = page._remote_posts_generation

        # Simulate leaving A and returning to A.
        page._remote_posts_generation += 2
        page._pending_remote_post_account = None

        # The selected account is A again, but this response
        # belongs to the earlier generation.
        page._remote_post_loading_generation = original_generation

        page._on_remote_posts_loaded(stale_posts)

        assert displayed_posts == []
        assert page._loaded_remote_posts != stale_posts
    finally:
        page.shutdown()


def test_remote_posts_loading_accepts_current_generation(
    qtbot,
    monkeypatch,
):
    """Current-generation results must still populate remote posts."""
    page, account, _ = _create_featured_media_test_page(qtbot)

    posts = (
        RemotePost(
            remote_id="123",
            destination=PublishingDestination.WORDPRESS,
            content="Current WordPress post",
            published_at=datetime(2026, 10, 15, 12, 0),
            status="publish",
        ),
    )

    displayed_posts = []
    monkeypatch.setattr(
        page.remote_posts_panel,
        "show_posts",
        lambda value: displayed_posts.append(value),
    )

    try:
        page._remote_post_loading_account = account
        page._remote_post_loading_generation = (
            page._remote_posts_generation
        )
        page._pending_remote_post_account = None

        page._on_remote_posts_loaded(posts)

        assert displayed_posts == [posts]
        assert page._loaded_remote_posts == posts
        assert page._loaded_remote_posts_account == account
    finally:
        page.shutdown()


def test_remote_posts_loading_error_accepts_current_generation(
    qtbot,
    monkeypatch,
):
    """Current-generation loading errors must remain visible."""
    page, account, _ = _create_featured_media_test_page(qtbot)

    errors = []
    monkeypatch.setattr(
        page.remote_posts_panel,
        "show_error",
        lambda message: errors.append(message),
    )

    try:
        page._remote_post_loading_account = account
        page._remote_post_loading_generation = (
            page._remote_posts_generation
        )
        page._pending_remote_post_account = None

        page._on_remote_posts_error("WordPress request failed")

        assert errors == ["WordPress request failed"]
    finally:
        page.shutdown()


def test_remote_posts_loading_finished_clears_generation(
    qtbot,
    monkeypatch,
):
    """Finishing a load must discard its request-generation state."""
    page, account, _ = _create_featured_media_test_page(qtbot)

    next_load_calls = []
    monkeypatch.setattr(
        page,
        "_start_remote_post_loading",
        lambda: next_load_calls.append(True),
    )

    try:
        page._remote_post_loading_account = account
        page._remote_post_loading_generation = (
            page._remote_posts_generation
        )

        page._on_remote_post_loading_finished()

        assert page._remote_post_loading_account is None
        assert page._remote_post_loading_generation is None
        assert next_load_calls == [True]
    finally:
        page.shutdown()


def test_remote_tags_loading_ignores_reselected_same_account(
    qtbot,
    monkeypatch,
):
    """Old tag results must not update a newly selected A session."""
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    list_remote_tags = Mock(spec=ListRemoteTags)
    page = create_remote_tag_posts_page(
        (account,),
        list_remote_tags,
    )
    qtbot.addWidget(page)

    stale_tags = (
        RemoteTag(remote_id=999, name="Outdated tag"),
    )

    displayed_tags = []
    monkeypatch.setattr(
        page,
        "_selected_wordpress_account",
        lambda: account,
    )
    monkeypatch.setattr(
        page.remote_posts_panel,
        "set_available_remote_tags",
        lambda tags: displayed_tags.append(tags),
    )

    try:
        # The original request belongs to an earlier A session.
        page._remote_tag_loading_account = account
        page._remote_tag_loading_generation = 1

        # Simulate A -> B -> A, with no pending request
        # at the moment the old callback arrives.
        page._remote_tags_generation = 3
        page._pending_remote_tag_account = None

        page._on_remote_tags_loaded(stale_tags)

        assert displayed_tags == []
        assert page._loaded_remote_tags != stale_tags
        assert page._loaded_remote_tags_account is None
    finally:
        page.shutdown()


def test_remote_tags_loading_accepts_current_generation(
    qtbot,
    monkeypatch,
):
    """Current-generation tag results must update the editor."""
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    list_remote_tags = Mock(spec=ListRemoteTags)
    page = create_remote_tag_posts_page(
        (account,),
        list_remote_tags,
    )
    qtbot.addWidget(page)

    tags = (
        RemoteTag(remote_id=12, name="Python"),
        RemoteTag(remote_id=34, name="News"),
    )

    displayed_tags = []
    monkeypatch.setattr(
        page,
        "_selected_wordpress_account",
        lambda: account,
    )
    monkeypatch.setattr(
        page.remote_posts_panel,
        "set_available_remote_tags",
        lambda value: displayed_tags.append(value),
    )

    try:
        page._remote_tag_loading_account = account
        page._remote_tag_loading_generation = (
            page._remote_tags_generation
        )
        page._pending_remote_tag_account = None

        page._on_remote_tags_loaded(tags)

        assert displayed_tags == [tags]
        assert page._loaded_remote_tags == tags
        assert page._loaded_remote_tags_account == account
    finally:
        page.shutdown()


def test_remote_tags_loading_error_accepts_current_generation(
    qtbot,
    monkeypatch,
):
    """Current-generation tag-loading errors must be reported."""
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    list_remote_tags = Mock(spec=ListRemoteTags)
    page = create_remote_tag_posts_page(
        (account,),
        list_remote_tags,
    )
    qtbot.addWidget(page)

    try:
        page._remote_tag_loading_account = account
        page._remote_tag_loading_generation = (
            page._remote_tags_generation
        )
        page._pending_remote_tag_account = None

        monkeypatch.setattr(
            page,
            "_selected_wordpress_account",
            lambda: account,
        )

        page._on_remote_tags_error("WordPress tag request failed")

        assert page._remote_tags_error == "WordPress tag request failed"
        assert page._loaded_remote_tags == ()
        assert page._loaded_remote_tags_account is None
    finally:
        page.shutdown()


def test_remote_tags_loading_finished_clears_generation(
    qtbot,
    monkeypatch,
):
    """Completing a tag request clears its generation state."""
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    list_remote_tags = Mock(spec=ListRemoteTags)
    page = create_remote_tag_posts_page(
        (account,),
        list_remote_tags,
    )
    qtbot.addWidget(page)

    next_load_calls = []
    monkeypatch.setattr(
        page,
        "_start_remote_tag_loading",
        lambda: next_load_calls.append(True),
    )

    try:
        page._remote_tag_loading_account = account
        page._remote_tag_loading_generation = (
            page._remote_tags_generation
        )

        page._on_remote_tag_loading_finished()

        assert page._remote_tag_loading_account is None
        assert page._remote_tag_loading_generation is None
        assert next_load_calls == [True]
    finally:
        page.shutdown()


def test_remote_media_loading_ignores_reselected_same_account(
    qtbot,
    monkeypatch,
):
    """Old media results must not update a picker after A -> B -> A."""
    page, account, _ = _create_featured_media_test_page(qtbot)

    dialog = _open_test_media_dialog(page, account)
    displayed_media = []

    monkeypatch.setattr(
        dialog,
        "show_media",
        lambda media: displayed_media.append(media),
    )

    try:
        # Media loading started during the original A session.
        original_generation = page._remote_posts_generation
        page._remote_media_loading_generation = original_generation

        # Simulate leaving A and returning to A.
        # The account and post IDs are the same, but the
        # original media request belongs to an older session.
        page._remote_posts_generation += 2

        page._on_remote_media_loaded(())

        assert displayed_media == []
    finally:
        page.shutdown()


def test_remote_media_loading_accepts_current_generation(
    qtbot,
    monkeypatch,
):
    """Current-generation media results must reach the picker."""
    page, account, _ = _create_featured_media_test_page(qtbot)
    dialog = _open_test_media_dialog(page, account)

    displayed_media = []
    monkeypatch.setattr(
        dialog,
        "show_media",
        lambda media: displayed_media.append(media),
    )

    try:
        assert page._remote_media_loading_generation == (
            page._remote_posts_generation
        )

        page._on_remote_media_loaded(())

        assert displayed_media == [()]
    finally:
        page.shutdown()

def test_remote_media_error_accepts_current_generation(qtbot):
    """Current-generation media errors must reach the picker."""
    page, account, _ = _create_featured_media_test_page(qtbot)
    dialog = _open_test_media_dialog(page, account)

    try:
        assert page._remote_media_loading_generation == (
            page._remote_posts_generation
        )

        page._on_remote_media_error("WordPress media request failed")

        assert (
            "WordPress media request failed"
            in dialog.status_label.text()
        )
    finally:
        page.shutdown()

def test_remote_media_dialog_finished_clears_generation(qtbot):
    """Closing the picker must discard its request generation."""
    page, account, _ = _create_featured_media_test_page(qtbot)
    _open_test_media_dialog(page, account)

    try:
        assert page._remote_media_loading_generation == (
            page._remote_posts_generation
        )

        page._on_remote_media_dialog_finished(0)

        assert page._remote_media_dialog is None
        assert page._remote_media_loading_account is None
        assert page._remote_media_loading_generation is None
        assert page._remote_media_selected_post_id is None
    finally:
        page.shutdown()

def test_remote_media_loading_finished_preserves_open_dialog_state(qtbot):
    """Worker cleanup must not invalidate an open media picker."""
    page, account, _ = _create_featured_media_test_page(qtbot)
    dialog = _open_test_media_dialog(page, account)

    try:
        original_generation = page._remote_media_loading_generation
        original_post_id = page._remote_media_selected_post_id

        assert original_generation == page._remote_posts_generation
        assert page._remote_media_loading_account == account

        page._on_remote_media_loading_finished()

        assert page._remote_media_dialog is dialog
        assert page._remote_media_loading_account == account
        assert page._remote_media_loading_generation == original_generation
        assert page._remote_media_selected_post_id == original_post_id
    finally:
        page.shutdown()

def test_remote_media_loading_finished_clears_closed_dialog_state(qtbot):
    """Late worker completion must not restore a closed picker session."""
    page, account, _ = _create_featured_media_test_page(qtbot)
    _open_test_media_dialog(page, account)

    try:
        assert page._remote_media_loading_account == account
        assert page._remote_media_loading_generation is not None

        # The user closes the picker before worker completion.
        page._on_remote_media_dialog_finished(0)

        assert page._remote_media_dialog is None

        # A delayed worker-finished signal arrives afterward.
        page._on_remote_media_loading_finished()

        assert page._remote_media_dialog is None
        assert page._remote_media_loading_account is None
        assert page._remote_media_loading_generation is None
        assert page._remote_media_selected_post_id is None
    finally:
        page.shutdown()

def test_remote_media_loading_ignores_callback_after_shutdown(
    qtbot,
    monkeypatch,
):
    """Media results must not update a picker after page shutdown."""
    page, account, _ = _create_featured_media_test_page(qtbot)
    dialog = _open_test_media_dialog(page, account)

    displayed_media = []
    monkeypatch.setattr(
        dialog,
        "show_media",
        lambda media: displayed_media.append(media),
    )

    try:
        page.shutdown()

        # Simulate a delayed worker callback after shutdown.
        page._on_remote_media_loaded(())

        assert displayed_media == []
        assert page._remote_media_loading_shutting_down is True
    finally:
        page.shutdown()


def test_remote_media_error_ignored_after_shutdown(
    qtbot,
    monkeypatch,
):
    """Media errors must not update a picker after page shutdown."""
    page, account, _ = _create_featured_media_test_page(qtbot)
    dialog = _open_test_media_dialog(page, account)

    displayed_errors = []
    monkeypatch.setattr(
        dialog,
        "show_error",
        lambda message: displayed_errors.append(message),
    )

    try:
        page.shutdown()

        # Simulate a delayed worker error after shutdown.
        page._on_remote_media_error("WordPress media request failed")

        assert displayed_errors == []
        assert page._remote_media_loading_shutting_down is True
    finally:
        page.shutdown()

def test_remote_media_picker_cannot_reopen_while_loading(
    qtbot,
    monkeypatch,
):
    """A closed picker cannot reopen while its worker is running."""
    page, account, _ = _create_featured_media_test_page(qtbot)
    _open_test_media_dialog(page, account)

    class RunningMediaController:
        is_running = True

    try:
        # Simulate closing the first picker.
        page._on_remote_media_dialog_finished(0)

        assert page._remote_media_dialog is None

        # Simulate the original media request still running.
        monkeypatch.setattr(
            page,
            "_remote_media_loading_controller",
            RunningMediaController(),
        )

        page._browse_remote_media()

        # No second picker should have been created.
        assert page._remote_media_dialog is None
    finally:
        # Restore the original controller before shutdown.
        monkeypatch.undo()
        page.shutdown()


def test_remote_media_picker_state_cleared_before_reopening(qtbot):
    """A completed request must not retain a closed picker session."""
    page, account, _ = _create_featured_media_test_page(qtbot)
    _open_test_media_dialog(page, account)

    try:
        assert page._remote_media_loading_account == account
        assert page._remote_media_loading_generation is not None

        # Close the original picker.
        page._on_remote_media_dialog_finished(0)

        # The original worker finishes afterward.
        page._on_remote_media_loading_finished()

        assert page._remote_media_dialog is None
        assert page._remote_media_loading_account is None
        assert page._remote_media_loading_generation is None
        assert page._remote_media_selected_post_id is None

        # Simulate starting a new picker session.
        new_dialog = _open_test_media_dialog(page, account)

        assert page._remote_media_dialog is new_dialog
        assert page._remote_media_loading_account == account
        assert page._remote_media_loading_generation == (
            page._remote_posts_generation
        )
    finally:
        page.shutdown()


def test_remote_media_results_ignored_after_dialog_closes(
    qtbot,
    monkeypatch,
):
    """Results arriving after picker closure must be ignored."""
    page, account, _ = _create_featured_media_test_page(qtbot)
    dialog = _open_test_media_dialog(page, account)

    displayed_media = []
    monkeypatch.setattr(
        dialog,
        "show_media",
        lambda media: displayed_media.append(media),
    )

    try:
        page._on_remote_media_dialog_finished(0)
        page._on_remote_media_loaded(())

        assert displayed_media == []
        assert page._remote_media_dialog is None
    finally:
        page.shutdown()


def test_remote_media_errors_ignored_after_dialog_closes(
    qtbot,
    monkeypatch,
):
    """Errors arriving after picker closure must be ignored."""
    page, account, _ = _create_featured_media_test_page(qtbot)
    dialog = _open_test_media_dialog(page, account)

    displayed_errors = []
    monkeypatch.setattr(
        dialog,
        "show_error",
        lambda message: displayed_errors.append(message),
    )

    try:
        page._on_remote_media_dialog_finished(0)
        page._on_remote_media_error("Delayed media error")

        assert displayed_errors == []
        assert page._remote_media_dialog is None
    finally:
        page.shutdown()

def test_general_tags_ignore_reselected_account_session(qtbot):
    """An old A request must not populate tags after A -> off -> A."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        checkbox = page.post_editor.destination_selector._checkboxes[0]
        checkbox.setChecked(True)

        account = page.post_editor.selected_accounts()[0]

        # Simulate a request started in the original account session.
        page._tag_loading_account = account

        # Leave and re-enter the same account selection.
        checkbox.setChecked(False)
        checkbox.setChecked(True)

        page._on_tags_loaded((Tag(name="StaleTag"),))

        assert (
            Tag(name="StaleTag")
            not in page.post_editor.tag_selector.available_tags()
        )
        assert (
            account.id not in page._loaded_tags_by_account
            or Tag(name="StaleTag")
            not in page._loaded_tags_by_account[account.id]
        )
    finally:
        page.shutdown()


def test_general_tags_accept_current_account_session(qtbot):
    """A valid result must populate tags for the selected account."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        checkbox = page.post_editor.destination_selector._checkboxes[0]
        checkbox.setChecked(True)

        account = page.post_editor.selected_accounts()[0]
        page._tag_loading_account = account
        page._tag_loading_generation = page._tags_generation

        expected_tags = (Tag(name="CurrentTag"),)

        page._on_tags_loaded(expected_tags)

        assert page._loaded_tags_by_account[account.id] == expected_tags
        assert (
            Tag(name="CurrentTag")
            in page.post_editor.tag_selector.available_tags()
        )
    finally:
        page.shutdown()


def test_general_tags_ignore_results_after_shutdown(qtbot):
    """Tag callbacks must not update editor state after shutdown."""
    page = create_posts_page()
    qtbot.addWidget(page)

    checkbox = page.post_editor.destination_selector._checkboxes[0]
    checkbox.setChecked(True)

    account = page.post_editor.selected_accounts()[0]
    page._tag_loading_account = account
    page._tag_loading_generation = page._tags_generation

    try:
        page.shutdown()

        page._on_tags_loaded((Tag(name="LateTag"),))

        assert Tag(name="LateTag") not in (
            page.post_editor.tag_selector.available_tags()
        )
        assert Tag(name="LateTag") not in (
            page._loaded_tags_by_account.get(account.id, ())
        )
    finally:
        page.shutdown()


def test_general_tags_finished_clears_loading_generation(qtbot):
    """Finishing a tag request clears its account and generation."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        page._pending_tag_accounts.clear()
        page._tag_loading_account = None
        page._tag_loading_generation = page._tags_generation

        page._on_tag_loading_finished()

        assert page._tag_loading_account is None
        assert page._tag_loading_generation is None
    finally:
        page.shutdown()


def test_general_tags_queue_uses_current_generation(qtbot, monkeypatch):
    """A queued account starts with the latest selection generation."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        checkbox = page.post_editor.destination_selector._checkboxes[0]
        checkbox.setChecked(True)

        account = page.post_editor.selected_accounts()[0]

        # Represent an old request that has become outdated.
        page._tag_loading_account = account
        page._tag_loading_generation = page._tags_generation - 1

        # Queue a fresh request for the currently selected account.
        page._pending_tag_accounts[:] = [account]
        page._loaded_tags_by_account.pop(account.id, None)

        started_accounts = []

        monkeypatch.setattr(
            page._tag_loading_controller,
            "start",
            lambda selected_account: started_accounts.append(
                selected_account
            ),
        )

        page._on_tag_loading_finished()

        assert started_accounts == [account]
        assert page._tag_loading_account == account
        assert page._tag_loading_generation == page._tags_generation
    finally:
        page.shutdown()


def test_wordpress_tags_created_ignored_without_active_workflow(qtbot):
    """A stray success callback must not mark creation complete."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        assert page._pending_publish_request is None
        assert page._preparing_wordpress_account is None

        page._on_wordpress_tags_created(())

        assert page._wordpress_tag_creation_completed is False
    finally:
        page.shutdown()


def test_wordpress_tag_creation_error_ignored_without_active_workflow(qtbot):
    """A stray error must not change the idle publishing state."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        original_status = page.publish_status.text()

        page._on_wordpress_tag_creation_error("Delayed creation error")

        assert page._pending_publish_request is None
        assert page._wordpress_tag_creation_failed is False
        assert page.publish_status.text() == original_status
    finally:
        page.shutdown()


def test_wordpress_tags_created_ignored_after_cancellation(qtbot):
    """A late success callback must not revive cancelled creation."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        page._cancel_wordpress_tag_preparation()

        page._on_wordpress_tags_created(())

        assert page._pending_publish_request is None
        assert page._wordpress_tag_creation_completed is False
        assert page._wordpress_tag_creation_failed is False
    finally:
        page.shutdown()


def test_wordpress_tag_creation_error_ignored_after_cancellation(qtbot):
    """A late error must not overwrite cancelled workflow state."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        page._cancel_wordpress_tag_preparation()
        original_status = page.publish_status.text()

        page._on_wordpress_tag_creation_error("Delayed creation error")

        assert page._pending_publish_request is None
        assert page._wordpress_tag_creation_failed is False
        assert page.publish_status.text() == original_status
    finally:
        page.shutdown()

def test_wordpress_tags_created_accepted_during_active_workflow(qtbot):
    """A successful creation callback is accepted during preparation."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        account = page.post_editor.destination_selector._accounts[0]

        page._pending_publish_request = object()
        page._preparing_wordpress_account = account

        page._on_wordpress_tags_created(())

        assert page._wordpress_tag_creation_completed is True
        assert page._wordpress_tag_creation_failed is False
    finally:
        page.shutdown()


def test_wordpress_tag_creation_error_handled_during_active_workflow(qtbot):
    """A creation error is reported and cancels active preparation."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        account = page.post_editor.destination_selector._accounts[0]

        page._pending_publish_request = object()
        page._preparing_wordpress_account = account

        page._on_wordpress_tag_creation_error("HTTP 403")

        assert "HTTP 403" in page.publish_status.text()
        assert page._pending_publish_request is None
        assert page._preparing_wordpress_account is None
    finally:
        page.shutdown()


def test_wordpress_tag_creation_finished_ignored_without_active_workflow(qtbot):
    """A stray finished callback must not cancel an idle workflow."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        page._wordpress_tag_creation_completed = True

        page._on_wordpress_tag_creation_finished()

        assert page._wordpress_tag_creation_completed is True
        assert page._pending_publish_request is None
    finally:
        page.shutdown()


def test_wordpress_tag_creation_finished_ignored_after_cancellation(qtbot):
    """A delayed finished callback must not modify cancelled state."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        page._cancel_wordpress_tag_preparation()

        page._wordpress_tag_creation_completed = True

        page._on_wordpress_tag_creation_finished()

        assert page._wordpress_tag_creation_completed is True
        assert page._pending_publish_request is None
        assert page._preparing_wordpress_account is None
    finally:
        page.shutdown()


def test_wordpress_tag_creation_finished_accepted_during_active_workflow(qtbot):
    """An active successful creation may continue preparation."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        account = page.post_editor.destination_selector._accounts[0]

        page._pending_publish_request = object()
        page._preparing_wordpress_account = account
        page._wordpress_tag_creation_completed = True

        continued = []

        original_continue = page._continue_wordpress_tag_preparation

        page._continue_wordpress_tag_preparation = (
            lambda: continued.append(True)
        )

        page._on_wordpress_tag_creation_finished()

        assert continued == [True]
        assert page._preparing_wordpress_account is None
        assert page._wordpress_tag_creation_completed is False

        page._continue_wordpress_tag_preparation = original_continue
    finally:
        page.shutdown()

def test_wordpress_creation_worker_keeps_publishing_busy_after_cancellation(
    qtbot,
    monkeypatch,
):
    """Cancellation must not hide a still-running creation worker."""
    from types import SimpleNamespace

    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        page._cancel_wordpress_tag_preparation()

        with monkeypatch.context() as patch:
            patch.setattr(
                page,
                "_wordpress_tag_creation_controller",
                SimpleNamespace(is_running=True),
            )

            assert page._pending_publish_request is None
            assert page._publishing_workflow_is_busy() is True
    finally:
        page.shutdown()


def test_wordpress_creation_idle_after_cancellation_when_workers_idle(
    qtbot,
    monkeypatch,
):
    """Cancellation releases the workflow when all workers are idle."""
    from types import SimpleNamespace

    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        page._cancel_wordpress_tag_preparation()

        with monkeypatch.context() as patch:
            patch.setattr(
                page,
                "_wordpress_tag_creation_controller",
                SimpleNamespace(is_running=False),
            )
            patch.setattr(
                page,
                "_wordpress_tag_preparation_controller",
                SimpleNamespace(is_running=False),
            )
            patch.setattr(
                page,
                "_publishing_controller",
                SimpleNamespace(is_running=False),
            )

            assert page._pending_publish_request is None
            assert page._publishing_workflow_is_busy() is False
    finally:
        page.shutdown()


def test_publish_progress_ignored_after_shutdown(qtbot):
    """Late progress must not update the status after shutdown."""
    from typing import cast

    from socialflow.application.publishing.publish_result import PublishResult

    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        page.shutdown()

        original_status = page.publish_status.text()
        original_completed = page._publishing_completed

        # The shutdown guard must return before accessing the result.
        result = cast(PublishResult, object())

        page._on_publish_progress(result)

        assert page._publishing_completed == original_completed
        assert page.publish_status.text() == original_status
    finally:
        page.shutdown()


def test_publish_results_ignored_after_shutdown(qtbot):
    """Late results must not change publishing state."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        page.shutdown()

        original_results = page._last_publish_results
        original_status = page.publish_status.text()

        page._on_publish_results(())

        assert page._last_publish_results is original_results
        assert page.publish_status.text() == original_status
    finally:
        page.shutdown()


def test_publish_error_ignored_after_shutdown(qtbot):
    """Late errors must not clear publishing state."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        page.shutdown()

        original_request = page._last_publish_request
        original_results = page._last_publish_results
        original_status = page.publish_status.text()

        page._on_publish_error("Delayed publishing error")

        assert page._last_publish_request is original_request
        assert page._last_publish_results is original_results
        assert page.publish_status.text() == original_status
    finally:
        page.shutdown()


def test_publishing_finished_ignored_after_shutdown(qtbot):
    """Late completion must not re-enable publishing controls."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        page.shutdown()

        page.post_editor.publish_button.setEnabled(False)

        page._on_publishing_finished()

        assert page.post_editor.publish_button.isEnabled() is False
    finally:
        page.shutdown()

def test_publish_progress_accepted_before_shutdown(qtbot):
    """Publishing progress increments the counter while the page is active."""
    from socialflow.application.publishing.publish_result import PublishResult

    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        account = page.post_editor.destination_selector._accounts[0]
        result = PublishResult(account=account, succeeded=True)

        original_completed = page._publishing_completed

        page._on_publish_progress(result)

        assert page._publishing_completed == original_completed + 1
    finally:
        page.shutdown()


def test_publish_results_accepted_before_shutdown(qtbot):
    """Publishing results are stored while the page is active."""
    from socialflow.application.publishing.publish_result import PublishResult

    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        account = page.post_editor.destination_selector._accounts[0]
        result = PublishResult(account=account, succeeded=True)

        page._on_publish_results((result,))

        assert page._last_publish_results == (result,)
    finally:
        page.shutdown()


def test_publish_error_accepted_before_shutdown(qtbot):
    """Publishing errors update the status while the page is active."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        page._on_publish_error("Simulated publishing failure")

        assert page.publish_status.text() == "Publish request failed."
    finally:
        page.shutdown()


def test_publishing_finished_accepted_before_shutdown(qtbot):
    """Publishing completion restores the publish button."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        page.post_editor.publish_button.setEnabled(False)

        page._on_publishing_finished()

        assert page.post_editor.publish_button.isEnabled() is True
    finally:
        page.shutdown()


def test_publish_progress_accepted_when_worker_is_idle(qtbot, monkeypatch):
    """Queued progress remains valid after the worker stops."""
    from socialflow.application.publishing.publish_result import PublishResult

    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        account = page.post_editor.destination_selector._accounts[0]
        result = PublishResult(account=account, succeeded=True)

        with monkeypatch.context() as patch:
            patch.setattr(
                type(page._publishing_controller),
                "is_running",
                property(lambda self: False),
            )

            original_completed = page._publishing_completed

            page._on_publish_progress(result)

            assert page._publishing_completed == original_completed + 1
            assert account.name in page.publish_status.text()
    finally:
        page.shutdown()


def test_publish_error_accepted_when_worker_is_idle(qtbot, monkeypatch):
    """Queued errors remain valid after the worker stops."""
    page = create_posts_page()
    qtbot.addWidget(page)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(
                type(page._publishing_controller),
                "is_running",
                property(lambda self: False),
            )

            page._on_publish_error("Queued publishing error")

            assert page.publish_status.text() == "Publish request failed."
            assert page._last_publish_request is None
            assert page._last_publish_results == ()
    finally:
        page.shutdown()


def test_posts_page_recovers_across_success_failure_success_sequence(
    qtbot,
) -> None:
    """Consecutive operations reset UI state after an unexpected failure."""
    from unittest.mock import patch

    repository = InMemoryAccountRepository()
    repository.add(
        Account(
            name="Main Facebook",
            destination=PublishingDestination.FACEBOOK,
        )
    )

    publisher = RecordingPublisher()
    list_tags, create_tag = create_tag_services()

    publish_post = PublishPost(
        publisher_router=PublisherRouter(
            {
                PublishingDestination.FACEBOOK: publisher,
            }
        ),
        publication_id_generator=create_publication_id_generator(),
    )

    original_execute = publish_post.execute
    attempts = 0

    def execute(request, *, on_progress=None):
        nonlocal attempts
        attempts += 1

        if attempts == 2:
            raise RuntimeError("Unexpected second-operation failure")

        return original_execute(
            request,
            on_progress=on_progress,
        )

    page = PostsPage(
        publish_post=publish_post,
        list_accounts=ListAccounts(repository),
        list_tags=list_tags,
        create_tag=create_tag,
        list_recent_publications=create_list_recent_publications(),
    )
    qtbot.addWidget(page)

    page.post_editor.text_editor.setPlainText(
        "Consecutive publishing recovery"
    )
    page.post_editor.destination_selector._checkboxes[0].setChecked(True)

    try:
        with patch.object(publish_post, "execute", side_effect=execute):
            # First operation succeeds.
            with qtbot.waitSignal(page.publishing_finished, timeout=5000):
                page.post_editor.publish_button.click()

            assert attempts == 1
            assert len(publisher.published_posts) == 1
            assert page.post_editor.publish_button.isEnabled()
            assert not page.retry_failed_button.isEnabled()
            assert len(page._last_publish_results) == 1
            assert page._last_publish_results[0].succeeded

            # Second operation encounters an unexpected worker error.
            with qtbot.waitSignal(page.publishing_finished, timeout=5000):
                page.post_editor.publish_button.click()

            assert attempts == 2
            assert len(publisher.published_posts) == 1
            assert page._last_publish_request is None
            assert page._last_publish_results == ()
            assert not page.retry_failed_button.isEnabled()
            assert page.post_editor.publish_button.isEnabled()
            assert page.publish_status.property("status") == "error"

            # Third operation succeeds without recreating PostsPage.
            with qtbot.waitSignal(page.publishing_finished, timeout=5000):
                page.post_editor.publish_button.click()

            assert attempts == 3
            assert len(publisher.published_posts) == 2
            assert page.post_editor.publish_button.isEnabled()
            assert not page.retry_failed_button.isEnabled()
            assert len(page._last_publish_results) == 1
            assert page._last_publish_results[0].succeeded
            assert not page.publishing_is_running
    finally:
        page.shutdown()


def test_new_publishing_operation_clears_previous_retry_state(
    qtbot,
) -> None:
    """Starting a new operation must invalidate the previous retry action."""
    from unittest.mock import Mock

    page = create_posts_page()
    qtbot.addWidget(page)

    previous_request = Mock()
    previous_result = Mock()
    previous_result.succeeded = False

    page._last_publish_request = previous_request
    page._last_publish_results = (previous_result,)
    page.retry_failed_button.setEnabled(True)

    assert page.retry_failed_button.isEnabled()

    new_request = Mock()
    new_request.accounts = (Mock(),)

    page._publishing_controller.start = Mock()

    try:
        page._start_publishing(new_request)

        assert not page.retry_failed_button.isEnabled()
        assert page._publishing_completed == 0
        assert page._publishing_total == 1

        page._publishing_controller.start.assert_called_once_with(
            new_request
        )
    finally:
        page.shutdown()


def test_new_request_replaces_retry_context_before_wordpress_preparation(
    qtbot,
    monkeypatch,
) -> None:
    """A fresh request replaces stale retry data before preparation begins."""
    page = create_posts_page()
    qtbot.addWidget(page)

    previous_request = Mock()
    previous_result = Mock()

    new_request = Mock()

    page._last_publish_request = previous_request
    page._last_publish_results = (previous_result,)
    page.retry_failed_button.setEnabled(True)

    observed_state = []

    def capture_preparation(request):
        observed_state.append(
            (
                request,
                page._last_publish_request,
                page._last_publish_results,
            )
        )

    monkeypatch.setattr(
        page,
        "_begin_wordpress_tag_preparation",
        capture_preparation,
    )

    try:
        page._handle_publish_request(new_request)

        assert observed_state == [
            (new_request, new_request, ()),
        ]
        assert page._last_publish_request is new_request
        assert page._last_publish_results == ()
    finally:
        page.shutdown()


def test_busy_workflow_preserves_existing_retry_context(
    qtbot,
    monkeypatch,
) -> None:
    """A request rejected during active preparation must not replace state."""
    page = create_posts_page()
    qtbot.addWidget(page)

    existing_request = Mock()
    existing_result = Mock()
    rejected_request = Mock()

    page._last_publish_request = existing_request
    page._last_publish_results = (existing_result,)

    preparation = Mock()

    monkeypatch.setattr(
        page,
        "_publishing_workflow_is_busy",
        lambda: True,
    )
    monkeypatch.setattr(
        page,
        "_begin_wordpress_tag_preparation",
        preparation,
    )

    try:
        page._handle_publish_request(rejected_request)

        assert page._last_publish_request is existing_request
        assert page._last_publish_results == (existing_result,)
        preparation.assert_not_called()
    finally:
        page.shutdown()


def test_retry_replaces_active_context_before_wordpress_preparation(
    qtbot,
    monkeypatch,
) -> None:
    """Retry preparation receives the new active request, not the old one."""
    page = create_posts_page()
    qtbot.addWidget(page)

    previous_request = Mock()
    previous_result = Mock()
    retry_request = Mock()

    page._last_publish_request = previous_request
    page._last_publish_results = (previous_result,)

    observed_state = []

    def capture_preparation(request):
        observed_state.append(
            (
                request,
                page._last_publish_request,
                page._last_publish_results,
            )
        )

    monkeypatch.setattr(
        page,
        "_build_failed_retry_request",
        lambda: retry_request,
    )
    monkeypatch.setattr(
        page,
        "_begin_wordpress_tag_preparation",
        capture_preparation,
    )

    try:
        page._retry_failed_publications()

        assert observed_state == [
            (retry_request, retry_request, ()),
        ]
        assert page._last_publish_request is retry_request
        assert page._last_publish_results == ()
    finally:
        page.shutdown()


def test_retry_without_failed_accounts_preserves_existing_context(
    qtbot,
    monkeypatch,
) -> None:
    """An unavailable retry must not start preparation or alter state."""
    page = create_posts_page()
    qtbot.addWidget(page)

    previous_request = Mock()
    previous_result = Mock()

    page._last_publish_request = previous_request
    page._last_publish_results = (previous_result,)

    preparation = Mock()

    monkeypatch.setattr(
        page,
        "_build_failed_retry_request",
        lambda: None,
    )
    monkeypatch.setattr(
        page,
        "_begin_wordpress_tag_preparation",
        preparation,
    )

    try:
        page._retry_failed_publications()

        assert page._last_publish_request is previous_request
        assert page._last_publish_results == (previous_result,)
        preparation.assert_not_called()
    finally:
        page.shutdown()


def test_pending_wordpress_preparation_blocks_new_publish_request(
    qtbot,
    monkeypatch,
) -> None:
    """An active preparation request cannot be replaced by another publish."""
    page = create_posts_page()
    qtbot.addWidget(page)

    pending_request = Mock()
    replacement_request = Mock()

    page._pending_publish_request = pending_request
    page._last_publish_request = pending_request
    page._last_publish_results = ()

    preparation = Mock()
    monkeypatch.setattr(
        page,
        "_begin_wordpress_tag_preparation",
        preparation,
    )

    try:
        assert page._publishing_workflow_is_busy()

        page._handle_publish_request(replacement_request)

        assert page._pending_publish_request is pending_request
        assert page._last_publish_request is pending_request
        assert page._last_publish_results == ()

        preparation.assert_not_called()
    finally:
        page.shutdown()


def test_cancelled_wordpress_preparation_cannot_resume_publishing(
    qtbot,
    monkeypatch,
) -> None:
    """A late preparation-finished callback cannot publish a cancelled request."""
    page = create_posts_page()
    qtbot.addWidget(page)

    pending_request = Mock()
    pending_account = Mock()

    page._pending_publish_request = pending_request
    page._pending_wordpress_accounts = [pending_account]
    page._preparing_wordpress_account = pending_account

    start_publishing = Mock()
    monkeypatch.setattr(
        page,
        "_start_publishing",
        start_publishing,
    )

    try:
        page._cancel_wordpress_tag_preparation()

        assert page._pending_publish_request is None
        assert page._pending_wordpress_accounts == []
        assert page._preparing_wordpress_account is None

        # Simulate the preparation worker's completion arriving
        # after the user has cancelled the operation.
        page._on_wordpress_tag_preparation_finished()

        start_publishing.assert_not_called()
        assert page._pending_publish_request is None
    finally:
        page.shutdown()


def test_cancelled_wordpress_preparation_restores_page_state(
    qtbot,
    monkeypatch,
) -> None:
    """Cancellation clears preparation state and restores publishing controls."""
    page = create_posts_page()
    qtbot.addWidget(page)

    pending_request = Mock()
    pending_account = Mock()

    page._pending_publish_request = pending_request
    page._pending_wordpress_accounts = [pending_account]
    page._approved_wordpress_tag_plans["previous"] = Mock()
    page._preparing_wordpress_account = pending_account

    page._wordpress_tag_creation_completed = True
    page._wordpress_tag_creation_failed = True

    page.post_editor.publish_button.setEnabled(False)
    page.retry_failed_button.setEnabled(False)

    monkeypatch.setattr(
        page,
        "_build_failed_retry_request",
        lambda: None,
    )

    try:
        page._cancel_wordpress_tag_preparation()

        assert page._pending_publish_request is None
        assert page._pending_wordpress_accounts == []
        assert page._approved_wordpress_tag_plans == {}
        assert page._preparing_wordpress_account is None

        assert not page._wordpress_tag_creation_completed
        assert not page._wordpress_tag_creation_failed

        assert page.post_editor.publish_button.isEnabled()
        assert not page.retry_failed_button.isEnabled()
    finally:
        page.shutdown()


def test_fresh_request_is_accepted_after_cancelled_wordpress_preparation(
    qtbot,
    monkeypatch,
) -> None:
    """Cancellation allows a new request to replace the previous context."""
    page = create_posts_page()
    qtbot.addWidget(page)

    cancelled_request = Mock()
    fresh_request = Mock()

    page._pending_publish_request = cancelled_request
    page._last_publish_request = cancelled_request
    page._last_publish_results = (Mock(),)

    preparation = Mock()

    monkeypatch.setattr(
        page,
        "_begin_wordpress_tag_preparation",
        preparation,
    )
    monkeypatch.setattr(
        page,
        "_build_failed_retry_request",
        lambda: None,
    )

    try:
        page._cancel_wordpress_tag_preparation()

        assert not page._publishing_workflow_is_busy()

        # A delayed completion from the cancelled operation
        # must not restart publishing.
        page._on_wordpress_tag_preparation_finished()

        page._handle_publish_request(fresh_request)

        assert page._last_publish_request is fresh_request
        assert page._last_publish_results == ()
        preparation.assert_called_once_with(fresh_request)
    finally:
        page.shutdown()


def test_posts_page_has_three_sub_tabs(qtbot) -> None:
    page = create_posts_page()
    qtbot.addWidget(page)

    assert page.posts_tabs.count() == 3

    assert page.posts_tabs.tabText(0) == "Create Post"
    assert page.posts_tabs.tabText(1) == "My Posts"
    assert page.posts_tabs.tabText(2) == "Trash"

    assert page.posts_tabs.widget(0) is page.create_post_view
    assert page.posts_tabs.widget(1) is page.my_posts_view
    assert page.posts_tabs.widget(2) is page.trash_view

    assert page.posts_tabs.currentWidget() is page.create_post_view