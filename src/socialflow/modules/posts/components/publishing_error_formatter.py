
from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)
from socialflow.modules.posts.services.error_classifier import (
    ErrorCategory,
)
from socialflow.modules.posts.services.publish_result import PublishResult


class PublishingErrorFormatter:
    """Convert publishing failures into user-friendly messages."""

    @staticmethod
    def format(result: PublishResult) -> str:
        """Return a safe message for a publishing result."""
        error = result.error

        if isinstance(error, FacebookApiError):
            if error.code == 190:
                return (
                    "Facebook access token expired or invalid. "
                    "Reconnect the Facebook Page."
                )

            if error.code in (10, 200):
                return (
                    "Facebook Page permissions are insufficient. "
                    "Check the Page access permissions."
                )

        if result.error_category is ErrorCategory.TRANSIENT:
            return "Connection problem. Check your connection before retrying."

        if result.error_category is ErrorCategory.PERMANENT:
            return "Publishing configuration needs attention."

        return "Publishing failed. Please check the details."
