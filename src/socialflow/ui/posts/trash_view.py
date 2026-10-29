from PySide6.QtWidgets import QVBoxLayout, QWidget


class TrashView(QWidget):
    """Container for WordPress Trash management."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.content_layout = QVBoxLayout(self)