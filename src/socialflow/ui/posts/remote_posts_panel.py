from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from socialflow.domain.post.remote_post import RemotePost


class RemotePostsPanel(QWidget):
    """Display and edit posts retrieved from a remote platform."""

    save_requested = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._posts: tuple[RemotePost, ...] = ()

        self.title = QLabel("Remote WordPress posts", self)
        self.status_label = QLabel(self)
        self.posts_list = QListWidget(self)

        self.edit_label = QLabel("Edit selected post", self)
        self.content_editor = QPlainTextEdit(self)
        self.save_button = QPushButton("Save changes", self)

        self.content_editor.setPlaceholderText(
            "Select a WordPress post to edit its content."
        )
        self.content_editor.setEnabled(False)
        self.save_button.setEnabled(False)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addWidget(self.status_label)
        layout.addWidget(self.posts_list)
        layout.addWidget(self.edit_label)
        layout.addWidget(self.content_editor)
        layout.addWidget(self.save_button)

        self.posts_list.currentRowChanged.connect(
            self._on_post_selected
        )
        self.content_editor.textChanged.connect(
            self._update_save_button
        )
        self.save_button.clicked.connect(
            self._request_save
        )

        self.show_empty()

    def _clear_selection(self) -> None:
        """Clear the editor and its associated remote post."""
        self._posts = ()
        self.posts_list.clear()
        self.content_editor.clear()
        self.content_editor.setEnabled(False)
        self.save_button.setEnabled(False)

    def show_loading(self) -> None:
        """Display a loading indicator."""
        self._clear_selection()
        self.status_label.setText("Loading WordPress posts...")

    def show_posts(self, posts: tuple[RemotePost, ...]) -> None:
        """Display the retrieved remote posts."""
        self._clear_selection()
        self._posts = posts

        for post in posts:
            preview = " ".join(post.content.split())[:100]

            self.posts_list.addItem(
                f"{post.published_at:%Y-%m-%d} | "
                f"{post.status} | {preview}"
            )

        self.status_label.setText(
            f"{len(posts)} remote posts loaded"
            if posts
            else "No remote posts found."
        )

    def show_error(self, message: str) -> None:
        """Display a retrieval error."""
        self._clear_selection()
        self.status_label.setText(
            f"Unable to load WordPress posts: {message}"
        )

    def show_empty(self) -> None:
        """Reset the panel."""
        self._clear_selection()
        self.status_label.setText(
            "Select a WordPress account to load remote posts."
        )

    def _on_post_selected(self, row: int) -> None:
        """Load the selected post into the editing field."""
        if not 0 <= row < len(self._posts):
            self.content_editor.clear()
            self.content_editor.setEnabled(False)
            self.save_button.setEnabled(False)
            return

        post = self._posts[row]

        self.content_editor.setEnabled(True)
        self.content_editor.setPlainText(post.content)
        self._update_save_button()

    def restore_editing(self) -> None:
        """Restore editing controls after a failed save."""
        self.content_editor.setEnabled(
            0 <= self.posts_list.currentRow() < len(self._posts)
        )
        self._update_save_button()

    def _update_save_button(self) -> None:
        """Enable saving only when the selected content has changed."""
        row = self.posts_list.currentRow()

        if not 0 <= row < len(self._posts):
            self.save_button.setEnabled(False)
            return

        original_content = self._posts[row].content
        updated_content = self.content_editor.toPlainText()

        self.save_button.setEnabled(
            bool(updated_content.strip())
            and updated_content != original_content
        )

    def _request_save(self) -> None:
        """Request saving the selected remote post."""
        if not self.save_button.isEnabled():
            return

        row = self.posts_list.currentRow()

        if not 0 <= row < len(self._posts):
            return

        self.save_requested.emit(
            self._posts[row].remote_id,
            self.content_editor.toPlainText(),
        )