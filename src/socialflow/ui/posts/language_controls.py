
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QWidget

from socialflow.domain.language.language import Language
from socialflow.ui.posts.language_indicator import LanguageIndicator
from socialflow.ui.posts.language_selector import LanguageSelector


class LanguageControls(QWidget):
    """Controls for viewing and selecting the post language."""

    manual_language_selected = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.selector = LanguageSelector(self)
        self.indicator = LanguageIndicator(self)

        layout = QHBoxLayout()
        layout.addWidget(self.selector)
        layout.addWidget(self.indicator)
        layout.addStretch()

        self.setLayout(layout)

        self.selector.currentIndexChanged.connect(
            self._update_indicator
        )
        self.selector.activated.connect(
            self._notify_manual_language_selected
        )

    def selected_language(self) -> Language:
        """Return the currently selected language."""
        return self.selector.selected_language()

    def set_language(self, language: Language) -> None:
        """Explicitly select a language and mark it as manually chosen."""
        self.selector.set_language(language)
        self.manual_language_selected.emit()

    def set_detected_language(self, language: Language) -> None:
        """Update the language without recording a manual selection."""
        self.selector.set_language(language)

    def _notify_manual_language_selected(
            self,
            _index: int,
    ) -> None:
        """Notify listeners of an explicit dropdown selection."""
        self.manual_language_selected.emit()

    def _update_indicator(self) -> None:
        """Synchronize the indicator with the selected language."""
        self.indicator.set_language(self.selected_language())
