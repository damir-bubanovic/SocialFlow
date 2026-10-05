from socialflow.application.publishing.publish_result import PublishResult
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

    def show_results(
            self,
            results: tuple[PublishResult, ...],
    ) -> None:
        """Display publishing results for individual accounts."""
        lines = []

        for result in results:
            outcome = "Published" if result.succeeded else "Failed"
            lines.append(f"{result.account.name} — {outcome}")

        self.setText("\n".join(lines))

        if all(result.succeeded for result in results):
            self.setProperty("status", "success")
        else:
            self.setProperty("status", "error")

    def clear_status(self) -> None:
        """Clear the current publishing status."""
        self.setText("")
        self.setProperty("status", "")