from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from socialflow.application.accounts.add_account import AddAccount
from socialflow.application.accounts.errors import (
    AccountNotFoundError,
    DuplicateAccountError,
    InvalidAccountError,
)
from socialflow.application.accounts.list_accounts import ListAccounts
from socialflow.application.accounts.remove_account import RemoveAccount
from socialflow.ui.accounts.account_form import AccountForm
from socialflow.ui.accounts.account_list import AccountList
from socialflow.ui.accounts.account_status import AccountStatus


class AccountsPage(QWidget):
    """Page for managing publishing accounts."""

    def __init__(
        self,
        add_account: AddAccount,
        list_accounts: ListAccounts,
        remove_account: RemoveAccount,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._add_account = add_account
        self._list_accounts = list_accounts
        self._remove_account = remove_account

        self.account_form = AccountForm(self)
        self.account_list = AccountList(self)
        self.account_status = AccountStatus(self)
        self.remove_button = QPushButton("Remove account", self)
        self.remove_button.setEnabled(False)

        layout = QVBoxLayout()
        layout.addWidget(self.account_form)
        layout.addWidget(self.account_status)
        layout.addWidget(self.account_list)
        layout.addWidget(self.remove_button)

        self.setLayout(layout)

        self.account_form.add_button.clicked.connect(
            self._handle_add_account
        )
        self.remove_button.clicked.connect(
            self._handle_remove_account
        )
        self.account_list.itemSelectionChanged.connect(
            self._update_remove_button
        )

        self._refresh_accounts()

    def _handle_add_account(self) -> None:
        """Add the account represented by the form."""
        try:
            self._add_account.execute(self.account_form.account())
        except (DuplicateAccountError, InvalidAccountError):
            self.account_status.show_error()
            return

        self._refresh_accounts()
        self.account_form.clear()
        self.account_status.show_success()

    def _handle_remove_account(self) -> None:
        """Remove the currently selected account."""
        account = self.account_list.selected_account()

        if account is None:
            return

        try:
            self._remove_account.execute(account)
        except AccountNotFoundError:
            self.account_status.show_remove_error()
            return

        self._refresh_accounts()
        self.account_status.show_removed()

    def _update_remove_button(self) -> None:
        """Synchronize the remove button with account selection."""
        self.remove_button.setEnabled(
            self.account_list.selected_account() is not None
        )

    def _refresh_accounts(self) -> None:
        """Refresh the displayed account list."""
        self.account_list.set_accounts(
            self._list_accounts.execute()
        )