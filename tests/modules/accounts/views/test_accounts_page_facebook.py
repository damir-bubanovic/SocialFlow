
from unittest.mock import Mock

from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.facebook_page_config import (
    FacebookPageConfig,
)
from socialflow.modules.accounts.repositories.in_memory_account_repository import (
    InMemoryAccountRepository,
)
from socialflow.modules.accounts.services.add_account import AddAccount

from socialflow.modules.accounts.services.list_accounts import ListAccounts
from socialflow.modules.accounts.services.remove_account import RemoveAccount
from socialflow.modules.accounts.services.update_account import UpdateAccount
from socialflow.modules.accounts.views.accounts_page import AccountsPage


def create_page(
    repository: InMemoryAccountRepository | None = None,
    **kwargs,
) -> tuple[AccountsPage, InMemoryAccountRepository]:
    if repository is None:
        repository = InMemoryAccountRepository()

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        **kwargs,
    )
    return page, repository


def select_platform(
    page: AccountsPage,
    destination: PublishingDestination,
) -> None:
    index = page.account_form.destination_input.findData(destination)
    assert index >= 0
    page.account_form.destination_input.setCurrentIndex(index)


def add_facebook_account(
    page: AccountsPage,
    *,
    name: str = "Facebook Main",
    page_id: str = "12345",
    page_name: str = "My Page",
) -> None:
    page.new_account_button.click()
    page.account_form.name_input.setText(name)
    select_platform(page, PublishingDestination.FACEBOOK)
    page.account_form.facebook_page_id_input.setText(page_id)
    page.account_form.facebook_page_name_input.setText(page_name)
    page.account_form.add_button.click()


def test_create_facebook_account_persists_page_config(qtbot) -> None:
    page, repository = create_page()
    qtbot.addWidget(page)

    add_facebook_account(
        page,
        name="  Facebook Main  ",
        page_id=" 12345 ",
        page_name=" My Page ",
    )

    assert page.account_list.count() == 1
    assert len(repository.all()) == 1

    account = repository.all()[0]
    assert account.name == "Facebook Main"
    assert account.destination == PublishingDestination.FACEBOOK
    assert account.facebook_config == FacebookPageConfig(
        page_id="12345",
        page_name="My Page",
    )
    assert account.wordpress_config is None


def test_selecting_facebook_account_restores_page_fields(qtbot) -> None:
    page, _ = create_page()
    qtbot.addWidget(page)

    add_facebook_account(page)

    page.account_list.setCurrentRow(0)

    assert page.account_form.facebook_page_id_input.text() == "12345"
    assert page.account_form.facebook_page_name_input.text() == "My Page"
    assert page.account_form.selected_destination() == (
        PublishingDestination.FACEBOOK
    )


def test_edit_facebook_account_updates_page_config(qtbot) -> None:
    page, repository = create_page()
    qtbot.addWidget(page)

    add_facebook_account(page)
    original_id = repository.all()[0].id

    page.account_list.setCurrentRow(0)
    page.account_form.facebook_page_id_input.setText(" 67890 ")
    page.account_form.facebook_page_name_input.setText(" Updated Page ")
    page.update_button.click()

    assert len(repository.all()) == 1

    account = repository.all()[0]
    assert account.id == original_id
    assert account.facebook_config == FacebookPageConfig(
        page_id="67890",
        page_name="Updated Page",
    )


def test_facebook_config_survives_account_list_refresh(qtbot) -> None:
    page, repository = create_page()
    qtbot.addWidget(page)

    add_facebook_account(page)

    page._refresh_accounts()
    page.account_list.setCurrentRow(0)

    assert repository.all()[0].facebook_config == FacebookPageConfig(
        page_id="12345",
        page_name="My Page",
    )
    assert page.account_form.facebook_page_id_input.text() == "12345"
    assert page.account_form.facebook_page_name_input.text() == "My Page"


def test_switch_wordpress_account_to_facebook(qtbot) -> None:
    page, repository = create_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("My Account")
    select_platform(page, PublishingDestination.WORDPRESS)
    page.account_form.add_button.click()

    original_id = repository.all()[0].id

    page.account_list.setCurrentRow(0)
    select_platform(page, PublishingDestination.FACEBOOK)
    page.account_form.facebook_page_id_input.setText("555")
    page.account_form.facebook_page_name_input.setText("New Page")
    page.update_button.click()

    account = repository.all()[0]
    assert account.id == original_id
    assert account.destination == PublishingDestination.FACEBOOK
    assert account.facebook_config == FacebookPageConfig(
        page_id="555",
        page_name="New Page",
    )
    assert account.wordpress_config is None


def test_switch_facebook_account_to_wordpress_clears_config(
    qtbot,
) -> None:
    page, repository = create_page()
    qtbot.addWidget(page)

    add_facebook_account(page)

    page.account_list.setCurrentRow(0)
    select_platform(page, PublishingDestination.WORDPRESS)
    page.update_button.click()

    account = repository.all()[0]
    assert account.destination == PublishingDestination.WORDPRESS
    assert account.facebook_config is None


def test_new_account_mode_clears_facebook_fields(qtbot) -> None:
    page, _ = create_page()
    qtbot.addWidget(page)

    add_facebook_account(page)
    page.account_list.setCurrentRow(0)

    page.new_account_button.click()

    assert page.account_form.facebook_page_id_input.text() == ""
    assert page.account_form.facebook_page_name_input.text() == ""
    assert page.account_form.selected_destination() is None


def test_facebook_creation_does_not_save_wordpress_credentials(
    qtbot,
) -> None:
    save_credentials = Mock()
    page, _ = create_page(
        save_wordpress_credentials=save_credentials,
    )
    qtbot.addWidget(page)

    add_facebook_account(page)

    save_credentials.execute.assert_not_called()


def test_facebook_update_does_not_save_wordpress_credentials(
    qtbot,
) -> None:
    save_credentials = Mock()
    page, _ = create_page(
        save_wordpress_credentials=save_credentials,
    )
    qtbot.addWidget(page)

    add_facebook_account(page)
    page.account_list.setCurrentRow(0)
    page.account_form.facebook_page_name_input.setText("Updated")
    page.update_button.click()

    save_credentials.execute.assert_not_called()


def test_facebook_to_wordpress_conversion_does_not_delete_wordpress_credentials(
    qtbot,
) -> None:
    delete_credentials = Mock()
    page, _ = create_page(
        delete_wordpress_credentials=delete_credentials,
    )
    qtbot.addWidget(page)

    add_facebook_account(page)
    page.account_list.setCurrentRow(0)
    select_platform(page, PublishingDestination.WORDPRESS)
    page.update_button.click()

    delete_credentials.execute.assert_not_called()


def test_facebook_account_emits_accounts_changed_on_create_and_update(
    qtbot,
) -> None:
    page, _ = create_page()
    qtbot.addWidget(page)

    with qtbot.waitSignal(page.accounts_changed, timeout=1000):
        add_facebook_account(page)

    page.account_list.setCurrentRow(0)

    with qtbot.waitSignal(page.accounts_changed, timeout=1000):
        page.account_form.facebook_page_name_input.setText("Updated")
        page.update_button.click()


def test_facebook_account_can_be_removed(qtbot) -> None:
    page, repository = create_page()
    qtbot.addWidget(page)

    add_facebook_account(page)
    page.account_list.setCurrentRow(0)
    page.remove_button.click()

    assert repository.all() == ()
    assert page.account_list.count() == 0
