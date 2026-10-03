from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

from socialflow.ui.posts.language_controls import LanguageControls
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.ui.posts.publish_button import PublishButton


class PostEditor(QWidget):
    """Editor for composing post text."""

    publish_requested = Signal(Post)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.language_controls = LanguageControls(self)

        self.text_editor = QPlainTextEdit(self)
        self.text_editor.setPlaceholderText("Write your post...")
        self.publish_button = PublishButton(self)

        layout = QVBoxLayout()
        layout.addWidget(self.language_controls)
        layout.addWidget(self.text_editor)
        layout.addWidget(self.publish_button)

        self.setLayout(layout)
        self.text_editor.textChanged.connect(
            self._update_publish_button
        )
        self.publish_button.clicked.connect(
            self._request_publish
        )

    def post_text(self) -> str:
        """Return the current post text."""
        return self.text_editor.toPlainText()

    def selected_language(self) -> Language:
        """Return the currently selected post language."""
        return self.language_controls.selected_language()

    def post(self) -> Post:
        """Return the post currently represented by the editor."""
        return Post(
            text=self.post_text(),
            language=self.selected_language(),
        )

    def _update_publish_button(self) -> None:
        """Synchronize the publish button with the current post."""
        self.publish_button.set_post_available(
            self.post().has_content()
        )

    def _request_publish(self) -> None:
        """Emit the post when publishing is requested."""
        post = self.post()

        if post.has_content():
            self.publish_requested.emit(post)