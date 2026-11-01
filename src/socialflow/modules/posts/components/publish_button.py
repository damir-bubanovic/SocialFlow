from PySide6.QtWidgets import QPushButton, QWidget


class PublishButton(QPushButton):
    """Button used to begin publishing a post."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Publish", parent)

        self.setEnabled(False)

    def set_post_available(self, available: bool) -> None:
        """Enable publishing when a post contains content."""
        self.setEnabled(available)