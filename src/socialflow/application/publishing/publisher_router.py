
from collections.abc import Callable

from socialflow.application.publishing.publisher import Publisher
from socialflow.application.publishing.errors import (
    PublisherNotConfiguredError,
)
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination


PublisherFactory = Callable[[Account], Publisher]


class PublisherRouter:
    """Resolve publishers by destination or by account."""

    def __init__(
        self,
        publishers: dict[PublishingDestination, Publisher],
        account_factories: (
            dict[PublishingDestination, PublisherFactory] | None
        ) = None,
    ) -> None:
        self._publishers = dict(publishers)
        self._account_factories = dict(account_factories or {})

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

    def publisher_for_account(
        self,
        account: Account,
    ) -> Publisher:
        """Resolve a publisher using the selected account."""
        factory = self._account_factories.get(account.destination)

        if factory is not None:
            return factory(account)

        return self.publisher_for(account.destination)
