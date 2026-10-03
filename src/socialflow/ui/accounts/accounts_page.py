from PySide6.QtWidgets import QVBoxLayout, QWidget

from socialflow.application.accounts.add_account import AddAccount
from socialflow.application.accounts.list_accounts import ListAccounts
from socialflow.ui.accounts.account_form import AccountForm
from socialflow.ui.accounts.account_list import AccountList
from socialflow.ui.accounts.account_status import AccountStatus
from socialflow.application.accounts.errors import (
    DuplicateAccountError,
    InvalidAccountError,
)


class AccountsPage(QWidget):
    """Page for managing publishing accounts."""

    def __init__(
        self,
        add_account: AddAccount,
        list_accounts: ListAccounts,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._add_account = add_account
        self._list_accounts = list_accounts

        self.account_form = AccountForm(self)
        self.account_list = AccountList(self)
        self.account_status = AccountStatus(self)

        layout = QVBoxLayout()
        layout.addWidget(self.account_form)
        layout.addWidget(self.account_status)
        layout.addWidget(self.account_list)

        self.setLayout(layout)

        self.account_form.add_button.clicked.connect(
            self._handle_add_account
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

    def _refresh_accounts(self) -> None:
        """Refresh the displayed account list."""
        self.account_list.set_accounts(
            self._list_accounts.execute()
        )