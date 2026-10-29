from PySide6.QtWidgets import QVBoxLayout, QWidget


class CreatePostView(QWidget):
    """Container for the post composer and publishing controls."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.content_layout = QVBoxLayout(self)