from abc import ABC, abstractmethod

from socialflow.domain.publishing.publication_id import PublicationId


class PublicationIdGenerator(ABC):
    """Generate stable identifiers for new publications."""

    @abstractmethod
    def generate(self) -> PublicationId:
        """Return a new publication identifier."""