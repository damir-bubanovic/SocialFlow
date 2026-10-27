import pytest
import json

from PySide6.QtWidgets import QStackedWidget, QWidget

from socialflow.ui.accounts.accounts_page import AccountsPage
from socialflow.ui.main_content import MainContent
from socialflow.ui.navigation import Navigation
from socialflow.ui.posts.posts_page import PostsPage
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.accounts.json_account_repository import (
    JsonAccountRepository,
)
from socialflow.infrastructure.publishing.json_publication_repository import (
    JsonPublicationRepository,
)
from socialflow.infrastructure.wordpress.wordpress_connection_verifier import (
    WordPressConnectionVerifier,
)
from socialflow.infrastructure.storage.app_paths import AppPaths
from socialflow.infrastructure.storage.data_directory import data_directory
from socialflow.infrastructure.wordpress.wordpress_publisher import (
    WordPressPublisher,
)
from socialflow.infrastructure.wordpress.urllib_wordpress_tag_client import (
    UrllibWordPressTagClient,
)
from socialflow.application.publishing.trash_remote_post import (
    TrashRemotePost,
)
from socialflow.infrastructure.wordpress.wordpress_post_trasher import (
    WordPressPostTrasher,
)


@pytest.fixture(autouse=True)
def isolate_socialflow_data(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(
        "XDG_DATA_HOME",
        str(tmp_path),
    )


def test_main_content_is_widget(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert isinstance(content, QWidget)


def test_main_content_contains_navigation(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert isinstance(content.navigation, Navigation)


def test_main_content_contains_page_stack(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert isinstance(content.pages, QStackedWidget)


def test_main_content_contains_posts_page(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert isinstance(content.posts_page, PostsPage)


def test_main_content_contains_accounts_page(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert isinstance(content.accounts_page, AccountsPage)


def test_posts_page_is_selected_by_default(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert content.pages.currentWidget() is content.posts_page


def test_accounts_navigation_shows_accounts_page(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    content.navigation.tab_bar.setCurrentIndex(
        Navigation.ACCOUNTS_INDEX
    )

    assert content.pages.currentWidget() is content.accounts_page


def test_posts_navigation_shows_posts_page(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    content.navigation.tab_bar.setCurrentIndex(
        Navigation.ACCOUNTS_INDEX
    )
    content.navigation.tab_bar.setCurrentIndex(
        Navigation.POSTS_INDEX
    )

    assert content.pages.currentWidget() is content.posts_page

def test_adding_account_refreshes_posts_page_accounts(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert (
        len(content.posts_page.post_editor.destination_selector._checkboxes)
        == 0
    )

    content.accounts_page.account_form.name_input.setText(
        "Main Facebook"
    )
    content.accounts_page.account_form.add_button.click()

    checkboxes = (
        content.posts_page.post_editor.destination_selector._checkboxes
    )

    assert len(checkboxes) == 1
    assert checkboxes[0].text() == "Main Facebook (Facebook)"

def test_updating_account_refreshes_posts_page_accounts(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    content.accounts_page.account_form.name_input.setText(
        "Main Facebook"
    )
    content.accounts_page.account_form.add_button.click()

    content.accounts_page.account_list.setCurrentRow(0)
    content.accounts_page.account_form.name_input.setText(
        "Updated Facebook"
    )
    content.accounts_page.update_button.click()

    checkboxes = (
        content.posts_page.post_editor.destination_selector._checkboxes
    )

    assert len(checkboxes) == 1
    assert checkboxes[0].text() == "Updated Facebook (Facebook)"


def test_removing_account_refreshes_posts_page_accounts(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    content.accounts_page.account_form.name_input.setText(
        "Main Facebook"
    )
    content.accounts_page.account_form.add_button.click()

    content.accounts_page.account_list.setCurrentRow(0)
    content.accounts_page.remove_button.click()

    assert (
        len(content.posts_page.post_editor.destination_selector._checkboxes)
        == 0
    )

def test_main_content_does_not_persist_unconfigured_publication(
    qtbot,
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "XDG_DATA_HOME",
        str(tmp_path),
    )

    paths = AppPaths(data_directory())

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    account_repository = JsonAccountRepository(
        paths.accounts_file
    )
    account_repository.add(account)

    content = MainContent()
    qtbot.addWidget(content)

    assert (
        len(
            content.posts_page
            .post_editor
            .destination_selector
            ._checkboxes
        )
        == 1
    )

    content.posts_page.post_editor.text_editor.setPlainText(
        "Persistent history test"
    )

    content.posts_page.post_editor.destination_selector._checkboxes[
        0
    ].setChecked(True)

    with qtbot.waitSignal(
            content.posts_page.publishing_finished,
            timeout=5000,
    ):
        content.posts_page.post_editor.publish_button.click()

    publication_repository = JsonPublicationRepository(
        paths.publications_file
    )

    publications = publication_repository.recent_for_account(
        account
    )

    assert publications == ()

def test_main_content_displays_unconfigured_publishing_error(
    qtbot,
) -> None:
    paths = AppPaths(data_directory())

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    account_repository = JsonAccountRepository(
        paths.accounts_file
    )
    account_repository.add(account)

    content = MainContent()
    qtbot.addWidget(content)

    editor = content.posts_page.post_editor

    editor.text_editor.setPlainText(
        "Testing unconfigured publishing"
    )

    editor.destination_selector._checkboxes[0].setChecked(True)

    with qtbot.waitSignal(
            content.posts_page.publishing_finished,
            timeout=5000,
    ):
        editor.publish_button.click()

    assert content.posts_page.publish_status.text() == (
        "Main Facebook — Failed: "
        "Publishing configuration needs attention."
    )

    assert (
        content.posts_page.publish_status.property("status")
        == "error"
    )

    publication_repository = JsonPublicationRepository(
        paths.publications_file
    )

    assert publication_repository.recent_for_account(account) == ()

def test_main_content_migrates_legacy_publications_on_startup(
    qtbot,
) -> None:
    paths = AppPaths(data_directory())

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    account_repository = JsonAccountRepository(
        paths.accounts_file
    )
    account_repository.add(account)

    legacy_publication = {
        "id": "12345678-1234-5678-1234-567812345678",
        "account": {
            "name": "Main Facebook",
            "destination": "facebook",
        },
        "post": {
            "text": "Legacy publication",
            "language": "EN",
        },
        "published_at": "2026-10-05T21:30:00",
    }

    paths.publications_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    paths.publications_file.write_text(
        json.dumps([legacy_publication]),
        encoding="utf-8",
    )

    # Initializing MainContent must trigger migration.
    content = MainContent()
    qtbot.addWidget(content)

    stored_publications = json.loads(
        paths.publications_file.read_text(
            encoding="utf-8",
        )
    )

    assert len(stored_publications) == 1

    assert (
        stored_publications[0]["account"]["id"]
        == str(account.id)
    )

    assert (
        stored_publications[0]["post"]["text"]
        == "Legacy publication"
    )

def test_main_content_initializes_wordpress_verifier(qtbot) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    assert isinstance(
        content.wordpress_connection_verifier,
        WordPressConnectionVerifier,
    )

def test_main_content_configures_wordpress_publisher_with_tag_client(
    qtbot,
) -> None:
    content = MainContent()
    qtbot.addWidget(content)

    account = Account(
        name="WordPress Tag Test",
        destination=PublishingDestination.WORDPRESS,
    )

    router = content.posts_page._publishing_controller._publish_post._publisher_router
    publisher = router.publisher_for_account(account)

    assert isinstance(publisher, WordPressPublisher)
    assert isinstance(
        publisher._tag_client,
        UrllibWordPressTagClient,
    )



def test_main_content_wires_wordpress_trash_controller(qtbot):
    content = MainContent()
    qtbot.addWidget(content)

    controller = (
        content.posts_page._remote_post_trashing_controller
    )

    assert controller is not None
    assert not controller.is_running


def test_main_content_trash_controller_uses_wordpress_trasher(qtbot):
    content = MainContent()
    qtbot.addWidget(content)

    controller = (
        content.posts_page._remote_post_trashing_controller
    )
    use_case = controller._trash_remote_post

    assert isinstance(use_case, TrashRemotePost)
    assert isinstance(
        use_case._trasher,
        WordPressPostTrasher,
    )
