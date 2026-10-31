from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWidgets import QDialog, QMessageBox

from socialflow.application.accounts.list_accounts import ListAccounts
from socialflow.application.publishing.list_recent_publications import (
    ListRecentPublications,
)
from socialflow.application.publishing.list_remote_posts import (
    ListRemotePosts,
)
from socialflow.application.publishing.list_trashed_remote_posts import (
    ListTrashedRemotePosts,
)
from socialflow.application.publishing.restore_remote_post import (
    RestoreRemotePost,
)
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.application.tags.create_tag import CreateTag
from socialflow.application.tags.list_tags import ListTags
from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_post import RemotePost
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.publish_request import PublishRequest
from socialflow.domain.publishing.publication import Publication
from socialflow.ui.posts.post_editor import PostEditor
from socialflow.ui.posts.publish_status import PublishStatus
from socialflow.ui.posts.recent_posts_panel import RecentPostsPanel
from socialflow.ui.posts.remote_posts_panel import RemotePostsPanel
from socialflow.ui.posts.remote_trashed_posts_panel import (
    RemoteTrashedPostsPanel,
)
from socialflow.ui.posts.publishing_controller import PublishingController
from socialflow.application.publishing.publish_result import PublishResult
from socialflow.application.publishing.build_retry_request import (
    BuildRetryRequest,
)
from socialflow.ui.workers.tag_loading_controller import (
    TagLoadingController,
)
from socialflow.ui.workers.remote_post_loading_controller import (
    RemotePostLoadingController,
)
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.application.publishing.update_remote_post import (
    UpdateRemotePost,
)
from socialflow.application.publishing.trash_remote_post import (
    TrashRemotePost,
)
from socialflow.ui.workers.remote_post_trashing_controller import (
    RemotePostTrashingController,
)
from socialflow.ui.workers.remote_post_restoring_controller import (
    RemotePostRestoringController,
)
from socialflow.ui.workers.remote_trashed_post_loading_controller import (
    RemoteTrashedPostLoadingController,
)
from socialflow.ui.workers.remote_post_updating_controller import (
    RemotePostUpdatingController,
)
from socialflow.ui.workers.wordpress_tag_preparation_controller import (
    WordPressTagPreparationController,
)
from socialflow.infrastructure.wordpress.wordpress_tag_creation_plan import (
    WordPressTagCreationPlan,
)
from socialflow.ui.dialogs.wordpress_tag_confirmation_dialog import (
    WordPressTagConfirmationDialog,
)
from socialflow.ui.workers.wordpress_tag_creation_controller import (
    WordPressTagCreationController,
)
from socialflow.application.tags.list_remote_tags import (
    ListRemoteTags,
)
from socialflow.domain.post.remote_tag import RemoteTag
from socialflow.domain.post.remote_category import RemoteCategory
from socialflow.application.categories.list_remote_categories import (
    ListRemoteCategories,
)
from socialflow.ui.workers.remote_category_loading_controller import (
    RemoteCategoryLoadingController,
)

from socialflow.ui.workers.remote_tag_loading_controller import (
    RemoteTagLoadingController,
)
from socialflow.application.publishing.list_remote_media import (
    ListRemoteMedia,
)
from socialflow.ui.posts.remote_media_selection_dialog import (
    RemoteMediaSelectionDialog,
)
from socialflow.ui.workers.remote_media_loading_controller import (
    RemoteMediaLoadingController,
)
from socialflow.ui.posts.create_post_view import CreatePostView
from socialflow.ui.posts.my_posts_view import MyPostsView
from socialflow.ui.posts.trash_view import TrashView
from socialflow.ui.dialogs.wordpress_category_dialog import (
    WordPressCategoryDialog,
)
from socialflow.ui.workers.wordpress_category_creation_controller import (
    WordPressCategoryCreationController,
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
        list_remote_posts: ListRemotePosts | None = None,
        update_remote_post: UpdateRemotePost | None = None,
        trash_remote_post: TrashRemotePost | None = None,
        list_trashed_remote_posts: ListTrashedRemotePosts | None = None,
        restore_remote_post: RestoreRemotePost | None = None,
        list_remote_tags: ListRemoteTags | None = None,
        wordpress_tag_preparation_controller: WordPressTagPreparationController | None = None,
        wordpress_tag_creation_controller: WordPressTagCreationController | None = None,
        list_remote_media: ListRemoteMedia | None = None,
        list_remote_categories: ListRemoteCategories | None = None,
        wordpress_category_creation_controller: (
            WordPressCategoryCreationController | None
        ) = None,
    ) -> None:
        super().__init__(parent)

        self._remote_media_loading_controller = (
            RemoteMediaLoadingController(
                list_remote_media=list_remote_media,
                parent=self,
            )
            if list_remote_media is not None
            else None
        )

        self._remote_media_dialog: RemoteMediaSelectionDialog | None = None
        self._remote_media_loading_account: Account | None = None
        self._remote_media_loading_generation: int | None = None
        self._remote_media_selected_post_id: str | None = None
        self._remote_media_loading_shutting_down = False

        if self._remote_media_loading_controller is not None:
            self._remote_media_loading_controller.media_ready.connect(
                self._on_remote_media_loaded
            )
            self._remote_media_loading_controller.error_occurred.connect(
                self._on_remote_media_error
            )
            self._remote_media_loading_controller.finished.connect(
                self._on_remote_media_loading_finished
            )

        self._list_remote_categories = list_remote_categories
        self._remote_category_loading_controller = (
            RemoteCategoryLoadingController(
                list_remote_categories=list_remote_categories,
                parent=self,
            )
            if list_remote_categories is not None
            else None
        )

        self._wordpress_category_creation_controller = (
            wordpress_category_creation_controller
        )
        self._category_creation_account: Account | None = None
        self._category_creation_generation: int | None = None
        self._category_creation_shutting_down = False
        self._pending_created_category_id: int | None = None
        self._pending_category_selection_ids: tuple[int, ...] = ()

        if self._wordpress_category_creation_controller is not None:
            creation_controller = (
                self._wordpress_category_creation_controller
            )
            creation_controller.setParent(self)
            creation_controller.category_created.connect(
                self._on_wordpress_category_created
            )
            creation_controller.error_occurred.connect(
                self._on_wordpress_category_creation_error
            )
            creation_controller.finished.connect(
                self._on_wordpress_category_creation_finished
            )

        self._remote_categories_generation = 0
        self._remote_category_loading_generation: int | None = None
        self._remote_category_loading_account: Account | None = None
        self._pending_remote_category_account: Account | None = None
        self._remote_category_loading_shutting_down = False

        if self._remote_category_loading_controller is not None:
            controller = self._remote_category_loading_controller
            controller.categories_ready.connect(
                self._on_remote_categories_loaded
            )
            controller.error_occurred.connect(
                self._on_remote_categories_error
            )
            controller.finished.connect(
                self._on_remote_category_loading_finished
            )

        self._list_remote_tags = list_remote_tags
        self._remote_tag_loading_controller = (
            RemoteTagLoadingController(
                list_remote_tags=list_remote_tags,
                parent=self,
            )
            if list_remote_tags is not None
            else None
        )

        self._remote_tags_generation = 0
        self._remote_tag_loading_generation: int | None = None
        self._remote_tag_loading_account: Account | None = None
        self._pending_remote_tag_account: Account | None = None
        self._loaded_remote_tags_account: Account | None = None
        self._loaded_remote_tags: tuple[RemoteTag, ...] = ()
        self._remote_tags_error: str | None = None
        self._remote_tag_loading_shutting_down = False

        if self._remote_tag_loading_controller is not None:
            self._remote_tag_loading_controller.tags_ready.connect(
                self._on_remote_tags_loaded
            )
            self._remote_tag_loading_controller.error_occurred.connect(
                self._on_remote_tags_error
            )
            self._remote_tag_loading_controller.finished.connect(
                self._on_remote_tag_loading_finished
            )
        self._wordpress_tag_preparation_controller = (
            wordpress_tag_preparation_controller
        )
        self._wordpress_tag_creation_controller = (
            wordpress_tag_creation_controller
        )

        if self._wordpress_tag_creation_controller is not None:
            self._wordpress_tag_creation_controller.setParent(self)

        if self._wordpress_tag_creation_controller is not None:
            self._wordpress_tag_creation_controller.tags_created.connect(
                self._on_wordpress_tags_created
            )
            self._wordpress_tag_creation_controller.error_occurred.connect(
                self._on_wordpress_tag_creation_error
            )
            self._wordpress_tag_creation_controller.finished.connect(
                self._on_wordpress_tag_creation_finished
            )

        if self._wordpress_tag_preparation_controller is not None:
            self._wordpress_tag_preparation_controller.setParent(self)

        self._pending_publish_request: PublishRequest | None = None
        self._pending_wordpress_accounts: list[Account] = []
        self._preparing_wordpress_account: Account | None = None
        self._wordpress_preparation_shutting_down = False

        self._approved_wordpress_tag_plans: dict[
            object,
            WordPressTagCreationPlan,
        ] = {}

        self._wordpress_tag_creation_failed = False
        self._wordpress_tag_creation_completed = False

        if self._wordpress_tag_preparation_controller is not None:
            self._wordpress_tag_preparation_controller.plan_ready.connect(
                self._on_wordpress_tag_plan_ready
            )
            self._wordpress_tag_preparation_controller.error_occurred.connect(
                self._on_wordpress_tag_preparation_error
            )
            self._wordpress_tag_preparation_controller.finished.connect(
                self._on_wordpress_tag_preparation_finished
            )

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

        self._tag_loading_controller = TagLoadingController(
            list_tags=list_tags,
            parent=self,
        )
        self._tag_loading_account: Account | None = None
        self._tags_generation = 0
        self._tag_loading_generation: int | None = None
        self._pending_tag_accounts: list[Account] = []
        self._tag_loading_shutting_down = False
        self._loaded_tags_by_account: dict[object, tuple[Tag, ...]] = {}
        self._tag_loading_controller.tags_ready.connect(
            self._on_tags_loaded
        )
        self._tag_loading_controller.finished.connect(
            self._on_tag_loading_finished
        )
        self._list_recent_publications = list_recent_publications
        self._remote_post_loading_controller = (
            RemotePostLoadingController(
                list_remote_posts=list_remote_posts,
                parent=self,
            )
            if list_remote_posts is not None
            else None
        )
        self._remote_post_updating_controller = (
            RemotePostUpdatingController(
                update_remote_post=update_remote_post,
                parent=self,
            )
            if update_remote_post is not None
            else None
        )
        self._remote_post_trashing_controller = (
            RemotePostTrashingController(
                trash_remote_post=trash_remote_post,
                parent=self,
            )
            if trash_remote_post is not None
            else None
        )

        self._remote_trashed_post_loading_controller = (
            RemoteTrashedPostLoadingController(
                list_trashed_remote_posts=list_trashed_remote_posts,
                parent=self,
            )
            if list_trashed_remote_posts is not None
            else None
        )

        self._remote_post_restoring_controller = (
            RemotePostRestoringController(
                restore_remote_post=restore_remote_post,
                parent=self,
            )
            if restore_remote_post is not None
            else None
        )

        self._remote_trashed_post_loading_shutting_down = False
        self._remote_post_restoring_shutting_down = False
        self._remote_post_restoring_account: Account | None = None
        self._remote_post_restoring_generation: int | None = None
        self._remote_post_restoring_succeeded = False

        if self._remote_post_restoring_controller is not None:
            self._remote_post_restoring_controller.post_restored.connect(
                self._on_remote_post_restored
            )
            self._remote_post_restoring_controller.error_occurred.connect(
                self._on_remote_post_restore_error
            )
            self._remote_post_restoring_controller.finished.connect(
                self._on_remote_post_restore_finished
            )

        self._trashed_posts_generation = 0
        self._trashed_post_loading_account: Account | None = None
        self._trashed_post_loading_generation: int | None = None
        self._pending_trashed_post_account: Account | None = None
        self._loaded_trashed_posts: tuple[RemotePost, ...] = ()
        self._loaded_trashed_posts_account: Account | None = None

        if self._remote_trashed_post_loading_controller is not None:
            self._remote_trashed_post_loading_controller.posts_ready.connect(
                self._on_trashed_posts_loaded
            )
            self._remote_trashed_post_loading_controller.error_occurred.connect(
                self._on_trashed_posts_error
            )
            self._remote_trashed_post_loading_controller.finished.connect(
                self._on_trashed_post_loading_finished
            )

        self._remote_post_trashing_shutting_down = False
        self._remote_post_trashing_account: Account | None = None
        self._remote_post_trashing_generation: int | None = None
        self._remote_post_trashing_succeeded = False

        self._remote_posts_generation = 0
        if self._remote_post_trashing_controller is not None:
            self._remote_post_trashing_controller.post_trashed.connect(
                self._on_remote_post_trashed
            )
            self._remote_post_trashing_controller.error_occurred.connect(
                self._on_remote_post_trash_error
            )
            self._remote_post_trashing_controller.finished.connect(
                self._on_remote_post_trash_finished
            )
        self._remote_post_updating_generation: int | None = None
        self._remote_post_updating_account: Account | None = None
        self._remote_post_update_succeeded = False
        self._remote_post_updating_shutting_down = False
        if self._remote_post_updating_controller is not None:
            self._remote_post_updating_controller.post_updated.connect(
                self._on_remote_post_updated
            )
            self._remote_post_updating_controller.error_occurred.connect(
                self._on_remote_post_update_error
            )
            self._remote_post_updating_controller.finished.connect(
                self._on_remote_post_update_finished
            )
        self._remote_post_loading_account: Account | None = None
        self._remote_post_loading_generation: int | None = None
        self._pending_remote_post_account: Account | None = None
        self._remote_post_loading_shutting_down = False
        self._loaded_remote_posts: tuple[RemotePost, ...] = ()
        self._loaded_remote_posts_account: Account | None = None
        self._remote_posts_error: str | None = None
        if self._remote_post_loading_controller is not None:
            self._remote_post_loading_controller.posts_ready.connect(
                self._on_remote_posts_loaded
            )
            self._remote_post_loading_controller.error_occurred.connect(
                self._on_remote_posts_error
            )
            self._remote_post_loading_controller.finished.connect(
                self._on_remote_post_loading_finished
            )

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
        self.remote_posts_panel = RemotePostsPanel(self)
        self.remote_posts_panel.save_requested.connect(
            self._handle_remote_post_save
        )
        self.remote_posts_panel.save_with_tags_requested.connect(
            self._handle_remote_post_save_with_tags
        )
        self.remote_posts_panel.save_with_media_requested.connect(
            self._handle_remote_post_save_with_media
        )
        self.remote_posts_panel.save_with_status_requested.connect(
            self._handle_remote_post_save_with_status
        )
        self.remote_posts_panel.save_with_excerpt_requested.connect(
            self._handle_remote_post_save_with_excerpt
        )
        self.remote_posts_panel.save_with_title_requested.connect(
            self._handle_remote_post_save_with_title
        )
        self.remote_posts_panel.browse_media_requested.connect(
            self._browse_remote_media
        )
        self.remote_posts_panel.trash_requested.connect(
            self._handle_remote_post_trash
        )

        self.remote_trashed_posts_panel = RemoteTrashedPostsPanel(self)
        self.remote_trashed_posts_panel.refresh_requested.connect(
            self._refresh_trashed_posts
        )
        self.remote_trashed_posts_panel.restore_requested.connect(
            self._handle_remote_post_restore
        )

        self.create_post_view = CreatePostView(self)
        self.my_posts_view = MyPostsView(self)
        self.trash_view = TrashView(self)

        self.create_post_view.content_layout.addWidget(
            self.post_editor
        )

        # Place New Post at the top-right of the composer.
        self.post_editor.composer_panel.layout().insertWidget(
            0,
            self.new_post_button,
            0,
            Qt.AlignmentFlag.AlignRight,
        )
        # Keep retry actions directly below Publish.
        publishing_layout = self.post_editor.publishing_panel.layout()
        publishing_layout.insertWidget(
            publishing_layout.count() - 1,
            self.retry_failed_button,
        )

        self.create_post_view.content_layout.addWidget(
            self.publish_status
        )

        # Keep WordPress posts and local history in the left column.
        self.remote_posts_panel.list_panel.layout().addWidget(
            self.recent_posts_panel
        )

        # The remote posts panel owns the two-column splitter.
        self.my_posts_view.content_layout.addWidget(
            self.remote_posts_panel
        )

        self.trash_view.content_layout.addWidget(
            self.remote_trashed_posts_panel
        )

        self.posts_tabs = QTabWidget(self)
        self.posts_tabs.addTab(
            self.create_post_view,
            "Create Post",
        )
        self.posts_tabs.addTab(
            self.my_posts_view,
            "My Posts",
        )
        self.posts_tabs.addTab(
            self.trash_view,
            "Trash",
        )

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(self.posts_tabs)

        self.post_editor.publish_requested.connect(
            self._handle_publish_request
        )

        self.post_editor.account_selection_changed.connect(
            self._refresh_available_tags
        )

        self.post_editor.account_selection_changed.connect(
            self._refresh_recent_posts
        )
        self.post_editor.account_selection_changed.connect(
            self._refresh_remote_posts
        )
        self.post_editor.account_selection_changed.connect(
            self._refresh_trashed_posts
        )
        self.post_editor.account_selection_changed.connect(
            self._refresh_remote_tags
        )
        self.post_editor.account_selection_changed.connect(
            self._refresh_remote_categories
        )

        self.post_editor.add_category_button.clicked.connect(
            self._add_wordpress_category
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
        self.post_editor.title_editor.textChanged.connect(
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
        self._refresh_trashed_posts()

    def refresh_accounts(self) -> None:
        """Refresh the accounts available for publishing."""
        self.post_editor.set_accounts(
            self._list_accounts.execute()
        )

    def _on_tags_loaded(self, tags: tuple[Tag, ...]) -> None:
        """Store tags only while the page is active and account selected."""
        if self._tag_loading_shutting_down:
            return

        account = self._tag_loading_account

        if account is None:
            return

        if account not in self.post_editor.selected_accounts():
            return

        if self._tag_loading_generation != self._tags_generation:
            return

        self._loaded_tags_by_account[account.id] = tags
        self._display_loaded_tags()

    def _display_loaded_tags(self) -> None:
        """Combine selected accounts' tags without duplicates."""
        tags: list[Tag] = []
        seen_tags: set[Tag] = set()

        for account in self.post_editor.selected_accounts():
            account_tags = self._loaded_tags_by_account.get(
                account.id,
                (),
            )

            for tag in account_tags:
                if tag not in seen_tags:
                    seen_tags.add(tag)
                    tags.append(tag)

        self.post_editor.tag_selector.set_available_tags(
            tuple(tags)
        )

    def _on_tag_loading_finished(self) -> None:
        """Continue loading queued accounts after thread cleanup."""
        self._tag_loading_account = None
        self._tag_loading_generation = None
        self._start_next_tag_loading()

    def _start_next_tag_loading(self) -> None:
        """Start the next queued account when the controller is idle."""
        if self._tag_loading_shutting_down:
            return
        if self._tag_loading_controller.is_running:
            return

        selected_accounts = self.post_editor.selected_accounts()

        while self._pending_tag_accounts:
            account = self._pending_tag_accounts.pop(0)

            if account not in selected_accounts:
                continue

            if account.id in self._loaded_tags_by_account:
                continue

            self._tag_loading_account = account
            self._tag_loading_generation = self._tags_generation
            self._tag_loading_controller.start(account)
            return

    def _refresh_available_tags(self) -> None:
        """Load WordPress tags in the background."""
        if self._tag_loading_shutting_down:
            return

        self._tags_generation += 1

        selected_accounts = self.post_editor.selected_accounts()
        selected_ids = {account.id for account in selected_accounts}

        self._loaded_tags_by_account = {
            account_id: tags
            for account_id, tags in self._loaded_tags_by_account.items()
            if account_id in selected_ids
        }

        self._pending_tag_accounts.clear()

        for account in selected_accounts:
            if account.id in self._loaded_tags_by_account:
                continue

            if account.destination == PublishingDestination.WORDPRESS:
                self._pending_tag_accounts.append(account)
                continue

            self._loaded_tags_by_account[account.id] = (
                self._list_tags.execute(account)
            )

        self._display_loaded_tags()
        self._start_next_tag_loading()


    def _selected_wordpress_account(self) -> Account | None:
        """Return the first selected WordPress account."""
        return next(
            (
                account
                for account in self.post_editor.selected_accounts()
                if account.destination == PublishingDestination.WORDPRESS
            ),
            None,
        )

    def _selected_category_wordpress_account(self) -> Account | None:
        """Return a WordPress account only when exactly one is selected."""
        accounts = tuple(
            account
            for account in self.post_editor.selected_accounts()
            if account.destination == PublishingDestination.WORDPRESS
        )

        return accounts[0] if len(accounts) == 1 else None




    def _refresh_remote_categories(self) -> None:
        """Queue category loading for the selected WordPress account."""
        if self._remote_category_loading_shutting_down:
            return

        self._remote_categories_generation += 1
        self._pending_created_category_id = None
        self._pending_category_selection_ids = ()

        account = self._selected_category_wordpress_account()
        self._pending_remote_category_account = account

        selector = self.post_editor.category_selector
        selector.setEnabled(False)
        selector.set_selected_ids(())
        selector.set_available_categories(())

        self.post_editor.add_category_button.setEnabled(False)

        self._start_remote_category_loading()

    def _start_remote_category_loading(self) -> None:
        """Start the latest queued request when the worker is idle."""
        controller = self._remote_category_loading_controller

        if (
            controller is None
            or self._remote_category_loading_shutting_down
            or controller.is_running
        ):
            return

        account = self._pending_remote_category_account
        self._pending_remote_category_account = None

        if account is None:
            return

        self._remote_category_loading_account = account
        self._remote_category_loading_generation = (
            self._remote_categories_generation
        )

        controller.start(account)

    def _is_current_remote_category_account(self) -> bool:
        """Reject results from an outdated WordPress account."""
        account = self._remote_category_loading_account

        if (
            account is None
            or self._remote_category_loading_shutting_down
        ):
            return False

        return (
                account == self._selected_category_wordpress_account()
                and self._pending_remote_category_account is None
                and self._remote_category_loading_generation
                == self._remote_categories_generation
        )

    def _on_remote_categories_loaded(
        self,
        categories: tuple[RemoteCategory, ...],
    ) -> None:
        """Display categories only for the current account."""
        if not self._is_current_remote_category_account():
            return

        selector = self.post_editor.category_selector
        selector.set_available_categories(categories)
        selector.setEnabled(True)

        if self._pending_created_category_id is not None:
            created_id = self._pending_created_category_id

            if any(
                    category.remote_id == created_id
                    for category in categories
            ):
                selector.set_selected_ids(
                    self._pending_category_selection_ids
                )

            self._pending_created_category_id = None
            self._pending_category_selection_ids = ()

        creation_controller = (
            self._wordpress_category_creation_controller
        )
        self.post_editor.add_category_button.setEnabled(
            creation_controller is not None
            and not creation_controller.is_running
            and not self._category_creation_shutting_down
        )

    def _on_remote_categories_error(self, _message: str) -> None:
        """Keep category controls disabled after retrieval fails."""
        if not self._is_current_remote_category_account():
            return

        selector = self.post_editor.category_selector
        selector.set_available_categories(())
        selector.setEnabled(False)
        self.post_editor.add_category_button.setEnabled(False)

    def _on_remote_category_loading_finished(self) -> None:
        """Start any newer queued request after thread cleanup."""
        self._remote_category_loading_account = None
        self._remote_category_loading_generation = None
        self._start_remote_category_loading()



    def _add_wordpress_category(self) -> None:
        """Ask the user to confirm a new WordPress category."""
        controller = self._wordpress_category_creation_controller
        account = self._selected_category_wordpress_account()
        selector = self.post_editor.category_selector

        if (
            controller is None
            or controller.is_running
            or self._category_creation_shutting_down
            or account is None
            or not selector.isEnabled()
        ):
            return

        dialog = WordPressCategoryDialog(
            categories=selector.available_categories(),
            parent=self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        if not dialog.is_confirmed():
            return

        # The account may have changed while the dialog was open.
        if (
                account != self._selected_category_wordpress_account()
                or not selector.isEnabled()
        ):
            return

        self._category_creation_account = account
        self._category_creation_generation = (
            self._remote_categories_generation
        )

        self.post_editor.add_category_button.setEnabled(False)

        controller.start(
            account=account,
            name=dialog.category_name(),
            parent_id=dialog.parent_category_id(),
        )

    def _is_current_category_creation(self) -> bool:
        """Check that creation still belongs to the selected account."""
        return (
                not self._category_creation_shutting_down
                and self._category_creation_account is not None
                and self._category_creation_account
                == self._selected_category_wordpress_account()
                and self._category_creation_generation
                == self._remote_categories_generation
        )

    def _on_wordpress_category_created(
        self,
        category: RemoteCategory,
    ) -> None:
        """Refresh categories and select the newly created category."""
        if not self._is_current_category_creation():
            return

        selector = self.post_editor.category_selector
        selected_ids = tuple(
            dict.fromkeys(
                (*selector.selected_ids(), category.remote_id)
            )
        )

        self._refresh_remote_categories()

        self._pending_created_category_id = category.remote_id
        self._pending_category_selection_ids = selected_ids

    def _on_wordpress_category_creation_error(
        self,
        message: str,
    ) -> None:
        """Report failures only for the current WordPress account."""
        if not self._is_current_category_creation():
            return

        QMessageBox.warning(
            self,
            "WordPress category creation failed",
            message,
        )

    def _on_wordpress_category_creation_finished(self) -> None:
        """Clear creation state after background thread cleanup."""
        account = self._category_creation_account
        self._category_creation_account = None
        self._category_creation_generation = None

        if self._category_creation_shutting_down:
            return

        if account != self._selected_category_wordpress_account():
            return

        # Re-enable only when the category list is available.
        loading = self._remote_category_loading_controller
        if (
            loading is not None
            and not loading.is_running
            and self.post_editor.category_selector.isEnabled()
        ):
            self.post_editor.add_category_button.setEnabled(True)



    def _refresh_remote_tags(self) -> None:
        """Queue tag retrieval for the selected WordPress account."""
        if self._remote_tag_loading_shutting_down:
            return
        self._remote_tags_generation += 1

        account = self._selected_wordpress_account()

        self._loaded_remote_tags = ()
        self._loaded_remote_tags_account = None
        self._remote_tags_error = None
        self._pending_remote_tag_account = account

        self.remote_posts_panel.set_available_remote_tags(())

        self._start_remote_tag_loading()


    def _start_remote_tag_loading(self) -> None:
        """Start the latest queued tag request when the worker is idle."""
        controller = self._remote_tag_loading_controller

        if (
            controller is None
            or self._remote_tag_loading_shutting_down
            or controller.is_running
        ):
            return

        account = self._pending_remote_tag_account
        self._pending_remote_tag_account = None

        if account is None:
            return

        self._remote_tag_loading_account = account
        self._remote_tag_loading_generation = (
            self._remote_tags_generation
        )
        controller.start(account)

    def _is_current_remote_tag_account(self) -> bool:
        """Reject results from an outdated account selection."""
        account = self._remote_tag_loading_account

        if account is None or self._remote_tag_loading_shutting_down:
            return False

        return (
                account == self._selected_wordpress_account()
                and self._pending_remote_tag_account is None
                and self._remote_tag_loading_generation
                == self._remote_tags_generation
        )


    def _on_remote_tags_loaded(
        self,
        tags: tuple[RemoteTag, ...],
    ) -> None:
        """Display remote tags only for the current WordPress account."""
        if not self._is_current_remote_tag_account():
            return

        self._loaded_remote_tags = tags
        self._loaded_remote_tags_account = (
            self._remote_tag_loading_account
        )
        self._remote_tags_error = None

        self.remote_posts_panel.set_available_remote_tags(tags)



    def _on_remote_tags_error(self, message: str) -> None:
        """Keep existing tag IDs available when name retrieval fails."""
        if not self._is_current_remote_tag_account():
            return

        self._loaded_remote_tags = ()
        self._loaded_remote_tags_account = None
        self._remote_tags_error = message

        self.remote_posts_panel.set_available_remote_tags(())

    def _on_remote_tag_loading_finished(self) -> None:
        """Start the latest queued request after thread cleanup."""
        self._remote_tag_loading_account = None
        self._remote_tag_loading_generation = None
        self._start_remote_tag_loading()


    def _refresh_remote_posts(self) -> None:
        """Queue retrieval for the first selected WordPress account."""
        if self._remote_post_loading_shutting_down:
            return

        controller = self._remote_post_loading_controller
        if controller is None:
            return

        self._remote_posts_generation += 1
        account = next(
            (
                selected
                for selected in self.post_editor.selected_accounts()
                if selected.destination == PublishingDestination.WORDPRESS
            ),
            None,
        )

        self._loaded_remote_posts = ()
        self._loaded_remote_posts_account = None
        self._remote_posts_error = None
        self._pending_remote_post_account = account
        if account is None:
            self.remote_posts_panel.show_empty()
        else:
            self.remote_posts_panel.show_loading()
        self._start_remote_post_loading()

    def _start_remote_post_loading(self) -> None:
        """Start the latest queued request once the controller is idle."""
        controller = self._remote_post_loading_controller
        if (
            controller is None
            or self._remote_post_loading_shutting_down
            or controller.is_running
        ):
            return

        account = self._pending_remote_post_account
        self._pending_remote_post_account = None
        if account is None:
            return

        self._remote_post_loading_account = account
        self._remote_post_loading_generation = (
            self._remote_posts_generation
        )
        controller.start(account)

    def _is_current_remote_post_account(self) -> bool:
        """Check whether the in-flight request still matches selection."""
        account = self._remote_post_loading_account
        if account is None or self._remote_post_loading_shutting_down:
            return False

        selected = next(
            (
                item
                for item in self.post_editor.selected_accounts()
                if item.destination == PublishingDestination.WORDPRESS
            ),
            None,
        )
        return (
                account == selected
                and self._pending_remote_post_account is None
                and self._remote_post_loading_generation
                == self._remote_posts_generation
        )

    def _on_remote_posts_loaded(self, posts: tuple) -> None:
        """Display remote posts for the currently selected account."""
        if not self._is_current_remote_post_account():
            return

        self._loaded_remote_posts = posts
        self._loaded_remote_posts_account = (
            self._remote_post_loading_account
        )
        self.remote_posts_panel.show_posts(posts)

    def _on_remote_posts_error(self, message: str) -> None:
        """Display remote retrieval errors."""
        if not self._is_current_remote_post_account():
            return

        self.remote_posts_panel.show_error(message)


    def _on_remote_post_loading_finished(self) -> None:
        """Process the latest request after worker thread cleanup."""
        self._remote_post_loading_account = None
        self._remote_post_loading_generation = None
        self._start_remote_post_loading()

    def _refresh_trashed_posts(self) -> None:
        """Queue Trash retrieval for the selected WordPress account."""
        if self._remote_trashed_post_loading_shutting_down:
            return

        controller = self._remote_trashed_post_loading_controller
        if controller is None:
            return

        self._trashed_posts_generation += 1
        account = self._selected_wordpress_account()

        self._loaded_trashed_posts = ()
        self._loaded_trashed_posts_account = None
        self._pending_trashed_post_account = account

        if account is None:
            self.remote_trashed_posts_panel.show_empty()
        else:
            self.remote_trashed_posts_panel.show_loading()

        restore_controller = self._remote_post_restoring_controller
        if (
                restore_controller is not None
                and restore_controller.is_running
        ):
            self.remote_trashed_posts_panel.set_restoring(True)

        self._start_trashed_post_loading()

    def _start_trashed_post_loading(self) -> None:
        """Start the latest Trash request when its controller is idle."""
        controller = self._remote_trashed_post_loading_controller

        if (
            controller is None
            or self._remote_trashed_post_loading_shutting_down
            or controller.is_running
        ):
            return

        account = self._pending_trashed_post_account
        self._pending_trashed_post_account = None

        if account is None:
            return

        self._trashed_post_loading_account = account
        self._trashed_post_loading_generation = (
            self._trashed_posts_generation
        )
        controller.start(account)

    def _is_current_trashed_post_account(self) -> bool:
        """Reject Trash results from an outdated account selection."""
        account = self._trashed_post_loading_account

        if (
            account is None
            or self._remote_trashed_post_loading_shutting_down
        ):
            return False

        return (
            account == self._selected_wordpress_account()
            and self._pending_trashed_post_account is None
            and self._trashed_post_loading_generation
            == self._trashed_posts_generation
        )

    def _on_trashed_posts_loaded(
        self,
        posts: tuple[RemotePost, ...],
    ) -> None:
        """Display Trash results only for the current account."""
        if not self._is_current_trashed_post_account():
            return

        self._loaded_trashed_posts = posts
        self._loaded_trashed_posts_account = (
            self._trashed_post_loading_account
        )
        self.remote_trashed_posts_panel.show_posts(posts)

        restore_controller = self._remote_post_restoring_controller
        if (
                restore_controller is not None
                and restore_controller.is_running
        ):
            self.remote_trashed_posts_panel.set_restoring(True)

    def _on_trashed_posts_error(self, message: str) -> None:
        """Display a Trash retrieval error for the current account."""
        if not self._is_current_trashed_post_account():
            return

        self._loaded_trashed_posts = ()
        self._loaded_trashed_posts_account = None
        self.remote_trashed_posts_panel.show_error(message)

        restore_controller = self._remote_post_restoring_controller

        if (
                restore_controller is not None
                and restore_controller.is_running
        ):
            self.remote_trashed_posts_panel.set_restoring(True)

    def _on_trashed_post_loading_finished(self) -> None:
        """Continue with the latest queued request after cleanup."""
        self._trashed_post_loading_account = None
        self._trashed_post_loading_generation = None
        self._start_trashed_post_loading()

    def _handle_remote_post_restore(self, remote_id: str) -> None:
        """Confirm restoring a trashed WordPress post as a draft."""
        controller = self._remote_post_restoring_controller
        trash_controller = self._remote_post_trashing_controller
        update_controller = self._remote_post_updating_controller

        if (
            controller is None
            or self._remote_post_restoring_shutting_down
            or controller.is_running
            or (
                trash_controller is not None
                and trash_controller.is_running
            )
            or (
                update_controller is not None
                and update_controller.is_running
            )
        ):
            return

        account = self._selected_wordpress_account()

        if (
            account is None
            or account != self._loaded_trashed_posts_account
        ):
            return

        post = self.remote_trashed_posts_panel.selected_post()

        if (
            post is None
            or post.remote_id != remote_id
            or post not in self._loaded_trashed_posts
        ):
            return

        try:
            post_id = int(remote_id)
        except (TypeError, ValueError):
            return

        if post_id <= 0:
            return

        confirmation = QMessageBox.question(
            self,
            "Restore WordPress post",
            (
                "Restore this WordPress post from Trash?\n\n"
                f"Title: {post.title or '(Untitled)'}\n"
                f"Post ID: {post_id}\n\n"
                "The post will be restored as a Draft. "
                "It will not be published automatically."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        # Revalidate after the modal dialog.
        if (
            self._remote_post_restoring_shutting_down
            or controller.is_running
            or (
                trash_controller is not None
                and trash_controller.is_running
            )
            or (
                update_controller is not None
                and update_controller.is_running
            )
            or account != self._selected_wordpress_account()
            or account != self._loaded_trashed_posts_account
            or self.remote_trashed_posts_panel.selected_post() != post
            or post not in self._loaded_trashed_posts
        ):
            return

        self._remote_post_restoring_account = account
        self._remote_post_restoring_generation = (
            self._trashed_posts_generation
        )
        self._remote_post_restoring_succeeded = False

        self.remote_trashed_posts_panel.set_restoring(True)
        self.remote_trashed_posts_panel.status_label.setText(
            "Restoring WordPress post as Draft..."
        )

        controller.start(
            account=account,
            post_id=post_id,
        )

    def _on_remote_post_restored(self) -> None:
        """Record a confirmed successful Restore operation."""
        if not self._remote_post_restoring_shutting_down:
            self._remote_post_restoring_succeeded = True

    def _on_remote_post_restore_error(self, message: str) -> None:
        """Report Restore failure for the current account."""
        if self._remote_post_restoring_shutting_down:
            return

        if (
            self._remote_post_restoring_account
            != self._loaded_trashed_posts_account
            or self._remote_post_restoring_generation
            != self._trashed_posts_generation
        ):
            return

        self.remote_trashed_posts_panel.status_label.setText(
            f"Unable to restore WordPress post: {message}"
        )

    def _on_remote_post_restore_finished(self) -> None:
        """Refresh both lists after a successful Restore operation."""
        if self._remote_post_restoring_shutting_down:
            return

        account = self._remote_post_restoring_account
        generation = self._remote_post_restoring_generation
        succeeded = self._remote_post_restoring_succeeded

        self._remote_post_restoring_account = None
        self._remote_post_restoring_generation = None
        self._remote_post_restoring_succeeded = False

        if (
                account is None
                or account != self._selected_wordpress_account()
                or generation != self._trashed_posts_generation
        ):
            if self._loaded_trashed_posts_account is not None:
                self.remote_trashed_posts_panel.set_restoring(False)
            return

        if succeeded:
            self._refresh_trashed_posts()
            self._refresh_remote_posts()
        else:
            self.remote_trashed_posts_panel.set_restoring(False)

    def _browse_remote_media(self) -> None:
        """Open the media picker and start loading WordPress images."""
        controller = self._remote_media_loading_controller

        if (
            controller is None
            or self._remote_media_loading_shutting_down
            or controller.is_running
            or self._remote_media_dialog is not None
        ):
            return

        account = self._selected_wordpress_account()

        if (
            account is None
            or account != self._loaded_remote_posts_account
            or not self.remote_posts_panel.browse_media_button.isEnabled()
        ):
            return

        dialog = RemoteMediaSelectionDialog(self)
        dialog.show_loading()

        self._remote_media_dialog = dialog
        self._remote_media_loading_account = account
        self._remote_media_loading_generation = (
            self._remote_posts_generation
        )

        selected_row = self.remote_posts_panel.posts_list.currentRow()
        self._remote_media_selected_post_id = (
            self._loaded_remote_posts[selected_row].remote_id
            if 0 <= selected_row < len(self._loaded_remote_posts)
            else None
        )

        dialog.finished.connect(self._on_remote_media_dialog_finished)

        dialog.open()
        controller.start(account=account)

    def _is_current_remote_media_account(self) -> bool:
        """Check that the picker still belongs to the selected account."""
        return (
                not self._remote_media_loading_shutting_down
                and self._remote_media_dialog is not None
                and self._remote_media_loading_account is not None
                and self._remote_media_loading_account
                == self._loaded_remote_posts_account
                and self._remote_media_loading_account
                == self._selected_wordpress_account()
                and self._remote_media_loading_generation
                == self._remote_posts_generation
        )

    def _on_remote_media_loaded(self, media: tuple) -> None:
        """Display retrieved images in the active picker."""
        if not self._is_current_remote_media_account():
            return

        dialog = self._remote_media_dialog
        if dialog is not None:
            dialog.show_media(media)

    def _on_remote_media_error(self, message: str) -> None:
        """Display a media retrieval error in the picker."""
        if not self._is_current_remote_media_account():
            return

        dialog = self._remote_media_dialog
        if dialog is not None:
            dialog.show_error(message)

    def _on_remote_media_loading_finished(self) -> None:
        """Retain the request account while its dialog is open."""
        if self._remote_media_dialog is None:
            self._remote_media_loading_account = None
            self._remote_media_loading_generation = None

    def _on_remote_media_dialog_finished(self, result: int) -> None:
        """Apply media only to the post that opened the picker."""
        dialog = self._remote_media_dialog
        if dialog is None:
            return

        selected_row = self.remote_posts_panel.posts_list.currentRow()

        current_post_id = (
            self._loaded_remote_posts[selected_row].remote_id
            if 0 <= selected_row < len(self._loaded_remote_posts)
            else None
        )

        selection_is_current = (
                self._is_current_remote_media_account()
                and self._remote_media_selected_post_id is not None
                and self._remote_media_selected_post_id == current_post_id
        )

        media_id = (
            dialog.selected_media_id()
            if result == QDialog.DialogCode.Accepted
            else None
        )

        self._remote_media_dialog = None
        self._remote_media_loading_account = None
        self._remote_media_loading_generation = None
        self._remote_media_selected_post_id = None

        if (
                media_id is not None
                and selection_is_current
                and self.remote_posts_panel.browse_media_button.isEnabled()
        ):
            self.remote_posts_panel.apply_selected_media(media_id)

        dialog.deleteLater()

    def _handle_remote_post_save(
            self,
            remote_id: str,
            content: str,
            tags: tuple[int, ...] | None = None,
            featured_media_id: int | None = None,
            status: str | None = None,
            excerpt: str | None = None,
            title: str | None = None,
    ) -> None:
        """Save an existing WordPress post asynchronously."""
        controller = self._remote_post_updating_controller
        trash_controller = self._remote_post_trashing_controller
        restore_controller = vars(self).get(
            "_remote_post_restoring_controller"
        )

        if (
                trash_controller is not None
                and trash_controller.is_running
        ):
            return
        if (
                restore_controller is not None
                and restore_controller.is_running
        ):
            self.remote_posts_panel.restore_editing()
            return
        if (
                controller is None
                or self._remote_post_updating_shutting_down
                or controller.is_running
        ):
            self.remote_posts_panel.restore_editing()
            return

        account = next(
            (
                selected
                for selected in self.post_editor.selected_accounts()
                if selected.destination == PublishingDestination.WORDPRESS
            ),
            None,
        )

        if (
                account is None
                or account != self._loaded_remote_posts_account
        ):
            self.remote_posts_panel.restore_editing()
            return

        if not any(
                post.remote_id == remote_id
                for post in self._loaded_remote_posts
        ):
            self.remote_posts_panel.restore_editing()
            return

        try:
            post_id = int(remote_id)
        except (ValueError, TypeError):
            self.remote_posts_panel.status_label.setText(
                "Invalid WordPress post ID."
            )
            self.remote_posts_panel.restore_editing()
            return

        if post_id <= 0 or not content.strip():
            self.remote_posts_panel.restore_editing()
            return

        self._remote_post_updating_account = account
        self._remote_post_updating_generation = (
            self._remote_posts_generation
        )
        self._remote_post_update_succeeded = False
        self.remote_posts_panel.save_button.setEnabled(False)
        self.remote_posts_panel.content_editor.setEnabled(False)
        self.remote_posts_panel.post_title_editor.setEnabled(False)
        self.remote_posts_panel.excerpt_editor.setEnabled(False)
        self.remote_posts_panel.post_status_selector.setEnabled(False)
        self.remote_posts_panel.remote_tag_selector.tags_list.setEnabled(
            False
        )
        self.remote_posts_panel.featured_media_checkbox.setEnabled(False)
        self.remote_posts_panel.featured_media_input.setEnabled(False)
        self.remote_posts_panel.status_label.setText(
            "Saving WordPress post..."
        )

        update_kwargs = {
            "account": account,
            "post_id": post_id,
            "content": content,
        }

        if tags is not None:
            update_kwargs["tags"] = tags

        if featured_media_id is not None:
            update_kwargs["featured_media_id"] = featured_media_id

        if status is not None:
            update_kwargs["status"] = status

        if excerpt is not None:
            update_kwargs["excerpt"] = excerpt

        if title is not None:
            update_kwargs["title"] = title

        controller.start(**update_kwargs)


    def _handle_remote_post_save_with_tags(
        self,
        remote_id: str,
        content: str,
        tags: tuple[int, ...],
    ) -> None:
        """Forward a tag-aware remote-post update."""
        if not isinstance(tags, tuple) or any(
            type(tag_id) is not int or tag_id <= 0
            for tag_id in tags
        ):
            self.remote_posts_panel.status_label.setText(
                "WordPress tag IDs must be positive integers."
            )
            self.remote_posts_panel.restore_editing()
            return

        self._handle_remote_post_save(
            remote_id,
            content,
            tags=tags,
        )

    def _handle_remote_post_save_with_media(
        self,
        remote_id: str,
        content: str,
        tags: tuple[int, ...] | None,
        featured_media_id: int,
    ) -> None:
        """Forward a remote-post update involving featured media."""
        if tags is not None and (
            not isinstance(tags, tuple)
            or any(
                type(tag_id) is not int or tag_id <= 0
                for tag_id in tags
            )
        ):
            self.remote_posts_panel.status_label.setText(
                "WordPress tag IDs must be positive integers."
            )
            self.remote_posts_panel.restore_editing()
            return

        if (
            type(featured_media_id) is not int
            or featured_media_id < 0
        ):
            self.remote_posts_panel.status_label.setText(
                "WordPress featured media ID must be "
                "a non-negative integer."
            )
            self.remote_posts_panel.restore_editing()
            return

        self._handle_remote_post_save(
            remote_id,
            content,
            tags=tags,
            featured_media_id=featured_media_id,
        )


    def _handle_remote_post_save_with_excerpt(
        self,
        remote_id: str,
        content: str,
        tags: tuple[int, ...] | None,
        featured_media_id: int | None,
        status: str | None,
        excerpt: str,
    ) -> None:
        """Forward an update containing a changed WordPress excerpt."""
        if type(excerpt) is not str:
            self.remote_posts_panel.status_label.setText(
                "WordPress excerpt must be a string."
            )
            self.remote_posts_panel.restore_editing()
            return

        if tags is not None and (
            not isinstance(tags, tuple)
            or any(
                type(tag_id) is not int or tag_id <= 0
                for tag_id in tags
            )
        ):
            self.remote_posts_panel.status_label.setText(
                "WordPress tag IDs must be positive integers."
            )
            self.remote_posts_panel.restore_editing()
            return

        if featured_media_id is not None and (
            type(featured_media_id) is not int
            or featured_media_id < 0
        ):
            self.remote_posts_panel.status_label.setText(
                "WordPress featured media ID must be "
                "a non-negative integer."
            )
            self.remote_posts_panel.restore_editing()
            return

        if status is not None and status not in (
            "draft", "pending", "private", "publish"
        ):
            self.remote_posts_panel.status_label.setText(
                "Unsupported WordPress post status."
            )
            self.remote_posts_panel.restore_editing()
            return

        self._handle_remote_post_save(
            remote_id,
            content,
            tags=tags,
            featured_media_id=featured_media_id,
            status=status,
            excerpt=excerpt,
        )


    def _handle_remote_post_save_with_title(
        self,
        remote_id: str,
        content: str,
        tags: tuple[int, ...] | None,
        featured_media_id: int | None,
        status: str | None,
        excerpt: str | None,
        title: str,
    ) -> None:
        """Forward an update containing a changed WordPress title."""
        if type(title) is not str or not title.strip():
            self.remote_posts_panel.status_label.setText(
                "WordPress post title must be a non-empty string."
            )
            self.remote_posts_panel.restore_editing()
            return

        if excerpt is not None and type(excerpt) is not str:
            self.remote_posts_panel.status_label.setText(
                "WordPress excerpt must be a string."
            )
            self.remote_posts_panel.restore_editing()
            return

        if tags is not None and (
            not isinstance(tags, tuple)
            or any(
                type(tag_id) is not int or tag_id <= 0
                for tag_id in tags
            )
        ):
            self.remote_posts_panel.status_label.setText(
                "WordPress tag IDs must be positive integers."
            )
            self.remote_posts_panel.restore_editing()
            return

        if featured_media_id is not None and (
            type(featured_media_id) is not int
            or featured_media_id < 0
        ):
            self.remote_posts_panel.status_label.setText(
                "WordPress featured media ID must be "
                "a non-negative integer."
            )
            self.remote_posts_panel.restore_editing()
            return

        if status is not None and status not in (
            "draft", "pending", "private", "publish"
        ):
            self.remote_posts_panel.status_label.setText(
                "Unsupported WordPress post status."
            )
            self.remote_posts_panel.restore_editing()
            return

        self._handle_remote_post_save(
            remote_id,
            content,
            tags=tags,
            featured_media_id=featured_media_id,
            status=status,
            excerpt=excerpt,
            title=title,
        )


    def _handle_remote_post_save_with_status(
            self,
            remote_id: str,
            content: str,
            tags: tuple[int, ...] | None,
            featured_media_id: int | None,
            status: str,
    ) -> None:
        """Forward a WordPress post update involving status."""
        if status not in (
                "draft",
                "pending",
                "private",
                "publish",
        ):
            self.remote_posts_panel.status_label.setText(
                "Unsupported WordPress post status."
            )
            self.remote_posts_panel.restore_editing()
            return

        if tags is not None and (
                not isinstance(tags, tuple)
                or any(
            type(tag_id) is not int or tag_id <= 0
            for tag_id in tags
        )
        ):
            self.remote_posts_panel.status_label.setText(
                "WordPress tag IDs must be positive integers."
            )
            self.remote_posts_panel.restore_editing()
            return

        if featured_media_id is not None and (
                type(featured_media_id) is not int
                or featured_media_id < 0
        ):
            self.remote_posts_panel.status_label.setText(
                "WordPress featured media ID must be "
                "a non-negative integer."
            )
            self.remote_posts_panel.restore_editing()
            return

        self._handle_remote_post_save(
            remote_id,
            content,
            tags=tags,
            featured_media_id=featured_media_id,
            status=status,
        )


    def _handle_remote_post_trash(self, remote_id: str) -> None:
        """Confirm and start moving a selected post to Trash."""
        controller = self._remote_post_trashing_controller
        update_controller = self._remote_post_updating_controller
        restore_controller = vars(self).get(
            "_remote_post_restoring_controller"
        )

        if (
            controller is None
            or self._remote_post_trashing_shutting_down
            or controller.is_running
            or (
                update_controller is not None
                and update_controller.is_running
            )
            or (
                restore_controller is not None
                and restore_controller.is_running
            )
        ):
            return

        account = self._selected_wordpress_account()

        if (
            account is None
            or account != self._loaded_remote_posts_account
        ):
            return

        row = self.remote_posts_panel.posts_list.currentRow()

        if not 0 <= row < len(self._loaded_remote_posts):
            return

        post = self._loaded_remote_posts[row]

        if post.remote_id != remote_id:
            return

        try:
            post_id = int(remote_id)
        except (TypeError, ValueError):
            return

        if post_id <= 0:
            return

        confirmation = QMessageBox.question(
            self,
            "Move WordPress post to Trash",
            (
                "Move the selected WordPress post to Trash?\n\n"
                f"Title: {post.title or '(Untitled)'}\n"
                f"Post ID: {post_id}\n\n"
                "This does not permanently delete the post."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        # Revalidate selection after the modal confirmation.
        if (
            self._remote_post_trashing_shutting_down
            or controller.is_running
                or (
                update_controller is not None
                and update_controller.is_running
            )
                or (
                restore_controller is not None
                and restore_controller.is_running
            )
                or account != self._selected_wordpress_account()
            or account != self._loaded_remote_posts_account
            or self.remote_posts_panel.posts_list.currentRow() != row
            or row >= len(self._loaded_remote_posts)
            or self._loaded_remote_posts[row].remote_id != remote_id
        ):
            return

        self._remote_post_trashing_account = account
        self._remote_post_trashing_generation = (
            self._remote_posts_generation
        )
        self._remote_post_trashing_succeeded = False

        self.remote_posts_panel.set_trashing(True)
        self.remote_posts_panel.status_label.setText(
            "Moving WordPress post to Trash..."
        )

        controller.start(
            account=account,
            post_id=post_id,
        )

    def _on_remote_post_trashed(self) -> None:
        """Record a confirmed successful Trash operation."""
        if not self._remote_post_trashing_shutting_down:
            self._remote_post_trashing_succeeded = True

    def _on_remote_post_trash_error(self, message: str) -> None:
        """Report a Trash failure without removing the post."""
        if self._remote_post_trashing_shutting_down:
            return

        if (
            self._remote_post_trashing_account
            != self._loaded_remote_posts_account
            or self._remote_post_trashing_generation
            != self._remote_posts_generation
        ):
            return

        self.remote_posts_panel.status_label.setText(
            f"Unable to move WordPress post to Trash: {message}"
        )

    def _on_remote_post_trash_finished(self) -> None:
        """Refresh only after confirmed success and thread cleanup."""
        if self._remote_post_trashing_shutting_down:
            return

        account = self._remote_post_trashing_account
        generation = self._remote_post_trashing_generation
        succeeded = self._remote_post_trashing_succeeded

        self._remote_post_trashing_account = None
        self._remote_post_trashing_generation = None
        self._remote_post_trashing_succeeded = False

        if (
            account is None
            or account != self._loaded_remote_posts_account
            or generation != self._remote_posts_generation
        ):
            return

        if succeeded:
            self.remote_posts_panel.status_label.setText(
                "WordPress post moved to Trash successfully."
            )
            self._refresh_remote_posts()
            self._refresh_trashed_posts()
        else:
            self.remote_posts_panel.restore_editing()


    def _on_remote_post_updated(self) -> None:
        """Record a successful update."""
        if self._remote_post_updating_shutting_down:
            return

        self._remote_post_update_succeeded = True

    def _on_remote_post_update_error(
        self,
        message: str,
    ) -> None:
        """Display update errors for the active account."""
        if self._remote_post_updating_shutting_down:
            return

        account = self._remote_post_updating_account

        if (
                account is None
                or account != self._loaded_remote_posts_account
                or self._remote_post_updating_generation
                != self._remote_posts_generation
        ):
            return

        self.remote_posts_panel.status_label.setText(
            f"Unable to update WordPress post: {message}"
        )
        self.remote_posts_panel.restore_editing()

    def _on_remote_post_update_finished(self) -> None:
        """Refresh posts after the update thread has stopped."""
        if self._remote_post_updating_shutting_down:
            return

        account = self._remote_post_updating_account
        generation = self._remote_post_updating_generation
        succeeded = self._remote_post_update_succeeded

        self._remote_post_updating_account = None
        self._remote_post_updating_generation = None
        self._remote_post_update_succeeded = False

        if (
                account is None
                or account != self._loaded_remote_posts_account
                or generation != self._remote_posts_generation
        ):
            return

        if succeeded:
            self.remote_posts_panel.status_label.setText(
                "WordPress post updated successfully."
            )
            self._refresh_remote_posts()
        else:
            self.remote_posts_panel.restore_editing()

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

            self._loaded_tags_by_account.pop(account.id, None)

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

    def _begin_wordpress_tag_preparation(
            self,
            request: PublishRequest,
    ) -> None:
        """Check selected WordPress accounts before publishing."""
        if self._publishing_workflow_is_busy():
            return

        controller = self._wordpress_tag_preparation_controller

        wordpress_accounts = [
            account
            for account in request.accounts
            if account.destination == PublishingDestination.WORDPRESS
        ]

        if not wordpress_accounts or not request.post.tags:
            self._start_publishing(request)
            return

        if controller is None:
            self.publish_status.setText(
                "WordPress tag preparation is unavailable."
            )
            return

        self._pending_publish_request = request
        self._pending_wordpress_accounts = wordpress_accounts

        self.post_editor.publish_button.setEnabled(False)
        self.retry_failed_button.setEnabled(False)

        self.publish_status.setText(
            "Checking WordPress tags before publishing..."
        )

        self._start_next_wordpress_tag_preparation()

    def _start_next_wordpress_tag_preparation(self) -> None:
        """Prepare tags for the next selected WordPress account."""
        controller = self._wordpress_tag_preparation_controller

        if (
                controller is None
                or self._wordpress_preparation_shutting_down
                or controller.is_running
                or self._pending_publish_request is None
        ):
            return

        if not self._pending_wordpress_accounts:
            return

        account = self._pending_wordpress_accounts.pop(0)
        self._preparing_wordpress_account = account

        controller.start(
            account=account,
            selected_tags=self._pending_publish_request.post.tags,
        )

    def _on_wordpress_tag_plan_ready(
            self,
            plan: WordPressTagCreationPlan,
    ) -> None:
        """Request confirmation for missing WordPress tags."""
        if (
                self._wordpress_preparation_shutting_down
                or self._pending_publish_request is None
        ):
            return

        if not plan.requires_confirmation:
            return

        account = self._preparing_wordpress_account

        if account is None:
            self._cancel_wordpress_tag_preparation()
            return

        dialog = WordPressTagConfirmationDialog(
            plan=plan,
            parent=self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.publish_status.setText(
                "Publishing cancelled. WordPress tags were not approved."
            )
            self._cancel_wordpress_tag_preparation()
            return

        if self._wordpress_tag_creation_controller is None:
            self.publish_status.setText(
                "WordPress tag creation is unavailable."
            )
            self._cancel_wordpress_tag_preparation()
            return

        self._approved_wordpress_tag_plans[account.id] = plan

        self.publish_status.setText(
            f"WordPress tag creation approved for {account.name}."
        )

    def _on_wordpress_tag_preparation_error(self, message: str) -> None:
        """Cancel publishing when tag preparation fails."""
        if self._wordpress_preparation_shutting_down:
            return

        self.publish_status.setText(
            f"Unable to prepare WordPress tags: {message}"
        )
        self._cancel_wordpress_tag_preparation()

    def _on_wordpress_tag_preparation_finished(self) -> None:
        """Start approved creation or continue checking accounts."""
        if self._wordpress_preparation_shutting_down:
            return

        account = self._preparing_wordpress_account
        self._preparing_wordpress_account = None

        if self._pending_publish_request is None:
            return

        if account is not None:
            plan = self._approved_wordpress_tag_plans.pop(
                account.id,
                None,
            )

            if plan is not None:
                controller = self._wordpress_tag_creation_controller

                if controller is None:
                    self._cancel_wordpress_tag_preparation()
                    return

                self._preparing_wordpress_account = account
                self._wordpress_tag_creation_failed = False
                self._wordpress_tag_creation_completed = False

                self.publish_status.setText(
                    f"Creating approved WordPress tags for {account.name}..."
                )

                controller.start(
                    account=account,
                    plan=plan,
                )
                return

        self._continue_wordpress_tag_preparation()

    def _continue_wordpress_tag_preparation(self) -> None:
        """Check remaining accounts or begin publishing."""
        if (
                self._wordpress_preparation_shutting_down
                or self._pending_publish_request is None
        ):
            return

        if self._pending_wordpress_accounts:
            self._start_next_wordpress_tag_preparation()
            return

        request = self._pending_publish_request

        self._pending_publish_request = None
        self._pending_wordpress_accounts.clear()
        self._approved_wordpress_tag_plans.clear()

        self._start_publishing(request)

    def _on_wordpress_tags_created(self, _tags: object) -> None:
        """Record success only for an active tag-creation workflow."""
        if self._wordpress_preparation_shutting_down:
            return

        if (
                self._pending_publish_request is None
                or self._preparing_wordpress_account is None
        ):
            return

        self._wordpress_tag_creation_completed = True

    def _on_wordpress_tag_creation_error(self, message: str) -> None:
        """Handle creation errors only for an active workflow."""
        if self._wordpress_preparation_shutting_down:
            return

        if (
                self._pending_publish_request is None
                or self._preparing_wordpress_account is None
        ):
            return

        self._wordpress_tag_creation_failed = True

        self.publish_status.setText(
            f"Unable to create WordPress tags: {message}"
        )

        self._cancel_wordpress_tag_preparation()

    def _on_wordpress_tag_creation_finished(self) -> None:
        """Continue only after successful creation and thread cleanup."""
        if (
                self._wordpress_preparation_shutting_down
                or self._pending_publish_request is None
                or self._preparing_wordpress_account is None
        ):
            return

        succeeded = (
                self._wordpress_tag_creation_completed
                and not self._wordpress_tag_creation_failed
        )

        self._wordpress_tag_creation_completed = False
        self._wordpress_tag_creation_failed = False
        self._preparing_wordpress_account = None

        if not succeeded:
            self._cancel_wordpress_tag_preparation()
            return

        self._continue_wordpress_tag_preparation()

    def _cancel_wordpress_tag_preparation(self) -> None:
        """Discard the pending request and all approvals."""
        self._pending_publish_request = None
        self._pending_wordpress_accounts.clear()
        self._approved_wordpress_tag_plans.clear()

        self._preparing_wordpress_account = None
        self._wordpress_tag_creation_completed = False
        self._wordpress_tag_creation_failed = False

        self.post_editor.publish_button.setEnabled(True)
        self.retry_failed_button.setEnabled(
            self._build_failed_retry_request() is not None
        )

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

    def _publishing_workflow_is_busy(self) -> bool:
        """Check whether publishing or WordPress tag processing is active."""
        if self._wordpress_preparation_shutting_down:
            return True

        if self._pending_publish_request is not None:
            return True

        if self._publishing_controller.is_running:
            return True

        preparation = self._wordpress_tag_preparation_controller

        if preparation is not None and preparation.is_running:
            return True

        creation = self._wordpress_tag_creation_controller

        if creation is not None and creation.is_running:
            return True

        return False

    def _retry_failed_publications(self) -> None:
        """Retry only accounts that failed in the previous operation."""
        if self._publishing_workflow_is_busy():
            return

        retry_request = self._build_failed_retry_request()
        if retry_request is None:
            return

        self._last_publish_request = retry_request
        self._last_publish_results = ()

        self._begin_wordpress_tag_preparation(retry_request)

    def _handle_publish_request(
            self,
            request: PublishRequest,
    ) -> None:
        """Start a new publishing operation."""
        if self._publishing_workflow_is_busy():
            return

        self._last_publish_request = request
        self._last_publish_results = ()

        self._begin_wordpress_tag_preparation(request)

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
        if self._wordpress_preparation_shutting_down:
            return

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
        if self._wordpress_preparation_shutting_down:
            return

        self._last_publish_results = results
        self.retry_failed_button.setEnabled(
            self._build_failed_retry_request() is not None
        )

        self.publish_status.show_results(results)
        self._refresh_recent_posts()

    def _on_publish_error(self, _message: str) -> None:
        """Clear retry state after an unexpected publishing error."""
        if self._wordpress_preparation_shutting_down:
            return

        self._last_publish_request = None
        self._last_publish_results = ()

        self.retry_failed_button.setEnabled(False)
        self.publish_status.show_error()

    def _on_publishing_finished(self) -> None:
        """Restore publishing controls after thread cleanup."""
        if self._wordpress_preparation_shutting_down:
            return

        self.post_editor.publish_button.setEnabled(True)

    def shutdown(self) -> None:
        """Stop background operations without restarting queued work."""
        self._tag_loading_shutting_down = True
        self._pending_tag_accounts.clear()

        self._remote_post_loading_shutting_down = True
        self._remote_post_updating_shutting_down = True
        self._remote_post_trashing_shutting_down = True
        self._remote_trashed_post_loading_shutting_down = True
        self._remote_post_restoring_shutting_down = True
        self._pending_remote_post_account = None
        self._pending_trashed_post_account = None

        self._remote_media_loading_shutting_down = True

        if self._remote_media_dialog is not None:
            self._remote_media_dialog.reject()

        self._category_creation_shutting_down = True
        self._pending_created_category_id = None
        self._remote_category_loading_shutting_down = True
        self._pending_remote_category_account = None
        self._remote_tag_loading_shutting_down = True
        self._pending_remote_tag_account = None
        self._loaded_remote_tags = ()
        self._loaded_remote_tags_account = None

        self._tag_loading_controller.shutdown()

        if self._remote_tag_loading_controller is not None:
            self._remote_tag_loading_controller.shutdown()

        if self._remote_category_loading_controller is not None:
            self._remote_category_loading_controller.shutdown()

        if self._wordpress_category_creation_controller is not None:
            self._wordpress_category_creation_controller.shutdown()

        if self._remote_media_loading_controller is not None:
            self._remote_media_loading_controller.shutdown()

        if self._remote_post_loading_controller is not None:
            self._remote_post_loading_controller.shutdown()

        if self._remote_post_updating_controller is not None:
            self._remote_post_updating_controller.shutdown()

        if self._remote_post_trashing_controller is not None:
            self._remote_post_trashing_controller.shutdown()

        if self._remote_trashed_post_loading_controller is not None:
            self._remote_trashed_post_loading_controller.shutdown()

        if self._remote_post_restoring_controller is not None:
            self._remote_post_restoring_controller.shutdown()

        self._wordpress_preparation_shutting_down = True
        self._pending_publish_request = None
        self._pending_wordpress_accounts.clear()

        if self._wordpress_tag_preparation_controller is not None:
            self._wordpress_tag_preparation_controller.shutdown()

        self._publishing_controller.shutdown()

        if self._wordpress_tag_creation_controller is not None:
            self._wordpress_tag_creation_controller.shutdown()
