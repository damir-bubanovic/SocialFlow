import json
from pathlib import Path
from uuid import uuid4

from socialflow.application.publishing.publication_repository import (
    PublicationRepository,
)
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.publication import Publication
from socialflow.infrastructure.publishing.publication_serializer import (
    PublicationSerializer,
)


class JsonPublicationRepository(PublicationRepository):
    """Store publication history in a JSON file."""

    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    def add(self, publication: Publication) -> None:
        """Store a publication."""
        publications = list(self._load())
        publications.append(publication)
        self._save(publications)

    def recent_for_account(
        self,
        account: Account,
        limit: int = 5,
    ) -> tuple[Publication, ...]:
        """Return the most recent publications for an account."""
        publications = (
            publication
            for publication in self._load()
            if publication.account == account
        )

        ordered = sorted(
            publications,
            key=lambda publication: publication.published_at,
            reverse=True,
        )

        return tuple(ordered[:limit])

    def _load(self) -> tuple[Publication, ...]:
        """Load publications from disk and migrate legacy records."""
        if not self._file_path.exists():
            return ()

        with self._file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        migration_required = False

        for item in data:
            if "id" not in item:
                item["id"] = str(uuid4())
                migration_required = True

        publications = tuple(
            PublicationSerializer.from_dict(item)
            for item in data
        )

        if migration_required:
            self._save(list(publications))

        return publications

    def _save(
        self,
        publications: list[Publication],
    ) -> None:
        """Save publications to disk."""
        self._file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = [
            PublicationSerializer.to_dict(publication)
            for publication in publications
        ]

        serialized = json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )

        self._file_path.write_text(
            serialized,
            encoding="utf-8",
        )