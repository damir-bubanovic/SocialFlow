from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QLineEdit,
)


from socialflow.domain.publishing.destination import PublishingDestination
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
        self.text_editor.setMinimumHeight(180)
        self.text_editor.setMaximumHeight(280)
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

        self.title_editor = QLineEdit(self)
        self.title_editor.setPlaceholderText(
            "Enter WordPress post title..."
        )
        self.title_heading = QLabel(
            "WordPress title *",
            self,
        )
        self.title_heading.setStyleSheet("font-weight: bold;")
        self.title_heading.hide()
        self.title_editor.hide()

        # Left: shared post content.
        self.composer_panel = QWidget(self)
        composer_layout = QVBoxLayout(self.composer_panel)
        composer_layout.setContentsMargins(8, 8, 8, 8)
        composer_layout.setSpacing(8)

        self.content_heading = QLabel("Post content", self.composer_panel)
        self.images_heading = QLabel("Images", self.composer_panel)
        self.tags_heading = QLabel("Tags", self.composer_panel)

        for heading in (
                self.content_heading,
                self.images_heading,
                self.tags_heading,
        ):
            font = heading.font()
            font.setBold(True)
            heading.setFont(font)

        composer_layout.addWidget(self.title_heading)
        composer_layout.addWidget(self.title_editor)

        composer_layout.addWidget(self.content_heading)
        composer_layout.addWidget(self.text_editor)

        composer_layout.addWidget(self.images_heading)
        composer_layout.addWidget(self.image_selector)

        composer_layout.addWidget(self.tags_heading)
        composer_layout.addWidget(self.tag_selector)

        # Keep the composer sections grouped near the top.
        composer_layout.addStretch()

        # Right: destination and publishing controls.
        self.publishing_panel = QWidget(self)
        publishing_layout = QVBoxLayout(self.publishing_panel)
        publishing_layout.setContentsMargins(8, 8, 8, 8)
        publishing_layout.setSpacing(12)

        self.publishing_heading = QLabel(
            "Publishing",
            self.publishing_panel,
        )
        font = self.publishing_heading.font()
        font.setBold(True)
        self.publishing_heading.setFont(font)

        publishing_layout.addWidget(self.publishing_heading)
        publishing_layout.addWidget(self.destination_selector)
        publishing_layout.addWidget(self.language_controls)

        content_language_layout = QHBoxLayout()
        content_language_layout.setContentsMargins(0, 0, 0, 0)
        content_language_layout.setSpacing(8)
        content_language_layout.addWidget(self.content_language_label)
        content_language_layout.addWidget(
            self.content_language_indicator
        )
        content_language_layout.addStretch()

        publishing_layout.addLayout(content_language_layout)
        publishing_layout.addWidget(self.publish_button)
        publishing_layout.addStretch()

        # Resizable two-column desktop layout.
        self.editor_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.editor_splitter.setChildrenCollapsible(False)
        self.editor_splitter.addWidget(self.composer_panel)
        self.editor_splitter.addWidget(self.publishing_panel)
        self.editor_splitter.setStretchFactor(0, 7)
        self.editor_splitter.setStretchFactor(1, 3)
        self.editor_splitter.setSizes([700, 300])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor_splitter)

        self.title_editor.textChanged.connect(
            self._update_publish_button
        )
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
            title=self.title_editor.text().strip(),
        )

    def new_post(self) -> None:
        """Clear the current draft and restore automatic language detection."""
        self._manual_language_override = False

        self.title_editor.clear()
        self.text_editor.clear()
        self.image_selector.set_selected_images(())
        self.tag_selector.set_selected_tags(())

        self.language_controls.set_detected_language(
            Language.CROATIAN
        )

        self._update_publish_button()

    def load_post(self, post: Post) -> None:
        """Load an existing post into the editor."""
        self.title_editor.setText(post.title)
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

    def _wordpress_selected(self) -> bool:
        """Return whether a selected destination is WordPress."""
        return any(
            account.destination is PublishingDestination.WORDPRESS
            for account in self.selected_accounts()
        )

    def _update_publish_button(self) -> None:
        """Synchronize the publish button with the current post state."""
        wordpress_selected = self._wordpress_selected()

        self.title_heading.setVisible(wordpress_selected)
        self.title_editor.setVisible(wordpress_selected)

        title_valid = (
                not wordpress_selected
                or bool(self.title_editor.text().strip())
        )

        available = (
                self.post().has_content()
                and bool(self.selected_accounts())
                and title_valid
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

        title_valid = (
                not self._wordpress_selected()
                or bool(request.post.title.strip())
        )

        if (
                request.post.has_content()
                and request.accounts
                and title_valid
        ):
            self.publish_requested.emit(request)
