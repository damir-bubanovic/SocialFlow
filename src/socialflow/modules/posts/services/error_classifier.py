from enum import Enum

from socialflow.modules.posts.services.errors import (
    EmptyPostError,
    ImagePreparationNotConfiguredError,
    PublisherNotConfiguredError,
)
from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
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

        if isinstance(error, FacebookApiError):
            return (
                ErrorCategory.TRANSIENT
                if error.is_transient
                else ErrorCategory.PERMANENT
            )

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
