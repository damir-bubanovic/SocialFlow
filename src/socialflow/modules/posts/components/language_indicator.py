from PySide6.QtWidgets import QLabel, QWidget

from socialflow.domain.language.language import Language


class LanguageIndicator(QLabel):
    """Displays the active post language."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.set_language(Language.CROATIAN)

    def set_language(self, language: Language) -> None:
        """Update the displayed language."""
        self.setText(str(language))
        self.setProperty("language", str(language))