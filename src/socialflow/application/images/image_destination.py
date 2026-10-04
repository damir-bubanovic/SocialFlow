from enum import StrEnum


class ImageDestination(StrEnum):
    """Publishing destinations that can require image processing."""

    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WORDPRESS = "wordpress"