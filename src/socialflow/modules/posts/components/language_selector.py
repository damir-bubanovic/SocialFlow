from PySide6.QtWidgets import QComboBox, QWidget

from socialflow.domain.language.language import Language


class LanguageSelector(QComboBox):
    """Selector for the post content language."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._add_language(Language.CROATIAN)
        self._add_language(Language.ENGLISH)

    def selected_language(self) -> Language:
        """Return the currently selected language."""
        return Language(self.currentData())

    def set_language(self, language: Language) -> None:
        """Select the specified language."""
        index = self.findData(language)

        if index >= 0:
            self.setCurrentIndex(index)

    def _add_language(self, language: Language) -> None:
        """Add a supported language to the selector."""
        self.addItem(language.label, language)

