from socialflow.application.language.language_detector import LanguageDetector
from socialflow.application.language.paragraph_language_detector import (
    ParagraphLanguageDetector,
)
from socialflow.application.language.post_language_classifier import (
    PostLanguageClassifier,
    PostLanguageClassification,
)


def create_classifier() -> PostLanguageClassifier:
    return PostLanguageClassifier(
        ParagraphLanguageDetector(LanguageDetector())
    )


def test_classifies_english_post() -> None:
    classifier = create_classifier()

    assert classifier.classify(
        "Today we are publishing important news.\n"
        "Thank you for your support."
    ) is PostLanguageClassification.ENGLISH


def test_classifies_croatian_post() -> None:
    classifier = create_classifier()

    assert classifier.classify(
        "Danas objavljujemo novu vijest.\n"
        "Ovo je nova objava."
    ) is PostLanguageClassification.CROATIAN


def test_classifies_mixed_post() -> None:
    classifier = create_classifier()

    assert classifier.classify(
        "Today we are publishing important news.\n"
        "Danas objavljujemo novu vijest."
    ) is PostLanguageClassification.MIXED


def test_ignores_unknown_paragraphs() -> None:
    classifier = create_classifier()

    assert classifier.classify(
        "Today we are publishing important news.\n"
        "\n"
        "SocialFlow"
    ) is PostLanguageClassification.ENGLISH


def test_classifies_unknown_post() -> None:
    classifier = create_classifier()

    assert classifier.classify(
        "SocialFlow\n12345"
    ) is PostLanguageClassification.UNKNOWN


def test_classifies_empty_post_as_unknown() -> None:
    classifier = create_classifier()

    assert classifier.classify(
        ""
    ) is PostLanguageClassification.UNKNOWN