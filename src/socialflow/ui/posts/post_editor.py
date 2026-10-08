
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from socialflow.application.language.language_detector import LanguageDetector
from socialflow.application.language.paragraph_language_detector import (
    ParagraphLanguageDetector,
)
from socialflow.ui.posts.paragraph_language_highlighter import (
    ParagraphLanguageHighlighter,
)
from socialflow.application.language.post_language_classifier import (
    PostLanguageClassification,
    PostLanguageClassifier,
)
from socialflow.ui.posts.content_language_indicator import (
    ContentLanguageIndicator,
)
from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.publish_request import PublishRequest
from socialflow.ui.posts.destination_selector import DestinationSelector
from socialflow.ui.posts.image_selector import ImageSelector
from socialflow.ui.posts.language_controls import LanguageControls
from socialflow.ui.posts.publish_button import PublishButton
from socialflow.ui.posts.tag_selector import TagSelector


class PostEditor(QWidget):
    """Editor for composing post text."""

    publish_requested = Signal(PublishRequest)
    account_selection_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._language_detector = LanguageDetector()
        self._paragraph_language_detector = ParagraphLanguageDetector(
            self._language_detector
        )
        self._post_language_classifier = PostLanguageClassifier(
            self._paragraph_language_detector
        )
        self._manual_language_override = False

        self.language_controls = LanguageControls(self)
        self.content_language_indicator = ContentLanguageIndicator(self)
        self.content_language_label = QLabel("Detected content:", self)
        self.content_language_label.setObjectName("contentLanguageLabel")
        self.language_controls.manual_language_selected.connect(
            self._lock_language_selection
        )
        self.destination_selector = DestinationSelector(self)

        self.text_editor = QPlainTextEdit(self)
        self.text_editor.setPlaceholderText("Write your post...")
        self._paragraph_highlighter = ParagraphLanguageHighlighter(
            self.text_editor.document(),
            self._language_detector,
        )
        self.language_controls.selector.currentIndexChanged.connect(
            self._update_language_visual_marker
        )
        self._update_language_visual_marker()

        self.image_selector = ImageSelector(self)
        self.tag_selector = TagSelector(self)
        self.publish_button = PublishButton(self)

        layout = QVBoxLayout()
        layout.addWidget(self.language_controls)
        content_language_layout = QHBoxLayout()
        content_language_layout.setContentsMargins(0, 0, 0, 0)
        content_language_layout.setSpacing(8)

        content_language_layout.addWidget(self.content_language_label)
        content_language_layout.addWidget(self.content_language_indicator)
        content_language_layout.addStretch()

        layout.addLayout(content_language_layout)
        layout.addWidget(self.destination_selector)
        layout.addWidget(self.text_editor)
        layout.addWidget(self.image_selector)
        layout.addWidget(self.tag_selector)
        layout.addWidget(self.publish_button)

        self.setLayout(layout)

        self.text_editor.textChanged.connect(
            self._update_publish_button
        )
        self.text_editor.textChanged.connect(
            self._detect_language
        )
        self.text_editor.textChanged.connect(
            self._update_language_visual_marker
        )
        self.publish_button.clicked.connect(
            self._request_publish
        )

        self._update_tag_creation()

    def set_accounts(self, accounts: tuple[Account, ...]) -> None:
        """Set the accounts available for publishing."""
        self.destination_selector.set_accounts(accounts)

        self.destination_selector.connect_selection_changed(
            self._update_publish_button
        )

        self.destination_selector.connect_selection_changed(
            self._notify_account_selection_changed
        )

        self._update_publish_button()

    def post_text(self) -> str:
        """Return the current post text."""
        return self.text_editor.toPlainText()

    def paragraph_languages(self) -> tuple[Language | None, ...]:
        """Return the detected language of each editor paragraph."""
        return self._paragraph_language_detector.detect(
            self.text_editor.toPlainText()
        )

    def post_language_classification(
            self,
    ) -> PostLanguageClassification:
        """Return the overall language classification of the editor text."""
        return self._post_language_classifier.classify(
            self.text_editor.toPlainText()
        )

    def selected_language(self) -> Language:
        """Return the currently selected post language."""
        return self.language_controls.selected_language()

    def post(self) -> Post:
        """Return the post currently represented by the editor."""
        return Post(
            text=self.text_editor.toPlainText(),
            language=self.language_controls.selected_language(),
            images=self.image_selector.selected_images(),
            tags=self.tag_selector.selected_tags(),
        )

    def new_post(self) -> None:
        """Clear the current draft and restore automatic language detection."""
        self._manual_language_override = False

        self.text_editor.clear()
        self.image_selector.set_selected_images(())
        self.tag_selector.set_selected_tags(())

        self.language_controls.set_detected_language(
            Language.CROATIAN
        )

        self._update_publish_button()

    def load_post(self, post: Post) -> None:
        """Load an existing post into the editor."""
        self.text_editor.setPlainText(post.text)
        self.language_controls.set_language(post.language)
        self.image_selector.set_selected_images(post.images)
        self.tag_selector.set_selected_tags(post.tags)

    def publish_request(self) -> PublishRequest:
        """Return the current publishing request."""
        return PublishRequest(
            post=self.post(),
            accounts=self.selected_accounts(),
        )

    def selected_accounts(self) -> tuple[Account, ...]:
        """Return the selected publishing accounts."""
        return self.destination_selector.selected_accounts()

    def _update_tag_creation(self) -> None:
        """Synchronize tag creation with account selection."""
        self.tag_selector.set_creation_enabled(
            bool(self.selected_accounts())
        )

    def _lock_language_selection(self) -> None:
        """Prevent automatic detection from overriding manual selection."""
        self._manual_language_override = True

    def _update_language_visual_marker(self) -> None:
        """Update the editor border using detected content languages."""
        classification = self.post_language_classification()
        self.content_language_indicator.set_classification(classification)

        border_colors = {
            PostLanguageClassification.ENGLISH: "#16a34a",
            PostLanguageClassification.CROATIAN: "#2563eb",
            PostLanguageClassification.MIXED: "#9333ea",
            PostLanguageClassification.UNKNOWN: "#6b7280",
        }

        border_color = border_colors[classification]

        language_codes = {
            PostLanguageClassification.ENGLISH: "en",
            PostLanguageClassification.CROATIAN: "hr",
            PostLanguageClassification.MIXED: "mixed",
            PostLanguageClassification.UNKNOWN: "unknown",
        }

        self.text_editor.setProperty(
            "postLanguage",
            language_codes[classification],
        )

        self.text_editor.setStyleSheet(
            f"""
            QPlainTextEdit {{
                border: 1px solid palette(mid);
                border-left: 4px solid {border_color};
                border-radius: 4px;
                padding: 6px;
            }}
            """
        )

        style = self.text_editor.style()
        style.unpolish(self.text_editor)
        style.polish(self.text_editor)
        self.text_editor.update()

    def _detect_language(self) -> None:
        """Update language automatically unless manually overridden."""
        if self._manual_language_override:
            return

        detected_language = self._language_detector.detect(
            self.text_editor.toPlainText()
        )

        if detected_language is not None:
            self.language_controls.set_detected_language(
                detected_language
            )

    def _update_publish_button(self) -> None:
        """Synchronize the publish button with the current post state."""
        available = (
            self.post().has_content()
            and bool(self.selected_accounts())
        )

        self.publish_button.set_post_available(available)

    def _notify_account_selection_changed(
        self,
        *_args: object,
    ) -> None:
        """Notify listeners that the selected accounts changed."""
        self._update_tag_creation()
        self.account_selection_changed.emit()

    def _request_publish(self) -> None:
        """Emit the current publishing request."""
        request = self.publish_request()

        if request.post.has_content() and request.accounts:
            self.publish_requested.emit(request)
