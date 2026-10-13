from enum import Enum

from socialflow.application.publishing.errors import (
    EmptyPostError,
    ImagePreparationNotConfiguredError,
    PublisherNotConfiguredError,
)


class ErrorCategory(str, Enum):
    """Classification of a publishing failure."""

    TRANSIENT = "transient"
    PERMANENT = "permanent"
    UNKNOWN = "unknown"


class ErrorClassifier:
    """Classify publishing failures without changing retry behavior."""

    @staticmethod
    def classify(error: Exception) -> ErrorCategory:
        """Return the category associated with a publishing error."""
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorCategory.TRANSIENT

        if isinstance(
            error,
            (
                EmptyPostError,
                ImagePreparationNotConfiguredError,
                PublisherNotConfiguredError,
            ),
        ):
            return ErrorCategory.PERMANENT

        return ErrorCategory.UNKNOWN