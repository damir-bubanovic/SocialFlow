from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

from socialflow.ui.posts.language_controls import LanguageControls
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.ui.posts.publish_button import PublishButton
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.ui.posts.destination_selector import DestinationSelector
from socialflow.domain.publishing.publish_request import PublishRequest


class PostEditor(QWidget):
    """Editor for composing post text."""

    publish_requested = Signal(PublishRequest)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.language_controls = LanguageControls(self)
        self.destination_selector = DestinationSelector(self)

        self.text_editor = QPlainTextEdit(self)
        self.text_editor.setPlaceholderText("Write your post...")
        self.publish_button = PublishButton(self)

        layout = QVBoxLayout()
        layout.addWidget(self.language_controls)
        layout.addWidget(self.destination_selector)
        layout.addWidget(self.text_editor)
        layout.addWidget(self.publish_button)

        self.setLayout(layout)
        self.text_editor.textChanged.connect(
            self._update_publish_button
        )
        self.destination_selector.facebook.toggled.connect(
            self._update_publish_button
        )
        self.destination_selector.instagram.toggled.connect(
            self._update_publish_button
        )
        self.destination_selector.wordpress.toggled.connect(
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

    def publish_request(self) -> PublishRequest:
        """Return the current publishing request."""
        return PublishRequest(
            post=self.post(),
            destinations=self.selected_destinations(),
        )

    def _update_publish_button(self) -> None:
        """Synchronize the publish button with the current post state."""
        available = (
                self.post().has_content()
                and bool(self.selected_destinations())
        )

        self.publish_button.set_post_available(available)

    def _request_publish(self) -> None:
        """Emit the current publishing request."""
        request = self.publish_request()

        if request.post.has_content() and request.destinations:
            self.publish_requested.emit(request)

    def selected_destinations(
            self,
    ) -> tuple[PublishingDestination, ...]:
        """Return the selected publishing destinations."""
        return self.destination_selector.selected_destinations()