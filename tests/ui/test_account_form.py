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