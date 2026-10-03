from PySide6.QtWidgets import QVBoxLayout, QWidget

from socialflow.application.publishing.publish_post import PublishPost
from socialflow.domain.post.post import Post
from socialflow.ui.posts.post_editor import PostEditor


class PostsPage(QWidget):
    """Primary page for creating and managing social media posts."""

    def __init__(
            self,
            publish_post: PublishPost,
            parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._publish_post = publish_post
        self.post_editor = PostEditor(self)

        layout = QVBoxLayout()
        layout.addWidget(self.post_editor)

        self.setLayout(layout)

        self.post_editor.publish_requested.connect(
            self._handle_publish_request
        )

    def _handle_publish_request(self, post: Post) -> None:
        """Delegate publishing to the application service."""
        self._publish_post.execute(post)