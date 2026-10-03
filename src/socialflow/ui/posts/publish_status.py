from PySide6.QtWidgets import QLabel, QWidget


class PublishStatus(QLabel):
    """Displays feedback about publishing activity."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.clear_status()

    def show_success(self) -> None:
        """Display a successful publishing request status."""
        self.setText("Publish request completed.")
        self.setProperty("status", "success")

    def show_error(self) -> None:
        """Display a failed publishing request status."""
        self.setText("Publish request failed.")
        self.setProperty("status", "error")

    def clear_status(self) -> None:
        """Clear the current publishing status."""
        self.setText("")
        self.setProperty("status", "")