from PySide6.QtWidgets import QHBoxLayout, QWidget

from socialflow.domain.language.language import Language
from socialflow.ui.posts.language_indicator import LanguageIndicator
from socialflow.ui.posts.language_selector import LanguageSelector


class LanguageControls(QWidget):
    """Controls for viewing and selecting the post language."""

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

    def selected_language(self) -> Language:
        """Return the currently selected language."""
        return self.selector.selected_language()

    def _update_indicator(self) -> None:
        """Synchronize the indicator with the selected language."""
        self.indicator.set_language(self.selected_language())