from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from socialflow.domain.post.remote_post import RemotePost
from socialflow.domain.post.remote_tag import RemoteTag
from socialflow.ui.posts.remote_tag_selector import RemoteTagSelector


class RemotePostsPanel(QWidget):
    """Display and edit posts retrieved from a remote platform."""

    save_requested = Signal(str, str)
    save_with_tags_requested = Signal(str, str, object)
    save_with_media_requested = Signal(str, str, object, object)
    save_with_status_requested = Signal(
        str, str, object, object, str
    )
    browse_media_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._posts: tuple[RemotePost, ...] = ()

        self.title = QLabel("Remote WordPress posts", self)
        self.status_label = QLabel(self)
        self.posts_list = QListWidget(self)

        self.edit_label = QLabel("Edit selected post", self)
        self.content_editor = QPlainTextEdit(self)

        self.post_status_label = QLabel("WordPress post status", self)

        self.post_status_selector = QComboBox(self)
        self.post_status_selector.addItem("Published", "publish")
        self.post_status_selector.addItem("Draft", "draft")
        self.post_status_selector.addItem("Pending review", "pending")
        self.post_status_selector.addItem("Private", "private")
        self.post_status_selector.setEnabled(False)

        self.tags_label = QLabel("WordPress tags", self)
        self.remote_tag_selector = RemoteTagSelector(self)
        self.remote_tag_selector.tags_list.setEnabled(False)

        self.featured_media_label = QLabel(
            "Featured image media ID", self
        )
        self.featured_media_checkbox = QCheckBox(
            "Change featured image", self
        )
        self.featured_media_input = QSpinBox(self)
        self.featured_media_input.setRange(0, 2147483647)
        self.featured_media_input.setSpecialValueText(
            "Remove featured image"
        )
        self.featured_media_input.setEnabled(False)
        self.featured_media_checkbox.setEnabled(False)

        self.browse_media_button = QPushButton(
            "Browse WordPress Media",
            self,
        )
        self.browse_media_button.setEnabled(False)

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
        layout.addWidget(self.post_status_label)
        layout.addWidget(self.post_status_selector)
        layout.addWidget(self.tags_label)
        layout.addWidget(self.remote_tag_selector)
        layout.addWidget(self.featured_media_label)
        layout.addWidget(self.featured_media_checkbox)
        layout.addWidget(self.featured_media_input)
        layout.addWidget(self.browse_media_button)
        layout.addWidget(self.save_button)

        self.posts_list.currentRowChanged.connect(
            self._on_post_selected
        )
        self.content_editor.textChanged.connect(
            self._update_save_button
        )
        self.post_status_selector.currentIndexChanged.connect(
            self._update_save_button
        )
        self.remote_tag_selector.selection_changed.connect(
            self._update_save_button
        )
        self.featured_media_checkbox.toggled.connect(
            self._on_featured_media_toggled
        )
        self.featured_media_input.valueChanged.connect(
            self._update_save_button
        )
        self.save_button.clicked.connect(
            self._request_save
        )
        self.browse_media_button.clicked.connect(
            self.browse_media_requested.emit
        )

        self.show_empty()

    def _reset_featured_media(self, media_id: int = 0) -> None:
        """Reset featured-image editing without requesting a change."""
        self.featured_media_checkbox.setChecked(False)
        self.featured_media_checkbox.setEnabled(False)
        self.featured_media_input.setValue(media_id)
        self.featured_media_input.setEnabled(False)
        self.browse_media_button.setEnabled(False)

    def _on_featured_media_toggled(self, checked: bool) -> None:
        """Enable featured-image editing when explicitly requested."""
        self.featured_media_input.setEnabled(
            checked and self.content_editor.isEnabled()
        )
        self._update_save_button()

    def apply_selected_media(self, media_id: int) -> None:
        """Apply an existing WordPress media ID to the editor."""
        if type(media_id) is not int or media_id <= 0:
            raise ValueError(
                "Selected media ID must be a positive integer."
            )

        row = self.posts_list.currentRow()

        if not 0 <= row < len(self._posts):
            raise ValueError(
                "Select a remote post before choosing media."
            )

        if not self.content_editor.isEnabled():
            raise ValueError(
                "Remote post editing is currently unavailable."
            )

        self.featured_media_checkbox.setChecked(True)
        self.featured_media_input.setValue(media_id)

        self._update_save_button()

    def _clear_selection(self) -> None:
        """Clear the editor and its associated remote post."""
        self._posts = ()
        self.posts_list.clear()

        self.content_editor.clear()
        self.content_editor.setEnabled(False)
        self.post_status_selector.setCurrentIndex(0)
        self.post_status_selector.setEnabled(False)

        self.remote_tag_selector.set_selected_ids(())
        self.remote_tag_selector.tags_list.setEnabled(False)

        self._reset_featured_media()
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
        """Load the selected post into the editing fields."""
        if not 0 <= row < len(self._posts):
            self.content_editor.clear()
            self.content_editor.setEnabled(False)

            self.post_status_selector.setCurrentIndex(0)
            self.post_status_selector.setEnabled(False)

            self.remote_tag_selector.set_selected_ids(())
            self.remote_tag_selector.tags_list.setEnabled(False)

            self._reset_featured_media()
            self.save_button.setEnabled(False)
            return

        post = self._posts[row]

        self.content_editor.setEnabled(True)
        self.content_editor.setPlainText(post.content)

        status_index = self.post_status_selector.findData(post.status)

        self.post_status_selector.setCurrentIndex(
            status_index if status_index >= 0 else 0
        )
        self.post_status_selector.setEnabled(
            status_index >= 0
        )

        self.remote_tag_selector.set_selected_ids(post.tag_ids)
        self.remote_tag_selector.tags_list.setEnabled(True)

        self._reset_featured_media(post.featured_media_id)
        self.featured_media_checkbox.setEnabled(True)
        self.browse_media_button.setEnabled(True)

        self._update_save_button()

    def restore_editing(self) -> None:
        """Restore editing controls after a failed save."""
        has_selection = (
                0 <= self.posts_list.currentRow() < len(self._posts)
        )

        self.content_editor.setEnabled(has_selection)
        self.post_status_selector.setEnabled(
            has_selection
            and self.post_status_selector.findData(
                self._posts[self.posts_list.currentRow()].status
            ) >= 0
        )
        self.remote_tag_selector.tags_list.setEnabled(has_selection)
        self.featured_media_checkbox.setEnabled(has_selection)
        self.featured_media_input.setEnabled(
            has_selection
            and self.featured_media_checkbox.isChecked()
        )
        self.browse_media_button.setEnabled(has_selection)

        self._update_save_button()

    def _update_save_button(self) -> None:
        """Enable saving when content, tags, or featured media changed."""
        row = self.posts_list.currentRow()

        if not 0 <= row < len(self._posts):
            self.save_button.setEnabled(False)
            return

        if not self.content_editor.isEnabled():
            self.save_button.setEnabled(False)
            return

        post = self._posts[row]
        updated_content = self.content_editor.toPlainText()

        if not updated_content.strip():
            self.save_button.setEnabled(False)
            return

        updated_tags = self.remote_tag_selector.selected_ids()

        content_changed = updated_content != post.content
        status_changed = (
                self.post_status_selector.isEnabled()
                and self.post_status_selector.currentData() != post.status
        )
        tags_changed = set(updated_tags) != set(post.tag_ids)
        media_changed = (
            self.featured_media_checkbox.isChecked()
            and self.featured_media_input.value()
            != post.featured_media_id
        )

        self.save_button.setEnabled(
            content_changed
            or tags_changed
            or media_changed
            or status_changed
        )

    def _request_save(self) -> None:
        """Request saving changed post fields."""
        if not self.save_button.isEnabled():
            return

        row = self.posts_list.currentRow()

        if not 0 <= row < len(self._posts):
            return

        post = self._posts[row]
        updated_content = self.content_editor.toPlainText()

        if not updated_content.strip():
            return

        updated_tags = self.remote_tag_selector.selected_ids()
        status_changed = (
                self.post_status_selector.isEnabled()
                and self.post_status_selector.currentData() != post.status
        )
        tags_changed = set(updated_tags) != set(post.tag_ids)
        media_changed = (
            self.featured_media_checkbox.isChecked()
            and self.featured_media_input.value()
            != post.featured_media_id
        )

        if (
            updated_content == post.content
            and not tags_changed
            and not media_changed
            and not status_changed
        ):
            return

        self.save_button.setEnabled(False)
        self.content_editor.setEnabled(False)
        self.post_status_selector.setEnabled(False)
        self.remote_tag_selector.tags_list.setEnabled(False)

        self.featured_media_checkbox.setEnabled(False)
        self.featured_media_input.setEnabled(False)
        self.browse_media_button.setEnabled(False)

        if status_changed:
            self.save_with_status_requested.emit(
                post.remote_id,
                updated_content,
                updated_tags if tags_changed else None,
                (
                    self.featured_media_input.value()
                    if media_changed
                    else None
                ),
                self.post_status_selector.currentData(),
            )
        elif media_changed:
            self.save_with_media_requested.emit(
                post.remote_id,
                updated_content,
                updated_tags if tags_changed else None,
                self.featured_media_input.value(),
            )
        elif tags_changed:
            self.save_with_tags_requested.emit(
                post.remote_id,
                updated_content,
                updated_tags,
            )
        else:
            self.save_requested.emit(
                post.remote_id,
                updated_content,
            )

    def set_available_remote_tags(
        self,
        tags: tuple[RemoteTag, ...],
    ) -> None:
        """Display WordPress tag names for the active account."""
        self.remote_tag_selector.set_available_tags(tags)
