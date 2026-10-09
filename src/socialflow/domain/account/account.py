from dataclasses import dataclass
from dataclasses import field
from uuid import uuid4

from socialflow.domain.account.account_id import AccountId
from socialflow.domain.publishing.destination import PublishingDestination


@dataclass(frozen=True, slots=True)
class Account:
    """A configured publishing account."""

    name: str
    destination: PublishingDestination
    id: AccountId = field(
        default_factory=lambda: AccountId(uuid4()),
    )

    def has_name(self) -> bool:
        """Return whether the account has a meaningful name."""
        return bool(self.name.strip())

    def normalized(self) -> "Account":
        """Return the account with normalized values."""
        return Account(
            name=self.name.strip(),
            destination=self.destination,
            id=self.id,
        )

    def display_name(self) -> str:
        """Return the account name used for display."""
        return f"{self.name} ({self.destination.display_name})"