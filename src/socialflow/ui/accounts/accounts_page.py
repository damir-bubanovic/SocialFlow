from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from socialflow.application.accounts.add_account import AddAccount
from socialflow.application.accounts.errors import (
    AccountNotFoundError,
    DuplicateAccountError,
    InvalidAccountError,
)
from socialflow.application.accounts.list_accounts import ListAccounts
from socialflow.application.accounts.remove_account import RemoveAccount
from socialflow.application.accounts.update_account import UpdateAccount
from socialflow.application.connections.connection_verifier import (
    ConnectionVerifier,
)
from socialflow.application.credentials.save_wordpress_credentials import (
    SaveWordPressCredentials,
)
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.application.credentials.errors import (
    CredentialStorageError,
)
from socialflow.ui.accounts.account_form import AccountForm
from socialflow.ui.accounts.account_list import AccountList
from socialflow.ui.accounts.account_status import AccountStatus
from socialflow.domain.account.account import Account
from socialflow.application.credentials.delete_wordpress_credentials import (
    DeleteWordPressCredentials,
)


class AccountsPage(QWidget):
    """Page for managing publishing accounts."""

    accounts_changed = Signal()

    def __init__(
        self,
        add_account: AddAccount,
        list_accounts: ListAccounts,
        remove_account: RemoveAccount,
        update_account: UpdateAccount,
        parent: QWidget | None = None,
        wordpress_connection_verifier: ConnectionVerifier | None = None,
        save_wordpress_credentials: SaveWordPressCredentials | None = None,
        delete_wordpress_credentials: DeleteWordPressCredentials | None = None,
    ) -> None:
        super().__init__(parent)

        self._add_account = add_account
        self._list_accounts = list_accounts
        self._remove_account = remove_account
        self._update_account = update_account
        self._wordpress_connection_verifier = wordpress_connection_verifier
        self._save_wordpress_credentials = save_wordpress_credentials
        self._delete_wordpress_credentials = delete_wordpress_credentials

        self.account_form = AccountForm(self)
        self.account_list = AccountList(self)
        self.account_status = AccountStatus(self)

        self.update_button = QPushButton("Update account", self)
        self.update_button.setEnabled(False)

        self.remove_button = QPushButton("Remove account", self)
        self.remove_button.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self.account_form)
        layout.addWidget(self.account_status)
        layout.addWidget(self.account_list)
        layout.addWidget(self.update_button)
        layout.addWidget(self.remove_button)

        self.setLayout(layout)

        self.account_form.add_button.clicked.connect(
            self._handle_add_account
        )
        self.update_button.clicked.connect(
            self._handle_update_account
        )
        self.remove_button.clicked.connect(
            self._handle_remove_account
        )
        self.account_list.itemSelectionChanged.connect(
            self._update_account_buttons
        )
        self.account_list.itemSelectionChanged.connect(
            self._load_selected_account
        )

        self._refresh_accounts()

    def _handle_add_account(self) -> None:
        """Add an account and then save its WordPress credentials."""
        account = self.account_form.account()
        password = self.account_form.wordpress_application_password()

        try:
            self._add_account.execute(account)
        except (DuplicateAccountError, InvalidAccountError):
            self.account_status.show_error()
            return

        if (
            account.destination == PublishingDestination.WORDPRESS
            and self._save_wordpress_credentials is not None
        ):
            try:
                self._save_wordpress_credentials.execute(
                    account,
                    password,
                )
            except CredentialStorageError:
                # Account creation succeeded, but credential saving failed.
                self._refresh_accounts()
                self.account_status.show_error()
                self.accounts_changed.emit()
                return

        self._refresh_accounts()
        self.account_status.show_success()
        self.accounts_changed.emit()


    def _handle_update_account(self) -> None:
        """Update an account and manage its WordPress credentials."""
        current = self.account_list.selected_account()

        if current is None:
            return

        updated = self.account_form.account()
        password = self.account_form.wordpress_application_password()

        try:
            self._update_account.execute(
                current,
                updated,
            )
        except (
            AccountNotFoundError,
            DuplicateAccountError,
            InvalidAccountError,
        ):
            self.account_status.show_error()
            return

        # Save credentials when the updated account is WordPress.
        if (
            updated.destination == PublishingDestination.WORDPRESS
            and self._save_wordpress_credentials is not None
        ):
            try:
                # Preserve the existing account UUID.
                self._save_wordpress_credentials.execute(
                    Account(
                        name=updated.name,
                        destination=updated.destination,
                        id=current.id,
                    ),
                    password,
                )
            except CredentialStorageError:
                # Account update succeeded, but credential saving failed.
                self._refresh_accounts()
                self.account_status.show_error()
                self.accounts_changed.emit()
                return

        # Delete obsolete credentials when converting away from WordPress.
        if (
            current.destination == PublishingDestination.WORDPRESS
            and updated.destination != PublishingDestination.WORDPRESS
            and self._delete_wordpress_credentials is not None
        ):
            try:
                self._delete_wordpress_credentials.execute(current)
            except CredentialStorageError:
                # Account update succeeded, but credential cleanup failed.
                self._refresh_accounts()
                self.account_status.show_error()
                self.accounts_changed.emit()
                return

        self._refresh_accounts()
        self.account_status.show_updated()
        self.accounts_changed.emit()


    def _handle_remove_account(self) -> None:
        """Remove the selected account and clean up WordPress credentials."""
        account = self.account_list.selected_account()

        if account is None:
            return

        try:
            self._remove_account.execute(account)
        except AccountNotFoundError:
            self.account_status.show_remove_error()
            return

        # Only delete credentials after successful account removal.
        if (
                account.destination == PublishingDestination.WORDPRESS
                and self._delete_wordpress_credentials is not None
        ):
            try:
                self._delete_wordpress_credentials.execute(account)
            except CredentialStorageError:
                # Account removal succeeded, but credential cleanup failed.
                self._refresh_accounts()
                self.account_status.show_remove_error()
                self.accounts_changed.emit()
                return

        self._refresh_accounts()
        self.account_status.show_removed()
        self.accounts_changed.emit()

    def _load_selected_account(self) -> None:
        """Load the selected account into the account form."""
        account = self.account_list.selected_account()

        if account is None:
            return

        self.account_form.set_account(account)

    def _update_account_buttons(self) -> None:
        """Synchronize account action buttons with selection."""
        has_selection = (
            self.account_list.selected_account() is not None
        )

        self.update_button.setEnabled(has_selection)
        self.remove_button.setEnabled(has_selection)

    def _refresh_accounts(self) -> None:
        """Refresh the account list with no account selected."""
        self.account_list.set_accounts(
            self._list_accounts.execute()
        )
        self.account_list.clearSelection()
        self.account_list.setCurrentRow(-1)
        self.account_form.clear()
        self._update_account_buttons()
