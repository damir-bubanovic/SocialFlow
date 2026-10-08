from enum import Enum

from socialflow.application.language.paragraph_language_detector import (
    ParagraphLanguageDetector,
)
from socialflow.domain.language.language import Language


class PostLanguageClassification(Enum):
    """Possible language classifications for a complete post."""

    ENGLISH = "english"
    CROATIAN = "croatian"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class PostLanguageClassifier:
    """Classify a post using its paragraph languages."""

    def __init__(
        self,
        paragraph_detector: ParagraphLanguageDetector,
    ) -> None:
        self._paragraph_detector = paragraph_detector

    def classify(self, text: str) -> PostLanguageClassification:
        """Determine the overall language classification."""
        detected_languages = set(
            self._paragraph_detector.detect(text)
        )

        detected_languages.discard(None)

        if not detected_languages:
            return PostLanguageClassification.UNKNOWN

        if len(detected_languages) > 1:
            return PostLanguageClassification.MIXED

        if Language.CROATIAN in detected_languages:
            return PostLanguageClassification.CROATIAN

        return PostLanguageClassification.ENGLISH