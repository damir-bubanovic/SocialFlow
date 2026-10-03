class PublishingError(Exception):
    """Base exception for publishing failures."""


class EmptyPostError(PublishingError, ValueError):
    """Raised when publishing is requested for an empty post."""