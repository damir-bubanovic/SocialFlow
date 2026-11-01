from pathlib import Path

from socialflow.modules.posts.models.publication_id import PublicationId
from socialflow.modules.posts.repositories.publication_repository import (
    PublicationRepository,
)
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.publication import Publication


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

    def missing_images_for_publication(
        self,
        publication_id: PublicationId,
    ) -> tuple[Path, ...]:
        """Return missing image paths for a publication."""
        return self._repository.missing_images_for_publication(
            publication_id
        )