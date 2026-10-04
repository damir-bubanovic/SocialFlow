from PySide6.QtWidgets import QPushButton

from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.application.accounts.add_account import AddAccount
from socialflow.application.accounts.list_accounts import ListAccounts
from socialflow.domain.account.account import Account
from socialflow.ui.accounts.account_form import AccountForm
from socialflow.ui.accounts.account_list import AccountList
from socialflow.ui.accounts.accounts_page import AccountsPage
from socialflow.ui.accounts.account_status import AccountStatus
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.application.accounts.remove_account import RemoveAccount


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

class MissingAccountRepository(InMemoryAccountRepository):
    """Test repository that reports no accounts during removal."""

    def all(self) -> tuple[Account, ...]:
        return ()

def create_accounts_page() -> AccountsPage:
    repository = InMemoryAccountRepository()

    return AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
    )


def test_accounts_page_contains_form_and_list(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    assert isinstance(page.account_form, AccountForm)
    assert isinstance(page.account_list, AccountList)


def test_accounts_page_adds_account(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("SocialFlow Facebook")
    page.account_form.add_button.click()

    assert page.account_list.count() == 1
    assert (
        page.account_list.item(0).text()
        == "SocialFlow Facebook - Facebook"
    )

def test_accounts_page_contains_account_status(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    assert isinstance(page.account_status, AccountStatus)


def test_accounts_page_shows_success_after_adding_account(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("SocialFlow Facebook")
    page.account_form.add_button.click()

    assert page.account_status.text() == "Account added."
    assert page.account_status.property("status") == "success"


def test_accounts_page_rejects_empty_account_name(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("   ")
    page.account_form.add_button.click()

    assert page.account_list.count() == 0
    assert page.account_status.text() == "Account could not be added."
    assert page.account_status.property("status") == "error"

def test_accounts_page_clears_form_after_adding_account(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("SocialFlow Instagram")
    page.account_form.destination_input.setCurrentIndex(1)

    page.account_form.add_button.click()

    assert page.account_form.name_input.text() == ""
    assert (
        page.account_form.selected_destination()
        == PublishingDestination.FACEBOOK
    )

def test_accounts_page_rejects_duplicate_account(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("SocialFlow Facebook")
    page.account_form.add_button.click()

    page.account_form.name_input.setText("SocialFlow Facebook")
    page.account_form.add_button.click()

    assert page.account_list.count() == 1
    assert page.account_status.text() == "Account could not be added."
    assert page.account_status.property("status") == "error"

def test_accounts_page_contains_remove_button(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    assert isinstance(page.remove_button, QPushButton)
    assert page.remove_button.text() == "Remove account"


def test_accounts_page_removes_selected_account(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("SocialFlow Facebook")
    page.account_form.add_button.click()

    page.account_list.setCurrentRow(0)
    page.remove_button.click()

    assert page.account_list.count() == 0


def test_accounts_page_ignores_remove_without_selection(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.remove_button.click()

    assert page.account_list.count() == 0

def test_remove_button_is_disabled_without_selection(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    assert not page.remove_button.isEnabled()


def test_remove_button_is_enabled_when_account_is_selected(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("SocialFlow Facebook")
    page.account_form.add_button.click()

    page.account_list.setCurrentRow(0)

    assert page.remove_button.isEnabled()

def test_accounts_page_shows_status_after_removing_account(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("SocialFlow Facebook")
    page.account_form.add_button.click()

    page.account_list.setCurrentRow(0)
    page.remove_button.click()

    assert page.account_status.text() == "Account removed."
    assert page.account_status.property("status") == "success"

def test_accounts_page_shows_error_when_account_cannot_be_removed(
    qtbot,
) -> None:
    repository = InMemoryAccountRepository()

    account = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(account)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
    )
    qtbot.addWidget(page)

    page.account_list.setCurrentRow(0)

    repository.remove(account)
    page.remove_button.click()

    assert page.account_status.text() == "Account could not be removed."
    assert page.account_status.property("status") == "error"