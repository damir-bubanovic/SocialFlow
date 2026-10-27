from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from socialflow.domain.post.remote_post import RemotePost


class RemoteTrashedPostsPanel(QWidget):
    """Display trashed WordPress posts without editing their content."""

    restore_requested = Signal(str)
    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._posts: tuple[RemotePost, ...] = ()
        self._busy = False
        self._can_refresh = False

        self.title = QLabel("WordPress Trash", self)
        self.status_label = QLabel(
            "Select a WordPress account to view its Trash.",
            self,
        )

        self.posts_list = QListWidget(self)
        self.posts_list.setEnabled(False)

        self.refresh_button = QPushButton("Refresh Trash", self)
        self.restore_button = QPushButton(
            "Restore as Draft",
            self,
        )

        self.refresh_button.setEnabled(False)
        self.restore_button.setEnabled(False)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.status_label)
        layout.addWidget(self.posts_list)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.restore_button)

        self.posts_list.currentRowChanged.connect(
            self._update_restore_button
        )
        self.refresh_button.clicked.connect(
            self.refresh_requested.emit
        )
        self.restore_button.clicked.connect(
            self._request_restore
        )

    def show_empty(self) -> None:
        """Clear Trash when no WordPress account is selected."""
        self._posts = ()
        self._busy = False
        self._can_refresh = False

        self.posts_list.clear()
        self.posts_list.setEnabled(False)

        self.status_label.setText(
            "Select a WordPress account to view its Trash."
        )
        self.refresh_button.setEnabled(False)
        self.restore_button.setEnabled(False)

    def show_loading(self) -> None:
        """Clear outdated results while Trash is loading."""
        self._posts = ()
        self._busy = True
        self._can_refresh = False

        self.posts_list.clear()
        self.posts_list.setEnabled(False)

        self.status_label.setText("Loading WordPress Trash...")
        self.refresh_button.setEnabled(False)
        self.restore_button.setEnabled(False)

    def show_posts(self, posts: tuple[RemotePost, ...]) -> None:
        """Display retrieved trashed posts."""
        self._posts = posts
        self._busy = False
        self._can_refresh = True

        self.posts_list.clear()

        for post in posts:
            title = post.title.strip() or "(Untitled)"
            self.posts_list.addItem(
                f"{title} — ID {post.remote_id}"
            )

        self.posts_list.setEnabled(bool(posts))
        self.refresh_button.setEnabled(True)
        self.restore_button.setEnabled(False)

        if posts:
            self.status_label.setText(
                f"{len(posts)} trashed WordPress post(s). "
                "Select a post to restore it as a draft."
            )
        else:
            self.status_label.setText(
                "WordPress Trash is empty."
            )

    def show_error(self, message: str) -> None:
        """Show a retrieval error without retaining stale posts."""
        self._posts = ()
        self._busy = False
        self._can_refresh = True

        self.posts_list.clear()
        self.posts_list.setEnabled(False)

        self.status_label.setText(
            f"Unable to load WordPress Trash: {message}"
        )
        self.refresh_button.setEnabled(True)
        self.restore_button.setEnabled(False)

    def set_restoring(self, restoring: bool) -> None:
        """Disable Trash actions during a restore operation."""
        self._busy = restoring

        self.posts_list.setEnabled(
            not restoring and bool(self._posts)
        )
        self.refresh_button.setEnabled(
            not restoring and self._can_refresh
        )
        self._update_restore_button()

    def selected_post(self) -> RemotePost | None:
        """Return the selected post, if it is still available."""
        row = self.posts_list.currentRow()

        if 0 <= row < len(self._posts):
            return self._posts[row]

        return None

    def _update_restore_button(self, *_args: object) -> None:
        """Enable Restore only for a valid, idle selection."""
        self.restore_button.setEnabled(
            not self._busy
            and self.posts_list.isEnabled()
            and self.selected_post() is not None
        )

    def _request_restore(self) -> None:
        """Request restoration of the currently selected post."""
        if self._busy or not self.restore_button.isEnabled():
            return

        post = self.selected_post()

        if post is None:
            return

        self.restore_requested.emit(post.remote_id)