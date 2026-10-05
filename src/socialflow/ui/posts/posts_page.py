from PySide6.QtWidgets import QVBoxLayout, QWidget

from socialflow.application.accounts.list_accounts import ListAccounts
from socialflow.application.publishing.errors import PublishingError
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.application.tags.create_tag import CreateTag
from socialflow.application.tags.list_tags import ListTags
from socialflow.domain.publishing.publish_request import PublishRequest
from socialflow.ui.posts.post_editor import PostEditor
from socialflow.ui.posts.publish_status import PublishStatus
from socialflow.domain.post.tag import Tag


class PostsPage(QWidget):
    """Page for composing and publishing posts."""

    def __init__(
        self,
        publish_post: PublishPost,
        list_accounts: ListAccounts,
        list_tags: ListTags,
        create_tag: CreateTag,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._publish_post = publish_post
        self._list_accounts = list_accounts
        self._list_tags = list_tags
        self._create_tag = create_tag

        self.post_editor = PostEditor(self)
        self.publish_status = PublishStatus(self)

        layout = QVBoxLayout()
        layout.addWidget(self.post_editor)
        layout.addWidget(self.publish_status)

        self.setLayout(layout)

        self.post_editor.publish_requested.connect(
            self._handle_publish_request
        )

        self.post_editor.account_selection_changed.connect(
            self._refresh_available_tags
        )

        self.post_editor.tag_selector.tag_created.connect(
            self._create_tag_for_selected_accounts
        )

        self.refresh_accounts()

    def refresh_accounts(self) -> None:
        """Refresh the accounts available for publishing."""
        self.post_editor.set_accounts(
            self._list_accounts.execute()
        )

    def _refresh_available_tags(self) -> None:
        """Refresh tags available for the selected accounts."""
        tags = []
        seen_tags = set()

        for account in self.post_editor.selected_accounts():
            for tag in self._list_tags.execute(account):
                if tag not in seen_tags:
                    seen_tags.add(tag)
                    tags.append(tag)

        self.post_editor.tag_selector.set_available_tags(
            tuple(tags)
        )

    def _create_tag_for_selected_accounts(
            self,
            tag: Tag,
    ) -> None:
        """Create a new tag for every selected account."""
        for account in self.post_editor.selected_accounts():
            self._create_tag.execute(
                account=account,
                name=tag.name,
            )

        self._refresh_available_tags()

    def _handle_publish_request(
            self,
            request: PublishRequest,
    ) -> None:
        """Publish a request created by the post editor."""
        try:
            results = self._publish_post.execute(request)
        except PublishingError:
            self.publish_status.show_error()
            return

        self.publish_status.show_results(results)