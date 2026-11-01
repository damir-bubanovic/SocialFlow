from uuid import uuid4

from socialflow.modules.posts.services.publication_id_generator import (
    PublicationIdGenerator,
)
from socialflow.modules.posts.models.publication_id import PublicationId


class UuidPublicationIdGenerator(PublicationIdGenerator):
    """Generate publication identifiers using UUID4."""

    def generate(self) -> PublicationId:
        """Return a new UUID-based publication identifier."""
        return PublicationId(uuid4())