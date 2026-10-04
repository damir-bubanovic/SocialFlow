from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination


class AccountSerializer:
    """Converts accounts to and from storage data."""

    @staticmethod
    def to_dict(account: Account) -> dict[str, str]:
        """Convert an account to serializable data."""
        return {
            "name": account.name,
            "destination": account.destination.value,
        }

    @staticmethod
    def from_dict(data: dict[str, str]) -> Account:
        """Create an account from serialized data."""
        return Account(
            name=data["name"],
            destination=PublishingDestination(data["destination"]),
        )