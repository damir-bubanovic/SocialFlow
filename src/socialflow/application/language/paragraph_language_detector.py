from socialflow.application.language.language_detector import LanguageDetector
from socialflow.domain.language.language import Language


class ParagraphLanguageDetector:
    """Detect the language of each paragraph independently."""

    def __init__(self, language_detector: LanguageDetector) -> None:
        self._language_detector = language_detector

    def detect(self, text: str) -> tuple[Language | None, ...]:
        """Return one language classification per paragraph."""
        return tuple(
            self._language_detector.detect(paragraph)
            for paragraph in text.split("\n")
        )