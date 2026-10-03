from PySide6.QtWidgets import QListWidget, QWidget

from socialflow.domain.account.account import Account


class AccountList(QListWidget):
    """Displays configured publishing accounts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def set_accounts(self, accounts: tuple[Account, ...]) -> None:
        """Replace the displayed accounts."""
        self.clear()

        for account in accounts:
            self.addItem(
                f"{account.name} - {account.destination.display_name}"
            )