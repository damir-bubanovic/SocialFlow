from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget

from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.publish_request import PublishRequest
from socialflow.ui.posts.destination_selector import DestinationSelector
from socialflow.ui.posts.language_controls import LanguageControls
from socialflow.ui.posts.publish_button import PublishButton
from socialflow.ui.posts.image_selector import ImageSelector


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
        self.image_selector = ImageSelector(self)

        layout = QVBoxLayout()
        layout.addWidget(self.language_controls)
        layout.addWidget(self.destination_selector)
        layout.addWidget(self.text_editor)
        layout.addWidget(self.image_selector)
        layout.addWidget(self.publish_button)

        self.setLayout(layout)

        self.text_editor.textChanged.connect(
            self._update_publish_button
        )
        self.publish_button.clicked.connect(
            self._request_publish
        )

    def set_accounts(self, accounts: tuple[Account, ...]) -> None:
        """Set the accounts available for publishing."""
        self.destination_selector.set_accounts(accounts)

        self.destination_selector.connect_selection_changed(
            self._update_publish_button
        )

        self._update_publish_button()

    def post_text(self) -> str:
        """Return the current post text."""
        return self.text_editor.toPlainText()

    def selected_language(self) -> Language:
        """Return the currently selected post language."""
        return self.language_controls.selected_language()

    def post(self) -> Post:
        """Return the post currently represented by the editor."""
        return Post(
            text=self.text_editor.toPlainText(),
            language=self.language_controls.selected_language(),
            images=self.image_selector.selected_images(),
        )

    def publish_request(self) -> PublishRequest:
        """Return the current publishing request."""
        return PublishRequest(
            post=self.post(),
            accounts=self.selected_accounts(),
        )

    def selected_accounts(self) -> tuple[Account, ...]:
        """Return the selected publishing accounts."""
        return self.destination_selector.selected_accounts()

    def _update_publish_button(self) -> None:
        """Synchronize the publish button with the current post state."""
        available = (
            self.post().has_content()
            and bool(self.selected_accounts())
        )

        self.publish_button.set_post_available(available)

    def _request_publish(self) -> None:
        """Emit the current publishing request."""
        request = self.publish_request()

        if request.post.has_content() and request.accounts:
            self.publish_requested.emit(request)