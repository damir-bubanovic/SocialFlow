
from PySide6.QtWidgets import QLineEdit

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.instagram_account_config import (
    InstagramAccountConfig,
)
from socialflow.modules.accounts.views.account_form import AccountForm


def select_platform(
    form: AccountForm,
    destination: PublishingDestination,
) -> None:
    index = form.destination_input.findData(destination)
    assert index >= 0
    form.destination_input.setCurrentIndex(index)


def test_instagram_fields_exist(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    assert isinstance(form.instagram_user_id_input, QLineEdit)
    assert isinstance(form.instagram_username_input, QLineEdit)
    assert isinstance(form.instagram_access_token_input, QLineEdit)


def test_instagram_fields_visible_for_instagram(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)
    form.show()

    select_platform(form, PublishingDestination.INSTAGRAM)

    assert form.instagram_user_id_input.isVisible()
    assert form.instagram_username_input.isVisible()
    assert form.instagram_access_token_input.isVisible()
    assert not form.facebook_page_id_input.isVisible()
    assert not form.wordpress_site_url_input.isVisible()


def test_instagram_fields_hidden_for_other_platforms(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)
    form.show()

    for destination in (
        PublishingDestination.FACEBOOK,
        PublishingDestination.WORDPRESS,
    ):
        select_platform(form, destination)

        assert not form.instagram_user_id_input.isVisible()
        assert not form.instagram_username_input.isVisible()
        assert not form.instagram_access_token_input.isVisible()


def test_instagram_config_normalizes_input(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.instagram_user_id_input.setText(" 17841400000000000 ")
    form.instagram_username_input.setText(" example_user ")

    assert form.instagram_account_config() == InstagramAccountConfig(
        instagram_user_id="17841400000000000",
        username="example_user",
    )


def test_instagram_account_contains_config_but_not_token(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    select_platform(form, PublishingDestination.INSTAGRAM)
    form.name_input.setText("My Instagram")
    form.instagram_user_id_input.setText("17841400000000000")
    form.instagram_username_input.setText("example_user")
    form.instagram_access_token_input.setText("SECRET_TEST_TOKEN")

    account = form.account()

    assert account.destination == PublishingDestination.INSTAGRAM
    assert account.instagram_config == InstagramAccountConfig(
        instagram_user_id="17841400000000000",
        username="example_user",
    )
    assert account.facebook_config is None
    assert account.wordpress_config is None
    assert "SECRET_TEST_TOKEN" not in repr(account)


def test_non_instagram_account_has_no_instagram_config(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.instagram_user_id_input.setText("12345")
    select_platform(form, PublishingDestination.FACEBOOK)

    assert form.account().instagram_config is None


def test_load_instagram_account(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    account = Account(
        name="My Instagram",
        destination=PublishingDestination.INSTAGRAM,
        instagram_config=InstagramAccountConfig(
            instagram_user_id="12345",
            username="example_user",
        ),
    )

    form.set_account(account)

    assert form.instagram_user_id_input.text() == "12345"
    assert form.instagram_username_input.text() == "example_user"
    assert form.instagram_access_token_input.text() == ""


def test_switching_accounts_clears_instagram_values(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    instagram = Account(
        name="Instagram",
        destination=PublishingDestination.INSTAGRAM,
        instagram_config=InstagramAccountConfig(
            instagram_user_id="12345",
            username="example_user",
        ),
    )
    facebook = Account(
        name="Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    form.set_account(instagram)
    form.instagram_access_token_input.setText("SECRET_TEST_TOKEN")
    form.set_account(facebook)

    assert form.instagram_user_id_input.text() == ""
    assert form.instagram_username_input.text() == ""
    assert form.instagram_access_token_input.text() == ""


def test_clear_resets_instagram_fields(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    select_platform(form, PublishingDestination.INSTAGRAM)
    form.instagram_user_id_input.setText("12345")
    form.instagram_username_input.setText("example_user")
    form.instagram_access_token_input.setText("SECRET_TEST_TOKEN")

    form.clear()

    assert form.instagram_user_id_input.text() == ""
    assert form.instagram_username_input.text() == ""
    assert form.instagram_access_token_input.text() == ""
    assert form.selected_destination() is None


def test_instagram_access_token_is_masked(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    assert (
        form.instagram_access_token_input.echoMode()
        == QLineEdit.EchoMode.Password
    )


def test_instagram_access_token_accessor(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    form.instagram_access_token_input.setText("SECRET_TEST_TOKEN")

    assert form.instagram_access_token() == "SECRET_TEST_TOKEN"


def test_switching_platform_clears_instagram_token(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    select_platform(form, PublishingDestination.INSTAGRAM)
    form.instagram_access_token_input.setText("SECRET_TEST_TOKEN")

    select_platform(form, PublishingDestination.WORDPRESS)

    assert form.instagram_access_token() == ""


def test_loading_account_clears_previous_instagram_token(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    select_platform(form, PublishingDestination.INSTAGRAM)
    form.instagram_access_token_input.setText("SECRET_TEST_TOKEN")

    account = Account(
        name="Another Instagram",
        destination=PublishingDestination.INSTAGRAM,
        instagram_config=InstagramAccountConfig(
            instagram_user_id="67890",
            username="another_user",
        ),
    )

    form.set_account(account)

    assert form.instagram_user_id_input.text() == "67890"
    assert form.instagram_username_input.text() == "another_user"
    assert form.instagram_access_token() == ""


def test_instagram_config_completeness(qtbot) -> None:
    form = AccountForm()
    qtbot.addWidget(form)

    assert not form.instagram_account_config().is_complete()

    form.instagram_user_id_input.setText("12345")

    assert form.instagram_account_config().is_complete()
