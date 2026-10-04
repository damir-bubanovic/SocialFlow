from collections.abc import Callable

from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QWidget

from socialflow.domain.account.account import Account


class DestinationSelector(QWidget):
    """Controls for selecting configured publishing accounts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._accounts: tuple[Account, ...] = ()
        self._checkboxes: list[QCheckBox] = []

        self._layout = QHBoxLayout()
        self._layout.addStretch()

        self.setLayout(self._layout)

    def set_accounts(self, accounts: tuple[Account, ...]) -> None:
        """Replace the available publishing accounts."""
        for checkbox in self._checkboxes:
            self._layout.removeWidget(checkbox)
            checkbox.deleteLater()

        self._checkboxes.clear()
        self._accounts = accounts

        for account in accounts:
            checkbox = QCheckBox(account.display_name(), self)

            self._layout.insertWidget(
                self._layout.count() - 1,
                checkbox,
            )
            self._checkboxes.append(checkbox)

    def selected_accounts(self) -> tuple[Account, ...]:
        """Return the selected publishing accounts."""
        return tuple(
            account
            for account, checkbox in zip(
                self._accounts,
                self._checkboxes,
                strict=True,
            )
            if checkbox.isChecked()
        )

    def connect_selection_changed(
        self,
        callback: Callable[[], None],
    ) -> None:
        """Connect a callback to account selection changes."""
        for checkbox in self._checkboxes:
            checkbox.toggled.connect(callback)