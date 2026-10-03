from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget

from socialflow.ui.posts.post_editor import PostEditor
from socialflow.domain.post.post import Post


class PostsPage(QWidget):
    """Primary page for creating and managing social media posts."""

    publish_requested = Signal(Post)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.post_editor = PostEditor(self)

        layout = QVBoxLayout()
        layout.addWidget(self.post_editor)

        self.setLayout(layout)
        self.post_editor.publish_requested.connect(
            self.publish_requested.emit
        )