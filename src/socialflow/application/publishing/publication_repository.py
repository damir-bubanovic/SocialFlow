from abc import ABC, abstractmethod
from pathlib import Path

from socialflow.domain.account.account import Account
from socialflow.domain.publishing.publication import Publication
from socialflow.domain.publishing.publication_id import PublicationId


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

    @abstractmethod
    def missing_images_for_publication(
        self,
        publication_id: PublicationId,
    ) -> tuple[Path, ...]:
        """Return missing image paths for a publication."""