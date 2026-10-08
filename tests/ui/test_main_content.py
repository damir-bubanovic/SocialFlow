import pytest

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
from socialflow.infrastructure.storage.app_paths import AppPaths
from socialflow.infrastructure.storage.data_directory import data_directory


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

    editor.publish_button.click()

    assert content.posts_page.publish_status.text() == (
        "Main Facebook — Failed: "
        "External publishing is not configured."
    )

    assert (
        content.posts_page.publish_status.property("status")
        == "error"
    )

    publication_repository = JsonPublicationRepository(
        paths.publications_file
    )

    assert publication_repository.recent_for_account(account) == ()