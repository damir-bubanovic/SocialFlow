from PySide6.QtGui import QTextDocument

from socialflow.application.language.language_detector import LanguageDetector
from socialflow.ui.posts.paragraph_language_highlighter import (
    ParagraphLanguageHighlighter,
)


def test_highlighter_preserves_document_text() -> None:
    document = QTextDocument()
    document.setPlainText(
        "Today we are publishing important news.\n"
        "Danas objavljujemo novu vijest."
    )

    highlighter = ParagraphLanguageHighlighter(
        document,
        LanguageDetector(),
    )
    highlighter.rehighlight()

    assert document.toPlainText() == (
        "Today we are publishing important news.\n"
        "Danas objavljujemo novu vijest."
    )


def test_highlighter_assigns_language_to_each_block() -> None:
    document = QTextDocument()
    document.setPlainText(
        "Today we are publishing important news.\n"
        "Danas objavljujemo novu vijest.\n"
        "SocialFlow"
    )

    highlighter = ParagraphLanguageHighlighter(
        document,
        LanguageDetector(),
    )
    highlighter.rehighlight()

    assert document.findBlockByNumber(0).userState() == 1
    assert document.findBlockByNumber(1).userState() == 2
    assert document.findBlockByNumber(2).userState() == 0