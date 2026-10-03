from dataclasses import dataclass

from socialflow.domain.publishing.destination import PublishingDestination


@dataclass(frozen=True, slots=True)
class Account:
    """A configured publishing account."""

    name: str
    destination: PublishingDestination

    def has_name(self) -> bool:
        """Return whether the account has a meaningful name."""
        return bool(self.name.strip())