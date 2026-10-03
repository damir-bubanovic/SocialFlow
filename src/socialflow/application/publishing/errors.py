class PublishingError(Exception):
    """Base exception for publishing failures."""


class EmptyPostError(PublishingError, ValueError):
    """Raised when publishing is requested for an empty post."""

class PublisherNotConfiguredError(PublishingError):
    """Raised when no publisher is configured for a destination."""