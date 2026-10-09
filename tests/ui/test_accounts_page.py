from PySide6.QtWidgets import QPushButton
from unittest.mock import Mock
import pytest

from socialflow.application.connections.connection_verifier import (
    ConnectionVerifier,
)
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
from socialflow.application.accounts.update_account import UpdateAccount
from socialflow.application.credentials.save_wordpress_credentials import (
    SaveWordPressCredentials,
)
from socialflow.application.credentials.errors import (
    CredentialStorageError,
)
from socialflow.application.credentials.delete_wordpress_credentials import (
    DeleteWordPressCredentials,
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

def create_accounts_page() -> AccountsPage:
    repository = InMemoryAccountRepository()

    return AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
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
        update_account=UpdateAccount(repository),
    )
    qtbot.addWidget(page)

    page.account_list.setCurrentRow(0)

    repository.remove(account)
    page.remove_button.click()

    assert page.account_status.text() == "Account could not be removed."
    assert page.account_status.property("status") == "error"

def test_accounts_page_loads_selected_account_into_form(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("SocialFlow WordPress")
    page.account_form.destination_input.setCurrentIndex(2)
    page.account_form.add_button.click()

    page.account_list.setCurrentRow(0)

    assert page.account_form.name_input.text() == "SocialFlow WordPress"
    assert (
        page.account_form.selected_destination()
        == PublishingDestination.WORDPRESS
    )

def test_accounts_page_contains_update_button(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    assert isinstance(page.update_button, QPushButton)
    assert page.update_button.text() == "Update account"


def test_update_button_is_disabled_without_selection(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    assert not page.update_button.isEnabled()


def test_update_button_is_enabled_when_account_is_selected(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("SocialFlow Facebook")
    page.account_form.add_button.click()

    page.account_list.setCurrentRow(0)

    assert page.update_button.isEnabled()

def test_accounts_page_updates_selected_account(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("SocialFlow Facebook")
    page.account_form.add_button.click()

    page.account_list.setCurrentRow(0)

    page.account_form.name_input.setText("Main Facebook")
    page.update_button.click()

    assert page.account_list.count() == 1
    assert page.account_list.item(0).text() == "Main Facebook - Facebook"

def test_accounts_page_shows_status_after_updating_account(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("SocialFlow Facebook")
    page.account_form.add_button.click()

    page.account_list.setCurrentRow(0)
    page.account_form.name_input.setText("Main Facebook")
    page.update_button.click()

    assert page.account_status.text() == "Account updated."
    assert page.account_status.property("status") == "success"

def test_accounts_page_starts_with_empty_form_when_accounts_exist(
    qtbot,
) -> None:
    repository = InMemoryAccountRepository()

    repository.add(
        Account(
            name="Persisted Facebook",
            destination=PublishingDestination.FACEBOOK,
        )
    )

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
    )
    qtbot.addWidget(page)

    assert page.account_list.count() == 1
    assert page.account_form.name_input.text() == ""
    assert page.account_list.selected_account() is None
    assert not page.update_button.isEnabled()
    assert not page.remove_button.isEnabled()


def test_accounts_page_clears_form_after_updating_account(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("SocialFlow Facebook")
    page.account_form.add_button.click()

    page.account_list.setCurrentRow(0)
    page.account_form.name_input.setText("Main Facebook")
    page.update_button.click()

    assert page.account_list.count() == 1
    assert page.account_list.item(0).text() == "Main Facebook - Facebook"
    assert page.account_form.name_input.text() == ""
    assert page.account_list.selected_account() is None
    assert not page.update_button.isEnabled()
    assert not page.remove_button.isEnabled()


def test_accounts_page_clears_form_after_removing_account(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("SocialFlow Facebook")
    page.account_form.add_button.click()

    page.account_list.setCurrentRow(0)
    page.remove_button.click()

    assert page.account_list.count() == 0
    assert page.account_form.name_input.text() == ""
    assert page.account_list.selected_account() is None
    assert not page.update_button.isEnabled()
    assert not page.remove_button.isEnabled()

def test_accounts_page_emits_accounts_changed_after_add(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("Main Facebook")

    with qtbot.waitSignal(page.accounts_changed):
        page.account_form.add_button.click()


def test_accounts_page_emits_accounts_changed_after_update(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("Main Facebook")
    page.account_form.add_button.click()

    page.account_list.setCurrentRow(0)
    page.account_form.name_input.setText("Updated Facebook")

    with qtbot.waitSignal(page.accounts_changed):
        page.update_button.click()


def test_accounts_page_emits_accounts_changed_after_remove(qtbot) -> None:
    page = create_accounts_page()
    qtbot.addWidget(page)

    page.account_form.name_input.setText("Main Facebook")
    page.account_form.add_button.click()

    page.account_list.setCurrentRow(0)

    with qtbot.waitSignal(page.accounts_changed):
        page.remove_button.click()

def test_accounts_page_accepts_wordpress_verifier(qtbot) -> None:
    verifier = Mock(spec=ConnectionVerifier)

    page = create_accounts_page()
    qtbot.addWidget(page)

    # Existing pages must remain usable without a verifier.
    assert page._wordpress_connection_verifier is None

    repository = InMemoryAccountRepository()

    page_with_verifier = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        wordpress_connection_verifier=verifier,
    )
    qtbot.addWidget(page_with_verifier)

    assert page_with_verifier._wordpress_connection_verifier is verifier

def test_accounts_page_saves_wordpress_password_after_add(qtbot) -> None:
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=SaveWordPressCredentials)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        save_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_form.name_input.setText("My WordPress Site")

    index = page.account_form.destination_input.findData(
        PublishingDestination.WORDPRESS
    )
    page.account_form.destination_input.setCurrentIndex(index)

    page.account_form.wordpress_application_password_input.setText(
        "test-application-password"
    )

    page.account_form.add_button.click()

    assert len(repository.all()) == 1

    saved_account = repository.all()[0]

    credential_service.execute.assert_called_once_with(
        saved_account,
        "test-application-password",
    )


def test_accounts_page_saves_wordpress_password_after_update(qtbot) -> None:
    """Updating WordPress credentials must preserve the account UUID."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=SaveWordPressCredentials)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        save_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    # Create an existing WordPress account.
    account = Account(
        name="Original WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    repository.add(account)

    # Refresh the account list and select the account.
    page._refresh_accounts()
    page.account_list.setCurrentRow(0)

    # Change the account name and application password.
    page.account_form.name_input.setText("Updated WordPress")
    page.account_form.wordpress_application_password_input.setText(
        "new-application-password"
    )

    page.update_button.click()

    # The account must still exist with its updated name.
    assert len(repository.all()) == 1
    assert repository.all()[0].name == "Updated WordPress"

    # Credentials must be saved using the original account UUID.
    credential_service.execute.assert_called_once_with(
        repository.all()[0],
        "new-application-password",
    )


def test_failed_wordpress_account_add_does_not_save_credentials(
    qtbot,
) -> None:
    """A rejected account must not trigger credential storage."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=SaveWordPressCredentials)

    existing_account = Account(
        name="My WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    repository.add(existing_account)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        save_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_form.name_input.setText("My WordPress")

    index = page.account_form.destination_input.findData(
        PublishingDestination.WORDPRESS
    )
    page.account_form.destination_input.setCurrentIndex(index)

    page.account_form.wordpress_application_password_input.setText(
        "should-not-be-saved"
    )

    page.account_form.add_button.click()

    assert len(repository.all()) == 1
    credential_service.execute.assert_not_called()

    assert page.account_status.property("status") == "error"


def test_failed_wordpress_account_update_does_not_save_credentials(
    qtbot,
) -> None:
    """A rejected account update must not trigger credential storage."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=SaveWordPressCredentials)

    original_account = Account(
        name="Original WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    existing_account = Account(
        name="Existing WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    repository.add(original_account)
    repository.add(existing_account)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        save_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    # Select the account that will be updated.
    page.account_list.setCurrentRow(0)

    # Attempt to rename it to an existing account name.
    page.account_form.name_input.setText("Existing WordPress")
    page.account_form.wordpress_application_password_input.setText(
        "should-not-be-saved"
    )

    page.update_button.click()

    # Both original accounts must remain unchanged.
    assert len(repository.all()) == 2
    assert repository.all()[0] == original_account
    assert repository.all()[1] == existing_account

    # No credential storage should occur.
    credential_service.execute.assert_not_called()

    assert page.account_status.property("status") == "error"


def test_accounts_page_handles_wordpress_credential_storage_failure(
    qtbot,
) -> None:
    """A credential failure must not hide a successful account creation."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=SaveWordPressCredentials)

    credential_service.execute.side_effect = CredentialStorageError(
        "Could not save WordPress credentials."
    )

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        save_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_form.name_input.setText("My WordPress")

    index = page.account_form.destination_input.findData(
        PublishingDestination.WORDPRESS
    )
    page.account_form.destination_input.setCurrentIndex(index)

    page.account_form.wordpress_application_password_input.setText(
        "test-application-password"
    )

    with qtbot.waitSignal(page.accounts_changed):
        page.account_form.add_button.click()

    # Account creation succeeded before credential storage failed.
    assert len(repository.all()) == 1
    assert repository.all()[0].name == "My WordPress"

    # Credential storage was attempted.
    credential_service.execute.assert_called_once_with(
        repository.all()[0],
        "test-application-password",
    )

    # The UI must report the incomplete operation.
    assert page.account_status.property("status") == "error"

    # The account list must reflect the persisted account.
    assert page.account_list.count() == 1


def test_accounts_page_handles_wordpress_credential_failure_on_update(
    qtbot,
) -> None:
    """A credential failure must not undo a successful account update."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=SaveWordPressCredentials)

    account = Account(
        name="Original WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    repository.add(account)

    credential_service.execute.side_effect = CredentialStorageError(
        "Could not save WordPress credentials."
    )

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        save_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    # Select the existing WordPress account.
    page.account_list.setCurrentRow(0)

    # Update the account name and application password.
    page.account_form.name_input.setText("Updated WordPress")
    page.account_form.wordpress_application_password_input.setText(
        "new-application-password"
    )

    with qtbot.waitSignal(page.accounts_changed):
        page.update_button.click()

    # The account update must remain persisted.
    assert len(repository.all()) == 1
    assert repository.all()[0].name == "Updated WordPress"

    # Credential saving must have been attempted.
    credential_service.execute.assert_called_once_with(
        repository.all()[0],
        "new-application-password",
    )

    # The UI must report the credential-storage failure.
    assert page.account_status.property("status") == "error"

    # The account list must reflect the updated account.
    assert page.account_list.count() == 1
    assert (
        page.account_list.item(0).text()
        == "Updated WordPress - WordPress"
    )


def test_converting_facebook_account_to_wordpress_saves_credentials(
    qtbot,
) -> None:
    """Converting an account must save credentials with its original UUID."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(wraps=SaveWordPressCredentials(
        credential_store=Mock(),
    ))

    original_account = Account(
        name="My Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(original_account)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        save_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_list.setCurrentRow(0)

    wordpress_index = page.account_form.destination_input.findData(
        PublishingDestination.WORDPRESS
    )
    assert wordpress_index >= 0

    page.account_form.destination_input.setCurrentIndex(
        wordpress_index
    )
    page.account_form.name_input.setText("My WordPress")
    page.account_form.wordpress_application_password_input.setText(
        "new-wordpress-password"
    )

    page.update_button.click()

    assert len(repository.all()) == 1

    updated_account = repository.all()[0]
    assert updated_account.destination == PublishingDestination.WORDPRESS
    assert updated_account.id == original_account.id

    credential_service.execute.assert_called_once_with(
        updated_account,
        "new-wordpress-password",
    )


def test_converting_instagram_account_to_wordpress_saves_credentials(
    qtbot,
) -> None:
    """Instagram-to-WordPress conversion preserves the account UUID."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(
        wraps=SaveWordPressCredentials(
            credential_store=Mock(),
        )
    )

    original_account = Account(
        name="My Instagram",
        destination=PublishingDestination.INSTAGRAM,
    )
    repository.add(original_account)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        save_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_list.setCurrentRow(0)

    wordpress_index = page.account_form.destination_input.findData(
        PublishingDestination.WORDPRESS
    )
    assert wordpress_index >= 0

    page.account_form.destination_input.setCurrentIndex(
        wordpress_index
    )
    page.account_form.name_input.setText("My WordPress")
    page.account_form.wordpress_application_password_input.setText(
        "instagram-conversion-password"
    )

    page.update_button.click()

    assert len(repository.all()) == 1

    updated_account = repository.all()[0]

    assert updated_account.name == "My WordPress"
    assert updated_account.destination == PublishingDestination.WORDPRESS
    assert updated_account.id == original_account.id

    credential_service.execute.assert_called_once_with(
        updated_account,
        "instagram-conversion-password",
    )


def test_converting_wordpress_account_to_facebook_does_not_save_credentials(
    qtbot,
) -> None:
    """Converting away from WordPress must not save WordPress credentials."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=SaveWordPressCredentials)

    original_account = Account(
        name="My WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    repository.add(original_account)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        save_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_list.setCurrentRow(0)

    facebook_index = page.account_form.destination_input.findData(
        PublishingDestination.FACEBOOK
    )
    assert facebook_index >= 0

    page.account_form.destination_input.setCurrentIndex(
        facebook_index
    )
    page.account_form.name_input.setText("My Facebook")

    page.update_button.click()

    assert len(repository.all()) == 1

    updated_account = repository.all()[0]

    assert updated_account.name == "My Facebook"
    assert updated_account.destination == PublishingDestination.FACEBOOK
    assert updated_account.id == original_account.id

    credential_service.execute.assert_not_called()


def test_removing_wordpress_account_deletes_credentials(qtbot) -> None:
    """Removing a WordPress account must delete its stored credentials."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=DeleteWordPressCredentials)

    account = Account(
        name="My WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    repository.add(account)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        delete_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_list.setCurrentRow(0)
    page.remove_button.click()

    assert repository.all() == ()
    credential_service.execute.assert_called_once_with(account)


def test_failed_wordpress_account_removal_does_not_delete_credentials(
    qtbot,
) -> None:
    """Failed account removal must not delete stored credentials."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=DeleteWordPressCredentials)

    account = Account(
        name="My WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    repository.add(account)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        delete_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_list.setCurrentRow(0)

    # Simulate an account that no longer exists in the repository.
    repository.remove(account)

    page.remove_button.click()

    # The removal operation failed, so credentials must be preserved.
    credential_service.execute.assert_not_called()

    assert page.account_status.property("status") == "error"


def test_wordpress_credential_deletion_failure_after_account_removal(
    qtbot,
) -> None:
    """Credential deletion failure must not undo account removal."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=DeleteWordPressCredentials)

    account = Account(
        name="My WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    repository.add(account)

    credential_service.execute.side_effect = CredentialStorageError(
        "Could not securely delete WordPress credentials."
    )

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        delete_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_list.setCurrentRow(0)

    with qtbot.waitSignal(page.accounts_changed):
        page.remove_button.click()

    # Account removal succeeded despite credential deletion failure.
    assert repository.all() == ()
    assert page.account_list.count() == 0

    # Secure credential deletion was attempted.
    credential_service.execute.assert_called_once_with(account)

    # The UI reports the incomplete cleanup operation.
    assert page.account_status.property("status") == "error"

    # The form and selection are reset.
    assert page.account_list.selected_account() is None
    assert page.account_form.name_input.text() == ""


def test_converting_wordpress_to_facebook_deletes_credentials(
    qtbot,
) -> None:
    """Converting away from WordPress must delete obsolete credentials."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=DeleteWordPressCredentials)

    original_account = Account(
        name="My WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    repository.add(original_account)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        delete_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_list.setCurrentRow(0)

    facebook_index = page.account_form.destination_input.findData(
        PublishingDestination.FACEBOOK
    )
    assert facebook_index >= 0

    page.account_form.destination_input.setCurrentIndex(facebook_index)
    page.account_form.name_input.setText("My Facebook")

    with qtbot.waitSignal(page.accounts_changed):
        page.update_button.click()

    assert len(repository.all()) == 1

    updated_account = repository.all()[0]

    assert updated_account.destination == PublishingDestination.FACEBOOK
    assert updated_account.id == original_account.id

    # Delete credentials using the original WordPress account.
    credential_service.execute.assert_called_once_with(original_account)

    assert page.account_status.property("status") == "success"


def test_converting_wordpress_to_instagram_deletes_credentials(
    qtbot,
) -> None:
    """WordPress-to-Instagram conversion must remove old credentials."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=DeleteWordPressCredentials)

    original_account = Account(
        name="My WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    repository.add(original_account)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        delete_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_list.setCurrentRow(0)

    instagram_index = page.account_form.destination_input.findData(
        PublishingDestination.INSTAGRAM
    )
    assert instagram_index >= 0

    page.account_form.destination_input.setCurrentIndex(instagram_index)
    page.account_form.name_input.setText("My Instagram")

    with qtbot.waitSignal(page.accounts_changed):
        page.update_button.click()

    assert len(repository.all()) == 1

    updated_account = repository.all()[0]

    assert updated_account.name == "My Instagram"
    assert updated_account.destination == PublishingDestination.INSTAGRAM
    assert updated_account.id == original_account.id

    credential_service.execute.assert_called_once_with(original_account)

    assert page.account_status.property("status") == "success"


def test_failed_wordpress_conversion_does_not_delete_credentials(
    qtbot,
) -> None:
    """Failed account conversion must preserve WordPress credentials."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=DeleteWordPressCredentials)

    original_account = Account(
        name="My WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    existing_facebook = Account(
        name="Existing Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    repository.add(original_account)
    repository.add(existing_facebook)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        delete_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_list.setCurrentRow(0)

    facebook_index = page.account_form.destination_input.findData(
        PublishingDestination.FACEBOOK
    )
    assert facebook_index >= 0

    page.account_form.destination_input.setCurrentIndex(facebook_index)

    # Use an existing account name to trigger a duplicate-account error.
    page.account_form.name_input.setText("Existing Facebook")

    page.update_button.click()

    # The failed update must leave both accounts unchanged.
    assert repository.all() == (
        original_account,
        existing_facebook,
    )

    # No credential cleanup should occur.
    credential_service.execute.assert_not_called()

    assert page.account_status.property("status") == "error"


def test_wordpress_credential_deletion_failure_after_conversion(
    qtbot,
) -> None:
    """Credential cleanup failure must not undo account conversion."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=DeleteWordPressCredentials)

    original_account = Account(
        name="My WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    repository.add(original_account)

    credential_service.execute.side_effect = CredentialStorageError(
        "Could not securely delete WordPress credentials."
    )

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        delete_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_list.setCurrentRow(0)

    facebook_index = page.account_form.destination_input.findData(
        PublishingDestination.FACEBOOK
    )
    assert facebook_index >= 0

    page.account_form.destination_input.setCurrentIndex(facebook_index)
    page.account_form.name_input.setText("My Facebook")

    with qtbot.waitSignal(page.accounts_changed):
        page.update_button.click()

    # Account conversion succeeded despite credential cleanup failure.
    assert len(repository.all()) == 1

    updated_account = repository.all()[0]

    assert updated_account.name == "My Facebook"
    assert updated_account.destination == PublishingDestination.FACEBOOK
    assert updated_account.id == original_account.id

    # Credential deletion was attempted using the original account.
    credential_service.execute.assert_called_once_with(original_account)

    # The UI must report the incomplete cleanup operation.
    assert page.account_status.property("status") == "error"

    # The account list must reflect the successful conversion.
    assert page.account_list.count() == 1
    assert page.account_list.item(0).text() == "My Facebook - Facebook"

    # The form and selection must be reset.
    assert page.account_list.selected_account() is None
    assert page.account_form.name_input.text() == ""


def test_updating_wordpress_account_does_not_delete_credentials(
    qtbot,
) -> None:
    """Updating a WordPress account must preserve its stored credentials."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=DeleteWordPressCredentials)

    original_account = Account(
        name="Original WordPress",
        destination=PublishingDestination.WORDPRESS,
    )
    repository.add(original_account)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        delete_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_list.setCurrentRow(0)

    # Change only the account name.
    page.account_form.name_input.setText("Updated WordPress")

    with qtbot.waitSignal(page.accounts_changed):
        page.update_button.click()

    assert len(repository.all()) == 1

    updated_account = repository.all()[0]

    assert updated_account.name == "Updated WordPress"
    assert updated_account.destination == PublishingDestination.WORDPRESS
    assert updated_account.id == original_account.id

    # Renaming a WordPress account must not delete its credentials.
    credential_service.execute.assert_not_called()

    assert page.account_status.property("status") == "success"


@pytest.mark.parametrize(
    "destination",
    [
        PublishingDestination.FACEBOOK,
        PublishingDestination.INSTAGRAM,
    ],
)
def test_removing_non_wordpress_account_does_not_delete_credentials(
    qtbot,
    destination: PublishingDestination,
) -> None:
    """Removing other platforms must not delete WordPress credentials."""
    repository = InMemoryAccountRepository()
    credential_service = Mock(spec=DeleteWordPressCredentials)

    account = Account(
        name="Non-WordPress Account",
        destination=destination,
    )
    repository.add(account)

    page = AccountsPage(
        add_account=AddAccount(repository),
        list_accounts=ListAccounts(repository),
        remove_account=RemoveAccount(repository),
        update_account=UpdateAccount(repository),
        delete_wordpress_credentials=credential_service,
    )
    qtbot.addWidget(page)

    page.account_list.setCurrentRow(0)

    with qtbot.waitSignal(page.accounts_changed):
        page.remove_button.click()

    # The account must be removed successfully.
    assert repository.all() == ()
    assert page.account_list.count() == 0

    # No WordPress credentials should be touched.
    credential_service.execute.assert_not_called()

    assert page.account_status.property("status") == "success"
