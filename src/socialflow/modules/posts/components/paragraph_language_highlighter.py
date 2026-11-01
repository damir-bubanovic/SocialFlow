from PySide6.QtGui import (
    QColor,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)

from socialflow.application.language.language_detector import LanguageDetector
from socialflow.domain.language.language import Language


class ParagraphLanguageHighlighter(QSyntaxHighlighter):
    """Highlight paragraphs according to their detected language."""

    UNKNOWN = 0
    ENGLISH = 1
    CROATIAN = 2

    def __init__(
        self,
        document: QTextDocument,
        language_detector: LanguageDetector,
    ) -> None:
        super().__init__(document)

        self._language_detector = language_detector

        self._english_format = QTextCharFormat()
        self._english_format.setUnderlineColor(QColor("#16a34a"))
        self._english_format.setUnderlineStyle(
            QTextCharFormat.UnderlineStyle.SingleUnderline
        )

        self._croatian_format = QTextCharFormat()
        self._croatian_format.setUnderlineColor(QColor("#2563eb"))
        self._croatian_format.setUnderlineStyle(
            QTextCharFormat.UnderlineStyle.SingleUnderline
        )

    def highlightBlock(self, text: str) -> None:
        """Detect and visually mark the current paragraph."""
        language = self._language_detector.detect(text)

        if language is Language.ENGLISH:
            self.setCurrentBlockState(self.ENGLISH)
            self.setFormat(0, len(text), self._english_format)

        elif language is Language.CROATIAN:
            self.setCurrentBlockState(self.CROATIAN)
            self.setFormat(0, len(text), self._croatian_format)

        else:
            self.setCurrentBlockState(self.UNKNOWN)