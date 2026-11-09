
from PySide6.QtWidgets import QLineEdit

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.facebook_page_config import (
    FacebookPageConfig,
)
from socialflow.modules.accounts.views.account_form import AccountForm


def select_platform(
    form: AccountForm,
    destination: PublishingDestination,
) -> None:
    index = form.destination_input.findData(destination)
    assert index >= 0
    form.destination_input.setCurrentIndex(index)


def test_facebook_fields_exist(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    assert isinstance(form.facebook_page_id_input, QLineEdit)
    assert isinstance(form.facebook_page_name_input, QLineEdit)


def test_facebook_fields_visible_for_facebook(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)
    form.show()

    select_platform(form, PublishingDestination.FACEBOOK)

    assert form.facebook_page_id_input.isVisible()
    assert form.facebook_page_name_input.isVisible()
    assert not form.wordpress_site_url_input.isVisible()


def test_facebook_fields_hidden_for_wordpress(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)
    form.show()

    select_platform(form, PublishingDestination.WORDPRESS)

    assert not form.facebook_page_id_input.isVisible()
    assert not form.facebook_page_name_input.isVisible()
    assert form.wordpress_site_url_input.isVisible()


def test_facebook_fields_hidden_for_instagram(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)
    form.show()

    select_platform(form, PublishingDestination.INSTAGRAM)

    assert not form.facebook_page_id_input.isVisible()
    assert not form.facebook_page_name_input.isVisible()


def test_facebook_config_normalizes_input(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.facebook_page_id_input.setText(" 12345 ")
    form.facebook_page_name_input.setText(" My Page ")

    assert form.facebook_page_config() == FacebookPageConfig(
        page_id="12345",
        page_name="My Page",
    )


def test_account_contains_facebook_config(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    select_platform(form, PublishingDestination.FACEBOOK)
    form.name_input.setText("Facebook Account")
    form.facebook_page_id_input.setText("12345")
    form.facebook_page_name_input.setText("My Page")

    account = form.account()

    assert account.destination == PublishingDestination.FACEBOOK
    assert account.facebook_config == FacebookPageConfig(
        page_id="12345",
        page_name="My Page",
    )
    assert account.wordpress_config is None


def test_wordpress_account_has_no_facebook_config(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    select_platform(form, PublishingDestination.WORDPRESS)
    form.facebook_page_id_input.setText("12345")

    assert form.account().facebook_config is None


def test_load_facebook_account(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    account = Account(
        name="My Facebook",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="12345",
            page_name="My Page",
        ),
    )

    form.set_account(account)

    assert form.facebook_page_id_input.text() == "12345"
    assert form.facebook_page_name_input.text() == "My Page"


def test_switching_accounts_clears_previous_facebook_values(
    qtbot,
) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    facebook = Account(
        name="Facebook",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="12345",
            page_name="My Page",
        ),
    )
    wordpress = Account(
        name="WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    form.set_account(facebook)
    form.set_account(wordpress)

    assert form.facebook_page_id_input.text() == ""
    assert form.facebook_page_name_input.text() == ""


def test_clear_resets_facebook_fields(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    select_platform(form, PublishingDestination.FACEBOOK)
    form.facebook_page_id_input.setText("12345")
    form.facebook_page_name_input.setText("My Page")

    form.clear()

    assert form.facebook_page_id_input.text() == ""
    assert form.facebook_page_name_input.text() == ""
    assert form.selected_destination() is None
