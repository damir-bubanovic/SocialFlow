import json
import os
import tempfile
from pathlib import Path
from uuid import uuid4

from socialflow.application.publishing.publication_repository import (
    PublicationRepository,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.publication import Publication
from socialflow.domain.publishing.publication_id import PublicationId
from socialflow.infrastructure.publishing.publication_image_inspector import (
    PublicationImageInspector,
)
from socialflow.infrastructure.publishing.publication_serializer import (
    PublicationSerializer,
)
from socialflow.infrastructure.storage.publication_image_storage import (
    PublicationImageStorage,
)


class JsonPublicationRepository(PublicationRepository):
    """Store publication history in a JSON file."""

    def __init__(
        self,
        file_path: Path,
        image_storage: PublicationImageStorage | None = None,
    ) -> None:
        self._file_path = file_path
        self._image_storage = image_storage or PublicationImageStorage(
            file_path.parent / "publication_images"
        )

    def add(self, publication: Publication) -> None:
        """Store a publication and roll back copied images on failure."""
        self._load()  # Ensure legacy records have been migrated.

        if self._file_path.exists():
            with self._file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)
        else:
            data = []

        stored_images = []

        try:
            for image in publication.post.images:
                stored_images.append(
                    self._image_storage.store(image)
                )

            stored_post = Post(
                text=publication.post.text,
                language=publication.post.language,
                images=tuple(stored_images),
                tags=publication.post.tags,
            )

            stored_publication = Publication(
                id=publication.id,
                account=publication.account,
                post=stored_post,
                published_at=publication.published_at,
            )

            data.append(
                PublicationSerializer.to_dict(stored_publication)
            )
            self._write_data(data)

        except Exception:
            for image in stored_images:
                image.path.unlink(missing_ok=True)
            raise

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

    def missing_images_for_publication(
        self,
        publication_id: PublicationId,
    ) -> tuple[Path, ...]:
        """Find missing images using the original stored JSON paths."""
        if not self._file_path.exists():
            return ()

        # Ensure legacy publication IDs have been migrated.
        self._load()

        with self._file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            records = json.load(file)

        for record in records:
            if record.get("id") != str(publication_id.value):
                continue

            image_paths = tuple(
                Path(path)
                for path in record.get("post", {}).get("images", [])
            )

            return PublicationImageInspector.missing_images(
                image_paths
            )

        return ()

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
            self._write_data(data)

        return publications

    def _save(self, publications: list[Publication]) -> None:
        """Serialize and atomically save publication history."""
        data = [
            PublicationSerializer.to_dict(publication)
            for publication in publications
        ]

        self._write_data(data)

    def _write_data(self, data: list[dict]) -> None:
        """Atomically write JSON without changing its records."""
        self._file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self._file_path.parent,
                prefix=".publications_",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)

                json.dump(
                    data,
                    temporary_file,
                    ensure_ascii=False,
                    indent=2,
                )

                temporary_file.flush()
                os.fsync(temporary_file.fileno())

            os.replace(temporary_path, self._file_path)

        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)