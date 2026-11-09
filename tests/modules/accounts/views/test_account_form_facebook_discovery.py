
from unittest.mock import Mock

from PySide6.QtWidgets import QLineEdit

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.views.account_form import AccountForm
from socialflow.modules.facebook.models.discovered_facebook_page import (
    DiscoveredFacebookPage,
)
from socialflow.modules.facebook.models.facebook_page import (
    FacebookPage,
)


def select_facebook(form: AccountForm) -> None:
    index = form.destination_input.findData(
        PublishingDestination.FACEBOOK
    )
    form.destination_input.setCurrentIndex(index)


def create_pages() -> list[DiscoveredFacebookPage]:
    return [
        DiscoveredFacebookPage(
            page=FacebookPage(id="123", name="First Page"),
            access_token="first-secret-page-token",
        ),
        DiscoveredFacebookPage(
            page=FacebookPage(id="456", name="Second Page"),
            access_token="second-secret-page-token",
        ),
    ]


def test_discovery_controls_visible_for_facebook(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)
    form.show()

    select_facebook(form)

    assert form.facebook_user_token_input.isVisible()
    assert form.facebook_discover_button.isVisible()
    assert form.facebook_page_selector.isVisible()


def test_discovery_controls_hidden_for_wordpress(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)
    form.show()

    index = form.destination_input.findData(
        PublishingDestination.WORDPRESS
    )
    form.destination_input.setCurrentIndex(index)

    assert not form.facebook_user_token_input.isVisible()
    assert not form.facebook_discover_button.isVisible()
    assert not form.facebook_page_selector.isVisible()


def test_user_token_is_masked(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    assert (
        form.facebook_user_token_input.echoMode()
        == QLineEdit.EchoMode.Password
    )


def test_discovery_emits_token_and_clears_input(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    listener = Mock()
    form.facebook_discovery_requested.connect(listener)

    form.facebook_user_token_input.setText(
        "sensitive-user-token"
    )
    form.facebook_discover_button.click()

    listener.assert_called_once_with("sensitive-user-token")
    assert form.facebook_user_token_input.text() == ""
    assert not form.facebook_discover_button.isEnabled()


def test_empty_token_does_not_request_discovery(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    listener = Mock()
    form.facebook_discovery_requested.connect(listener)

    form.facebook_discover_button.click()

    listener.assert_not_called()


def test_discovered_pages_populate_selector(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.set_discovered_facebook_pages(create_pages())

    assert form.facebook_page_selector.count() == 3
    assert form.facebook_page_selector.itemText(1) == "First Page"
    assert form.facebook_page_selector.itemText(2) == "Second Page"
    assert form.facebook_page_selector.isEnabled()


def test_selecting_page_populates_configuration(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.set_discovered_facebook_pages(create_pages())
    form.facebook_page_selector.setCurrentIndex(2)

    assert form.facebook_page_id_input.text() == "456"
    assert form.facebook_page_name_input.text() == "Second Page"
    assert (
        form.selected_facebook_page_token()
        == "second-secret-page-token"
    )


def test_clear_discards_discovered_page_tokens(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.set_discovered_facebook_pages(create_pages())
    form.facebook_page_selector.setCurrentIndex(1)

    form.clear()

    assert form.selected_facebook_page_token() == ""
    assert form.facebook_page_selector.count() == 1
    assert not form.facebook_page_selector.isEnabled()


def test_switching_accounts_discards_page_tokens(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.set_discovered_facebook_pages(create_pages())
    form.facebook_page_selector.setCurrentIndex(1)

    form.set_account(
        Account(
            name="WordPress Account",
            destination=PublishingDestination.WORDPRESS,
        )
    )

    assert form.selected_facebook_page_token() == ""
    assert form.facebook_page_selector.count() == 1


def test_discovered_page_tokens_not_in_account_model(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    select_facebook(form)
    form.name_input.setText("Facebook Account")

    form.set_discovered_facebook_pages(create_pages())
    form.facebook_page_selector.setCurrentIndex(1)

    account = form.account()

    assert account.facebook_config is not None
    assert account.facebook_config.page_id == "123"
    assert account.facebook_config.page_name == "First Page"
    assert "first-secret-page-token" not in repr(account)



def test_manual_page_id_change_invalidates_selected_token(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.set_discovered_facebook_pages(create_pages())
    form.facebook_page_selector.setCurrentIndex(1)

    assert form.selected_facebook_page_token() == (
        "first-secret-page-token"
    )

    form.facebook_page_id_input.setText("different-page-id")

    assert form.selected_facebook_page_token() == ""


def test_page_name_change_preserves_selected_token(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.set_discovered_facebook_pages(create_pages())
    form.facebook_page_selector.setCurrentIndex(1)

    form.facebook_page_name_input.setText("Renamed Page")

    assert form.selected_facebook_page_token() == (
        "first-secret-page-token"
    )


def test_selecting_another_page_replaces_token(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.set_discovered_facebook_pages(create_pages())

    form.facebook_page_selector.setCurrentIndex(1)
    assert form.selected_facebook_page_token() == (
        "first-secret-page-token"
    )

    form.facebook_page_selector.setCurrentIndex(2)

    assert form.facebook_page_id_input.text() == "456"
    assert form.selected_facebook_page_token() == (
        "second-secret-page-token"
    )


def test_switching_away_from_facebook_discards_tokens(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    select_facebook(form)
    form.set_discovered_facebook_pages(create_pages())
    form.facebook_page_selector.setCurrentIndex(1)

    assert form.selected_facebook_page_token() == (
        "first-secret-page-token"
    )

    index = form.destination_input.findData(
        PublishingDestination.WORDPRESS
    )
    form.destination_input.setCurrentIndex(index)

    assert form.selected_facebook_page_token() == ""
    assert form.facebook_page_selector.count() == 1
    assert not form.facebook_page_selector.isEnabled()


def test_switching_away_clears_temporary_user_token(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    select_facebook(form)
    form.facebook_user_token_input.setText(
        "temporary-user-token"
    )

    index = form.destination_input.findData(
        PublishingDestination.INSTAGRAM
    )
    form.destination_input.setCurrentIndex(index)

    assert form.facebook_user_token_input.text() == ""