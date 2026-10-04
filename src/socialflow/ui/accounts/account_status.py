from PySide6.QtWidgets import QLabel, QWidget


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