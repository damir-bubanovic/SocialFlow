from socialflow.application.language.language_detector import LanguageDetector
from socialflow.domain.language.language import Language


def test_detects_croatian_with_distinctive_characters() -> None:
    detector = LanguageDetector()

    assert detector.detect(
        "Danas ćemo objaviti važnu obavijest."
    ) is Language.CROATIAN


def test_detects_english_using_common_words() -> None:
    detector = LanguageDetector()

    assert detector.detect(
        "We are publishing an important announcement."
    ) is Language.ENGLISH


def test_detects_croatian_without_diacritics() -> None:
    detector = LanguageDetector()

    assert detector.detect(
        "Danas objavljujemo novu vijest."
    ) is Language.CROATIAN

def test_returns_uncertain_for_short_ambiguous_text() -> None:
    detector = LanguageDetector()

    assert detector.detect("SocialFlow") is None
    assert detector.detect("New") is None


def test_returns_uncertain_when_language_scores_are_equal() -> None:
    detector = LanguageDetector()

    assert detector.detect("We are danas sada") is None


def test_detection_is_case_insensitive() -> None:
    detector = LanguageDetector()

    assert detector.detect(
        "WE ARE PUBLISHING TODAY"
    ) is Language.ENGLISH


def test_detects_croatian_characters() -> None:
    detector = LanguageDetector()

    assert detector.detect(
        "Čestitamo!"
    ) is Language.CROATIAN

def test_detects_english_despite_croatian_characters() -> None:
    detector = LanguageDetector()

    assert detector.detect(
        "We are publishing important news about čokolada."
    ) is Language.ENGLISH

def test_returns_uncertain_for_balanced_mixed_language_text() -> None:
    detector = LanguageDetector()

    assert detector.detect(
        "We are publishing today. Danas smo objavljujemo novu vijest."
    ) is None