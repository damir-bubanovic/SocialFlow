import re

from PySide6.QtCore import Signal
from PySide6.QtGui import QTextDocument
from PySide6.QtCore import Qt
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
    QSplitter,
    QScrollArea,
)

from socialflow.domain.post.remote_post import RemotePost
from socialflow.domain.post.remote_tag import RemoteTag
from socialflow.ui.posts.remote_tag_selector import RemoteTagSelector



_HTML_TAG_PATTERN = re.compile(
    r"</?[a-zA-Z][a-zA-Z0-9]*(?:\s[^<>]*?)?\s*/?>"
)


def _contains_html(value: str) -> bool:
    """Identify HTML markup in retrieved WordPress content."""
    return bool(_HTML_TAG_PATTERN.search(value))


def _readable_content(value: str) -> str:
    """Convert HTML to readable text without changing stored content."""
    if not _contains_html(value):
        return value

    document = QTextDocument()
    document.setHtml(value)
    return document.toPlainText()


class RemotePostsPanel(QWidget):
    """Display and edit posts retrieved from a remote platform."""

    save_requested = Signal(str, str)
    save_with_tags_requested = Signal(str, str, object)
    save_with_media_requested = Signal(str, str, object, object)
    save_with_status_requested = Signal(
        str, str, object, object, str
    )
    browse_media_requested = Signal()
    trash_requested = Signal(str)
    save_with_excerpt_requested = Signal(
        str, str, object, object, object, str
    )
    save_with_title_requested = Signal(
        str, str, object, object, object, object, str
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._posts: tuple[RemotePost, ...] = ()

        self.title = QLabel("Remote WordPress posts", self)
        self.status_label = QLabel(self)
        self.posts_list = QListWidget(self)
        self.posts_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.posts_list.setTextElideMode(
            Qt.TextElideMode.ElideRight
        )

        self.edit_label = QLabel("Edit selected post", self)

        self.post_title_label = QLabel("WordPress post title", self)
        self.post_title_editor = QPlainTextEdit(self)
        self.post_title_editor.setPlaceholderText(
            "Enter a title for this WordPress post."
        )
        self.post_title_editor.setFixedHeight(65)
        self.post_title_editor.setEnabled(False)

        self.content_editor = QPlainTextEdit(self)
        self.content_editor.setFixedHeight(110)

        self.excerpt_label = QLabel("WordPress excerpt", self)
        self.excerpt_editor = QPlainTextEdit(self)
        self.excerpt_editor.setPlaceholderText(
            "Optional short summary of this WordPress post."
        )
        self.excerpt_editor.setEnabled(False)
        self.excerpt_editor.setFixedHeight(65)

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
        self.remote_tag_selector.setFixedHeight(85)

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

        self.trash_button = QPushButton("Move to Trash", self)
        self.trash_button.setEnabled(False)

        self.content_editor.setPlaceholderText(
            "Select a WordPress post to edit its content."
        )
        self.content_editor.setEnabled(False)
        self.save_button.setEnabled(False)

        # Left column: remote WordPress post selection.
        self.list_panel = QWidget(self)
        list_layout = QVBoxLayout(self.list_panel)
        list_layout.addWidget(self.title)
        list_layout.addWidget(self.status_label)
        list_layout.addWidget(self.posts_list)

        # Right column: selected WordPress post editor.
        self.editor_panel = QWidget(self)
        editor_layout = QVBoxLayout(self.editor_panel)
        editor_layout.setSpacing(5)
        editor_layout.addWidget(self.edit_label)
        editor_layout.addWidget(self.post_title_label)
        editor_layout.addWidget(self.post_title_editor)
        editor_layout.addWidget(self.content_editor)
        editor_layout.addWidget(self.excerpt_label)
        editor_layout.addWidget(self.excerpt_editor)
        editor_layout.addWidget(self.post_status_label)
        editor_layout.addWidget(self.post_status_selector)
        editor_layout.addWidget(self.tags_label)
        editor_layout.addWidget(self.remote_tag_selector)
        editor_layout.addWidget(self.featured_media_label)
        editor_layout.addWidget(self.featured_media_checkbox)
        editor_layout.addWidget(self.featured_media_input)
        editor_layout.addWidget(self.browse_media_button)
        editor_layout.addStretch()

        # Keep the editor accessible in smaller windows.
        self.editor_scroll = QScrollArea(self)
        self.editor_scroll.setWidgetResizable(True)
        self.editor_scroll.setFrameShape(
            QScrollArea.Shape.NoFrame
        )
        self.editor_scroll.setWidget(self.editor_panel)
        self.editor_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Keep the editing actions visible below the scroll area.
        self.editor_column = QWidget(self)
        editor_column_layout = QVBoxLayout(self.editor_column)
        editor_column_layout.setContentsMargins(0, 0, 0, 0)
        editor_column_layout.setSpacing(5)

        editor_column_layout.addWidget(self.editor_scroll, 1)
        editor_column_layout.addWidget(self.save_button)
        editor_column_layout.addWidget(self.trash_button)

        # Resizable two-column layout.
        self.splitter = QSplitter(
            Qt.Orientation.Horizontal,
            self,
        )
        self.splitter.addWidget(self.list_panel)
        self.splitter.addWidget(self.editor_column)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 7)
        self.splitter.setSizes([300, 700])

        layout = QVBoxLayout(self)
        layout.addWidget(self.splitter)

        self.posts_list.currentRowChanged.connect(
            self._on_post_selected
        )
        self.post_title_editor.textChanged.connect(
            self._update_save_button
        )
        self.content_editor.textChanged.connect(
            self._update_save_button
        )
        self.excerpt_editor.textChanged.connect(
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
        self.trash_button.clicked.connect(
            self._request_trash
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
        self.posts_list.setEnabled(True)

        self.post_title_editor.clear()
        self.post_title_editor.setEnabled(False)
        self.content_editor.clear()
        self.content_editor.setReadOnly(False)
        self.content_editor.setEnabled(False)
        self.excerpt_editor.clear()
        self.excerpt_editor.setReadOnly(False)
        self.excerpt_editor.setEnabled(False)
        self.post_status_selector.setCurrentIndex(0)
        self.post_status_selector.setEnabled(False)

        self.remote_tag_selector.set_selected_ids(())
        self.remote_tag_selector.tags_list.setEnabled(False)

        self._reset_featured_media()
        self.save_button.setEnabled(False)
        self.trash_button.setEnabled(False)

    def show_loading(self) -> None:
        """Display a loading indicator."""
        self._clear_selection()
        self.status_label.setText("Loading WordPress posts...")

    def show_posts(self, posts: tuple[RemotePost, ...]) -> None:
        """Display the retrieved remote posts."""
        self._clear_selection()
        self._posts = posts

        for post in posts:
            post_title = " ".join(post.title.split()) or "(Untitled)"

            self.posts_list.addItem(
                f"{post.published_at:%Y-%m-%d} | "
                f"{post.status} | {post_title}"
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
            self.trash_button.setEnabled(False)
            self.post_title_editor.clear()
            self.post_title_editor.setEnabled(False)
            self.content_editor.clear()
            self.content_editor.setReadOnly(False)
            self.content_editor.setEnabled(False)

            self.post_status_selector.setCurrentIndex(0)
            self.post_status_selector.setEnabled(False)

            self.excerpt_editor.clear()
            self.excerpt_editor.setReadOnly(False)
            self.excerpt_editor.setEnabled(False)

            self.remote_tag_selector.set_selected_ids(())
            self.remote_tag_selector.tags_list.setEnabled(False)

            self._reset_featured_media()
            self.save_button.setEnabled(False)
            return

        post = self._posts[row]
        self.trash_button.setEnabled(True)

        self.post_title_editor.setPlainText(post.title)
        self.post_title_editor.setEnabled(True)

        has_html_content = _contains_html(post.content)

        self.content_editor.setPlainText(
            _readable_content(post.content)
        )
        self.content_editor.setReadOnly(has_html_content)
        self.content_editor.setEnabled(True)

        has_html_excerpt = _contains_html(post.excerpt)

        self.excerpt_editor.setPlainText(
            _readable_content(post.excerpt)
        )
        self.excerpt_editor.setReadOnly(has_html_excerpt)
        self.excerpt_editor.setEnabled(True)

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

        self.posts_list.setEnabled(bool(self._posts))
        self.trash_button.setEnabled(has_selection)
        self.content_editor.setEnabled(has_selection)
        self.post_title_editor.setEnabled(has_selection)
        self.excerpt_editor.setEnabled(has_selection)
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
        updated_content = (
            post.content
            if self.content_editor.isReadOnly()
            else self.content_editor.toPlainText()
        )

        if not updated_content.strip():
            self.save_button.setEnabled(False)
            return

        updated_title = self.post_title_editor.toPlainText()
        title_changed = updated_title != post.title

        if title_changed and not updated_title.strip():
            self.save_button.setEnabled(False)
            return

        updated_tags = self.remote_tag_selector.selected_ids()

        content_changed = updated_content != post.content
        excerpt_changed = (
                not self.excerpt_editor.isReadOnly()
                and self.excerpt_editor.toPlainText() != post.excerpt
        )
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
            title_changed
            or content_changed
            or excerpt_changed
            or tags_changed
            or media_changed
            or status_changed
        )


    def _request_trash(self) -> None:
        """Request moving the selected WordPress post to Trash."""
        if not self.trash_button.isEnabled():
            return

        row = self.posts_list.currentRow()

        if not 0 <= row < len(self._posts):
            return

        self.trash_requested.emit(self._posts[row].remote_id)

    def set_trashing(self, trashing: bool) -> None:
        """Prevent conflicting edits while a Trash operation runs."""
        if trashing:
            self.posts_list.setEnabled(False)
            self.post_title_editor.setEnabled(False)
            self.content_editor.setEnabled(False)
            self.excerpt_editor.setEnabled(False)
            self.post_status_selector.setEnabled(False)
            self.remote_tag_selector.tags_list.setEnabled(False)
            self.featured_media_checkbox.setEnabled(False)
            self.featured_media_input.setEnabled(False)
            self.browse_media_button.setEnabled(False)
            self.save_button.setEnabled(False)
            self.trash_button.setEnabled(False)
        else:
            self.restore_editing()


    def _request_save(self) -> None:
        """Request saving changed post fields."""
        if not self.save_button.isEnabled():
            return

        row = self.posts_list.currentRow()

        if not 0 <= row < len(self._posts):
            return

        post = self._posts[row]
        updated_content = (
            post.content
            if self.content_editor.isReadOnly()
            else self.content_editor.toPlainText()
        )

        if not updated_content.strip():
            return

        updated_title = self.post_title_editor.toPlainText()
        title_changed = updated_title != post.title

        if title_changed and not updated_title.strip():
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
        updated_excerpt = (
            post.excerpt
            if self.excerpt_editor.isReadOnly()
            else self.excerpt_editor.toPlainText()
        )
        excerpt_changed = updated_excerpt != post.excerpt

        if (
                updated_content == post.content
                and not title_changed
                and not excerpt_changed
                and not tags_changed
                and not media_changed
                and not status_changed
        ):
            return

        self.save_button.setEnabled(False)
        self.trash_button.setEnabled(False)
        self.posts_list.setEnabled(False)
        self.content_editor.setEnabled(False)
        self.post_title_editor.setEnabled(False)
        self.excerpt_editor.setEnabled(False)
        self.post_status_selector.setEnabled(False)
        self.remote_tag_selector.tags_list.setEnabled(False)

        self.featured_media_checkbox.setEnabled(False)
        self.featured_media_input.setEnabled(False)
        self.browse_media_button.setEnabled(False)

        if title_changed:
            self.save_with_title_requested.emit(
                post.remote_id,
                updated_content,
                updated_tags if tags_changed else None,
                (
                    self.featured_media_input.value()
                    if media_changed
                    else None
                ),
                (
                    self.post_status_selector.currentData()
                    if status_changed
                    else None
                ),
                updated_excerpt if excerpt_changed else None,
                updated_title,
            )
        elif excerpt_changed:
            self.save_with_excerpt_requested.emit(
                post.remote_id,
                updated_content,
                updated_tags if tags_changed else None,
                (
                    self.featured_media_input.value()
                    if media_changed
                    else None
                ),
                (
                    self.post_status_selector.currentData()
                    if status_changed
                    else None
                ),
                updated_excerpt,
            )
        elif status_changed:
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
