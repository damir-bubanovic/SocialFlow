from socialflow.application.language.language_detector import LanguageDetector
from socialflow.application.language.paragraph_language_detector import (
    ParagraphLanguageDetector,
)
from socialflow.domain.language.language import Language


def test_detects_languages_for_individual_paragraphs() -> None:
    detector = ParagraphLanguageDetector(LanguageDetector())

    text = (
        "Today we are publishing important news.\n"
        "Danas objavljujemo novu vijest.\n"
        "Thank you for your support."
    )

    assert detector.detect(text) == (
        Language.ENGLISH,
        Language.CROATIAN,
        Language.ENGLISH,
    )


def test_preserves_empty_paragraphs_as_unknown() -> None:
    detector = ParagraphLanguageDetector(LanguageDetector())

    text = (
        "Today we are publishing news.\n"
        "\n"
        "Danas objavljujemo vijest."
    )

    assert detector.detect(text) == (
        Language.ENGLISH,
        None,
        Language.CROATIAN,
    )


def test_returns_unknown_for_ambiguous_paragraphs() -> None:
    detector = ParagraphLanguageDetector(LanguageDetector())

    assert detector.detect(
        "SocialFlow\n12345"
    ) == (
        None,
        None,
    )


def test_returns_unknown_for_empty_document() -> None:
    detector = ParagraphLanguageDetector(LanguageDetector())

    assert detector.detect("") == (None,)