from PySide6.QtWidgets import QVBoxLayout, QWidget


class MyPostsView(QWidget):
    """Container for recent publications and remote posts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.content_layout = QVBoxLayout(self)