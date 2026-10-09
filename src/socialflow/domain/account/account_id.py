from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AccountId:
    """Stable identifier for a publishing account."""

    value: UUID

    def __str__(self) -> str:
        """Return the identifier as text."""
        return str(self.value)