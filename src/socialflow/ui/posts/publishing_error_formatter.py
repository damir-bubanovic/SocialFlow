from socialflow.application.publishing.error_classifier import ErrorCategory
from socialflow.application.publishing.publish_result import PublishResult


class PublishingErrorFormatter:
    """Convert publishing failures into user-friendly messages."""

    @staticmethod
    def format(result: PublishResult) -> str:
        """Return a safe message for a publishing result."""
        if result.error_category is ErrorCategory.TRANSIENT:
            return "Connection problem. Check your connection before retrying."

        if result.error_category is ErrorCategory.PERMANENT:
            return "Publishing configuration needs attention."

        return "Publishing failed. Please check the details."