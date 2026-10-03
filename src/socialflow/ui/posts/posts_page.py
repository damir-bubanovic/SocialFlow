from PySide6.QtWidgets import QVBoxLayout, QWidget

from socialflow.application.publishing.publish_post import PublishPost
from socialflow.ui.posts.post_editor import PostEditor
from socialflow.ui.posts.publish_status import PublishStatus
from socialflow.application.publishing.errors import PublishingError
from socialflow.domain.publishing.publish_request import PublishRequest


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
        self.publish_status = PublishStatus(self)

        layout = QVBoxLayout()
        layout.addWidget(self.post_editor)
        layout.addWidget(self.publish_status)

        self.setLayout(layout)

        self.post_editor.publish_requested.connect(
            self._handle_publish_request
        )

    def _handle_publish_request(self, request: PublishRequest) -> None:
        """Delegate publishing to the application service."""
        try:
            self._publish_post.execute(request)
        except PublishingError:
            self.publish_status.show_error()
            return

        self.publish_status.show_success()