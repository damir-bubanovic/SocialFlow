from uuid import UUID

from socialflow.domain.publishing.publication_id import PublicationId
from socialflow.infrastructure.publishing.uuid_publication_id_generator import (
    UuidPublicationIdGenerator,
)


def test_uuid_publication_id_generator_returns_publication_id() -> None:
    generator = UuidPublicationIdGenerator()

    publication_id = generator.generate()

    assert isinstance(publication_id, PublicationId)
    assert isinstance(publication_id.value, UUID)


def test_uuid_publication_id_generator_returns_unique_ids() -> None:
    generator = UuidPublicationIdGenerator()

    first = generator.generate()
    second = generator.generate()

    assert first != second