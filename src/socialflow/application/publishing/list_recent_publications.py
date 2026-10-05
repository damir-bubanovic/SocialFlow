from socialflow.application.publishing.publication_repository import (
    PublicationRepository,
)
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.publication import Publication


class ListRecentPublications:
    """List recent publications for an account."""

    def __init__(
        self,
        repository: PublicationRepository,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        account: Account,
        limit: int = 5,
    ) -> tuple[Publication, ...]:
        """Return recent publications for an account."""
        return self._repository.recent_for_account(
            account=account,
            limit=limit,
        )