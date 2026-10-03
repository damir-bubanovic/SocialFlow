from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination


class AccountForm(QWidget):
    """Form for entering a publishing account."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Account name")

        self.destination_input = QComboBox(self)
        self._add_destination(PublishingDestination.FACEBOOK)
        self._add_destination(PublishingDestination.INSTAGRAM)
        self._add_destination(PublishingDestination.WORDPRESS)

        self.add_button = QPushButton("Add account", self)

        layout = QFormLayout()
        layout.addRow("Name", self.name_input)
        layout.addRow("Destination", self.destination_input)
        layout.addRow(self.add_button)

        self.setLayout(layout)

    def account(self) -> Account:
        """Return the account represented by the form."""
        return Account(
            name=self.name_input.text(),
            destination=self.selected_destination(),
        )

    def selected_destination(self) -> PublishingDestination:
        """Return the currently selected destination."""
        return PublishingDestination(self.destination_input.currentData())

    def _add_destination(
        self,
        destination: PublishingDestination,
    ) -> None:
        """Add a publishing destination to the selector."""
        self.destination_input.addItem(
            destination.display_name,
            destination,
        )