from socialflow.application.publishing.publisher import Publisher
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.application.publishing.errors import (
    PublisherNotConfiguredError,
)


class PublisherRouter:
    """Resolves publishers for publishing destinations."""

    def __init__(
        self,
        publishers: dict[PublishingDestination, Publisher],
    ) -> None:
        self._publishers = publishers

    def publisher_for(
            self,
            destination: PublishingDestination,
    ) -> Publisher:
        """Return the publisher configured for a destination."""
        try:
            return self._publishers[destination]
        except KeyError as error:
            raise PublisherNotConfiguredError(
                f"No publisher configured for {destination}."
            ) from error
