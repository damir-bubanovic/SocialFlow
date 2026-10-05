from socialflow.application.publishing.publication_repository import (
    PublicationRepository,
)
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.publication import Publication


class InMemoryPublicationRepository(PublicationRepository):
    """Store publication history in memory."""

    def __init__(self) -> None:
        self._publications: list[Publication] = []

    def add(self, publication: Publication) -> None:
        """Store a publication."""
        self._publications.append(publication)

    def recent_for_account(
        self,
        account: Account,
        limit: int = 5,
    ) -> tuple[Publication, ...]:
        """Return the most recent publications for an account."""
        publications = (
            publication
            for publication in self._publications
            if publication.account == account
        )

        ordered = sorted(
            publications,
            key=lambda publication: publication.published_at,
            reverse=True,
        )

        return tuple(ordered[:limit])