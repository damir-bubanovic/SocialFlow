from enum import StrEnum


class PublishingDestination(StrEnum):
    """Destinations supported for publishing SocialFlow posts."""

    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WORDPRESS = "wordpress"

    @property
    def display_name(self) -> str:
        """Return the human-readable destination name."""
        if self is PublishingDestination.FACEBOOK:
            return "Facebook"

        if self is PublishingDestination.INSTAGRAM:
            return "Instagram"

        return "WordPress"