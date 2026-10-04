from PySide6.QtWidgets import QVBoxLayout, QWidget

from socialflow.application.accounts.list_accounts import ListAccounts
from socialflow.application.publishing.errors import PublishingError
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.domain.publishing.publish_request import PublishRequest
from socialflow.ui.posts.post_editor import PostEditor
from socialflow.ui.posts.publish_status import PublishStatus


class PostsPage(QWidget):
    """Page for composing and publishing posts."""

    def __init__(
        self,
        publish_post: PublishPost,
        list_accounts: ListAccounts,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._publish_post = publish_post
        self._list_accounts = list_accounts

        self.post_editor = PostEditor(self)
        self.publish_status = PublishStatus(self)

        layout = QVBoxLayout()
        layout.addWidget(self.post_editor)
        layout.addWidget(self.publish_status)

        self.setLayout(layout)

        self.post_editor.publish_requested.connect(
            self._handle_publish_request
        )

        self.refresh_accounts()

    def refresh_accounts(self) -> None:
        """Refresh the accounts available for publishing."""
        self.post_editor.set_accounts(
            self._list_accounts.execute()
        )

    def _handle_publish_request(
        self,
        request: PublishRequest,
    ) -> None:
        """Publish a request created by the post editor."""
        try:
            self._publish_post.execute(request)
        except PublishingError:
            self.publish_status.show_error()
            return

        self.publish_status.show_success()