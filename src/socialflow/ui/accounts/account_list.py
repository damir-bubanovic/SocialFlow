from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget

from socialflow.domain.account.account import Account


class AccountList(QListWidget):
    """Displays configured publishing accounts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def set_accounts(self, accounts: tuple[Account, ...]) -> None:
        """Replace the displayed accounts."""
        self.clear()

        for account in accounts:
            item = QListWidgetItem(
                f"{account.name} - {account.destination.display_name}"
            )
            item.setData(Qt.ItemDataRole.UserRole, account)
            self.addItem(item)

    def selected_account(self) -> Account | None:
        """Return the currently selected account."""
        item = self.currentItem()

        if item is None:
            return None

        account = item.data(Qt.ItemDataRole.UserRole)

        if isinstance(account, Account):
            return account

        return None