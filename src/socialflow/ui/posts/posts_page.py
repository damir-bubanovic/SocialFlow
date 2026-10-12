from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QWidget

from socialflow.application.accounts.list_accounts import ListAccounts
from socialflow.application.publishing.list_recent_publications import (
    ListRecentPublications,
)
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.application.tags.create_tag import CreateTag
from socialflow.application.tags.list_tags import ListTags
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.publish_request import PublishRequest
from socialflow.domain.publishing.publication import Publication
from socialflow.ui.posts.post_editor import PostEditor
from socialflow.ui.posts.publish_status import PublishStatus
from socialflow.ui.posts.recent_posts_panel import RecentPostsPanel
from socialflow.ui.posts.publishing_controller import PublishingController
from socialflow.application.publishing.publish_result import PublishResult
from socialflow.application.publishing.build_retry_request import (
    BuildRetryRequest,
)


class PostsPage(QWidget):
    """Page for composing and publishing posts."""
    publishing_finished = Signal()

    def __init__(
        self,
        publish_post: PublishPost,
        list_accounts: ListAccounts,
        list_tags: ListTags,
        create_tag: CreateTag,
        list_recent_publications: ListRecentPublications,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._publishing_controller = PublishingController(
            publish_post,
            self,
        )
        self._publishing_controller.progress.connect(
            self._on_publish_progress
        )
        self._publishing_controller.result_ready.connect(
            self._on_publish_results
        )
        self._publishing_controller.error_occurred.connect(
            self._on_publish_error
        )
        self._publishing_controller.finished.connect(
            self._on_publishing_finished
        )
        self._publishing_controller.finished.connect(
            self.publishing_finished.emit
        )

        self._publishing_completed = 0
        self._publishing_total = 0
        self._last_publish_request: PublishRequest | None = None
        self._last_publish_results: tuple[PublishResult, ...] = ()
        self._list_accounts = list_accounts
        self._list_tags = list_tags
        self._create_tag = create_tag
        self._list_recent_publications = list_recent_publications

        self.post_editor = PostEditor(self)
        self.new_post_button = QPushButton("New Post", self)
        self.new_post_button.clicked.connect(
            self.post_editor.new_post
        )
        self.retry_failed_button = QPushButton("Retry Failed", self)
        self.retry_failed_button.setEnabled(False)
        self.retry_failed_button.clicked.connect(
            self._retry_failed_publications
        )
        self.publish_status = PublishStatus(self)
        self.recent_posts_panel = RecentPostsPanel(
            list_recent_publications,
            self,
        )

        layout = QVBoxLayout()
        layout.addWidget(self.new_post_button)
        layout.addWidget(self.post_editor)
        layout.addWidget(self.retry_failed_button)
        layout.addWidget(self.publish_status)
        layout.addWidget(self.recent_posts_panel)



        self.setLayout(layout)

        self.post_editor.publish_requested.connect(
            self._handle_publish_request
        )

        self.post_editor.account_selection_changed.connect(
            self._refresh_available_tags
        )

        self.post_editor.account_selection_changed.connect(
            self._refresh_recent_posts
        )

        self.post_editor.tag_selector.tag_created.connect(
            self._create_tag_for_selected_accounts
        )

        self.recent_posts_panel.publication_selected.connect(
            self._load_publication
        )
        self.post_editor.text_editor.textChanged.connect(
            self._invalidate_retry
        )
        self.post_editor.language_controls.selector.currentIndexChanged.connect(
            self._invalidate_retry
        )
        self.post_editor.image_selector.selection_changed.connect(
            self._invalidate_retry
        )
        self.post_editor.tag_selector.selection_changed.connect(
            self._invalidate_retry
        )

        self.new_post_button.clicked.connect(
            self._invalidate_retry
        )

        self.post_editor.account_selection_changed.connect(
            self._invalidate_retry
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

    def _refresh_recent_posts(self) -> None:
        """Refresh history for the first selected account."""
        accounts = self.post_editor.selected_accounts()

        if not accounts:
            self.recent_posts_panel.set_account(None)
            return

        self.recent_posts_panel.set_account(accounts[0])

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

    def _load_publication(
            self,
            publication: Publication,
    ) -> None:
        """Load a historical publication into the post editor."""
        self.post_editor.load_post(publication.post)


    @property
    def publishing_is_running(self) -> bool:
        """Report whether background publishing is active."""
        return self._publishing_controller.is_running

    def _invalidate_retry(self) -> None:
        """Discard retry state when the draft changes."""
        self._last_publish_request = None
        self._last_publish_results = ()
        self.retry_failed_button.setEnabled(False)

    def _start_publishing(self, request: PublishRequest) -> None:
        """Start a publishing operation with shared UI handling."""
        self._publishing_completed = 0
        self._publishing_total = len(request.accounts)

        self.post_editor.publish_button.setEnabled(False)
        self.retry_failed_button.setEnabled(False)

        self.publish_status.setText(
            f"Publishing 0 of {self._publishing_total} accounts..."
        )

        self._publishing_controller.start(request)

    def _retry_failed_publications(self) -> None:
        """Retry only accounts that failed in the previous operation."""
        if self._publishing_controller.is_running:
            return

        retry_request = self._build_failed_retry_request()
        if retry_request is None:
            return

        self._last_publish_request = retry_request
        self._last_publish_results = ()

        self._start_publishing(retry_request)

    def _handle_publish_request(
            self,
            request: PublishRequest,
    ) -> None:
        """Start a new publishing operation."""
        if self._publishing_controller.is_running:
            return

        self._last_publish_request = request
        self._last_publish_results = ()

        self._start_publishing(request)

    def _build_failed_retry_request(self) -> PublishRequest | None:
        """Build a retry request for the last failed accounts."""
        if self._last_publish_request is None:
            return None

        if not self._last_publish_results:
            return None

        return BuildRetryRequest.execute(
            self._last_publish_request,
            self._last_publish_results,
        )

    def _on_publish_progress(self, result: PublishResult) -> None:
        """Display progress and the outcome of the completed account."""
        self._publishing_completed += 1

        outcome = "Published" if result.succeeded else "Failed"

        self.publish_status.setText(
            f"Publishing {self._publishing_completed} "
            f"of {self._publishing_total} accounts...\n"
            f"{result.account.name} — {outcome}"
        )

    def _on_publish_results(
            self,
            results: tuple[PublishResult, ...],
    ) -> None:
        """Store publishing results and refresh the interface."""
        self._last_publish_results = results
        self.retry_failed_button.setEnabled(
            self._build_failed_retry_request() is not None
        )

        self.publish_status.show_results(results)
        self._refresh_recent_posts()

    def _on_publish_error(self, _message: str) -> None:
        """Clear retry state after an unexpected publishing error."""
        self._last_publish_request = None
        self._last_publish_results = ()

        self.retry_failed_button.setEnabled(False)
        self.publish_status.show_error()

    def _on_publishing_finished(self) -> None:
        """Restore publishing controls after thread cleanup."""
        self.post_editor.publish_button.setEnabled(True)

    def shutdown(self) -> None:
        """Wait for active publishing to finish."""
        self._publishing_controller.shutdown()
