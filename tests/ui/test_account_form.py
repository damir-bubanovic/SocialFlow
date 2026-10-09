from PySide6.QtWidgets import QComboBox, QLineEdit, QPushButton

from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.ui.accounts.account_form import AccountForm


def test_account_form_contains_expected_controls(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    assert isinstance(form.name_input, QLineEdit)
    assert isinstance(form.destination_input, QComboBox)
    assert isinstance(form.add_button, QPushButton)


def test_account_form_defaults_to_facebook(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    assert form.selected_destination() == PublishingDestination.FACEBOOK


def test_account_form_returns_account(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.name_input.setText("SocialFlow Instagram")
    form.destination_input.setCurrentIndex(1)

    account = form.account()

    assert isinstance(account, Account)
    assert account.name == "SocialFlow Instagram"
    assert account.destination == PublishingDestination.INSTAGRAM

def test_account_form_can_be_cleared(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.name_input.setText("SocialFlow Instagram")
    form.destination_input.setCurrentIndex(1)

    form.clear()

    assert form.name_input.text() == ""
    assert form.selected_destination() == PublishingDestination.FACEBOOK

def test_account_form_can_load_account(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    account = Account(
        name="SocialFlow WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    form.set_account(account)

    assert form.name_input.text() == "SocialFlow WordPress"
    assert (
        form.selected_destination()
        == PublishingDestination.WORDPRESS
    )


from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.accounts.account_form import AccountForm


def test_wordpress_fields_are_hidden_for_facebook(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)
    form.show()

    assert not form.wordpress_site_url_input.isVisible()
    assert not form.wordpress_username_input.isVisible()


def test_wordpress_fields_are_visible_for_wordpress(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)
    form.show()

    index = form.destination_input.findData(
        PublishingDestination.WORDPRESS
    )
    form.destination_input.setCurrentIndex(index)

    assert form.wordpress_site_url_input.isVisible()
    assert form.wordpress_username_input.isVisible()


def test_wordpress_connection_config_normalizes_input(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.wordpress_site_url_input.setText(
        "  https://example.com/  "
    )
    form.wordpress_username_input.setText("  admin  ")

    config = form.wordpress_connection_config()

    assert config.site_url == "https://example.com"
    assert config.username == "admin"


def test_account_form_clear_resets_wordpress_fields(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.wordpress_site_url_input.setText(
        "https://example.com"
    )
    form.wordpress_username_input.setText("admin")

    form.clear()

    assert form.wordpress_site_url_input.text() == ""
    assert form.wordpress_username_input.text() == ""


def test_wordpress_application_password_is_masked(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    assert (
        form.wordpress_application_password_input.echoMode()
        == QLineEdit.EchoMode.Password
    )


def test_wordpress_application_password_is_readable_by_form(
    qtbot,
) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.wordpress_application_password_input.setText(
        "test-application-password"
    )

    assert (
        form.wordpress_application_password()
        == "test-application-password"
    )


def test_wordpress_application_password_is_cleared(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.wordpress_application_password_input.setText(
        "test-application-password"
    )

    form.clear()

    assert form.wordpress_application_password() == ""


def test_wordpress_application_password_is_hidden_for_facebook(
    qtbot,
) -> None:
    form = AccountForm()
    qtbot.addWidget(form)
    form.show()

    assert not form.wordpress_application_password_input.isVisible()


def test_wordpress_application_password_is_visible_for_wordpress(
    qtbot,
) -> None:
    form = AccountForm()
    qtbot.addWidget(form)
    form.show()

    index = form.destination_input.findData(
        PublishingDestination.WORDPRESS
    )
    form.destination_input.setCurrentIndex(index)

    assert form.wordpress_application_password_input.isVisible()
