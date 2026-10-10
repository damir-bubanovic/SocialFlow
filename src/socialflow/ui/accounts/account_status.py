
from PySide6.QtWidgets import QLabel, QWidget

from socialflow.domain.connections.connection_result import (
    ConnectionResult,
)


class AccountStatus(QLabel):
    """Displays feedback about account operations."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.clear_status()

    def show_success(self) -> None:
        """Display a successful account operation status."""
        self.setText("Account added.")
        self.setProperty("status", "success")

    def show_error(self) -> None:
        """Display a failed account operation status."""
        self.setText("Account could not be added.")
        self.setProperty("status", "error")

    def show_removed(self) -> None:
        """Display a successful account removal status."""
        self.setText("Account removed.")
        self.setProperty("status", "success")

    def show_remove_error(self) -> None:
        """Display a failed account removal status."""
        self.setText("Account could not be removed.")
        self.setProperty("status", "error")

    def clear_status(self) -> None:
        """Clear the current account status."""
        self.setText("")
        self.setProperty("status", "")

    def show_updated(self) -> None:
        """Display a successful account update status."""
        self.setText("Account updated.")
        self.setProperty("status", "success")

    def show_connection_result(self, result: ConnectionResult) -> None:
        """Display the result of account connection verification."""
        self.setText(result.message)
        self.setProperty(
            "status",
            "success" if result.is_connected else "error",
        )

    def show_connection_error(self, message: str) -> None:
        """Display a WordPress connection verification error."""
        self.setText(message)
        self.setProperty("status", "error")

