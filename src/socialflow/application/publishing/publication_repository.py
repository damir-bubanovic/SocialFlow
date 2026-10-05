from abc import ABC, abstractmethod

from socialflow.domain.account.account import Account
from socialflow.domain.publishing.publication import Publication


class PublicationRepository(ABC):
    """Storage interface for publication history."""

    @abstractmethod
    def add(self, publication: Publication) -> None:
        """Store a publication."""

    @abstractmethod
    def recent_for_account(
        self,
        account: Account,
        limit: int = 5,
    ) -> tuple[Publication, ...]:
        """Return the most recent publications for an account."""