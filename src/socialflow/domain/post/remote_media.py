from dataclasses import dataclass
from urllib.parse import urlsplit

from socialflow.domain.publishing.destination import (
    PublishingDestination,
)


@dataclass(frozen=True, slots=True)
class RemoteMedia:
    """An image stored in a connected platform's media library."""

    remote_id: int
    destination: PublishingDestination
    source_url: str
    title: str
    thumbnail_url: str | None = None

    def __post_init__(self) -> None:
        if type(self.remote_id) is not int or self.remote_id <= 0:
            raise ValueError(
                "Remote media ID must be a positive integer."
            )

        if not isinstance(self.destination, PublishingDestination):
            raise ValueError("Invalid publishing destination.")

        self._validate_url(self.source_url, "Source URL")

        if not isinstance(self.title, str):
            raise ValueError("Media title must be a string.")

        if self.thumbnail_url is not None:
            self._validate_url(
                self.thumbnail_url,
                "Thumbnail URL",
            )

    @staticmethod
    def _validate_url(value: str, label: str) -> None:
        if not isinstance(value, str):
            raise ValueError(f"{label} must be an HTTPS URL.")

        parsed = urlsplit(value)

        if (
            parsed.scheme.lower() != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise ValueError(f"{label} must be an HTTPS URL.")