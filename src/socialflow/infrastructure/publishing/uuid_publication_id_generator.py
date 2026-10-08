from uuid import uuid4

from socialflow.application.publishing.publication_id_generator import (
    PublicationIdGenerator,
)
from socialflow.domain.publishing.publication_id import PublicationId


class UuidPublicationIdGenerator(PublicationIdGenerator):
    """Generate publication identifiers using UUID4."""

    def generate(self) -> PublicationId:
        """Return a new UUID-based publication identifier."""
        return PublicationId(uuid4())