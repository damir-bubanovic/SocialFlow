
from dataclasses import dataclass

from socialflow.application.publishing.error_classifier import (
    ErrorCategory,
    ErrorClassifier,
)
from socialflow.domain.account.account import Account


@dataclass(frozen=True)
class PublishResult:
    """Result of a publishing attempt for one account."""

    account: Account
    succeeded: bool
    error: Exception | None = None
    cleanup_error: Exception | None = None

    @property
    def error_category(self) -> ErrorCategory | None:
        """Return the classification of the publishing failure."""
        if self.error is None:
            return None

        return ErrorClassifier.classify(self.error)
