from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class PublicationId:
    """Stable identifier for a publication."""

    value: UUID

    def __str__(self) -> str:
        """Return the identifier as text."""
        return str(self.value)