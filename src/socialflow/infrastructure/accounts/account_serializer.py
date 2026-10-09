from uuid import UUID

from socialflow.domain.account.account import Account
from socialflow.domain.account.account_id import AccountId
from socialflow.domain.publishing.destination import PublishingDestination


class AccountSerializer:
    """Converts accounts to and from storage data."""

    @staticmethod
    def to_dict(account: Account) -> dict[str, str]:
        """Convert an account to serializable data."""
        return {
            "id": str(account.id),
            "name": account.name,
            "destination": account.destination.value,
        }

    @staticmethod
    def from_dict(data: dict[str, str]) -> Account:
        """Create an account from serialized data."""
        account_id = data.get("id")

        return Account(
            name=data["name"],
            destination=PublishingDestination(data["destination"]),
            id=AccountId(UUID(account_id)) if account_id is not None else AccountId(UUID(int=0)),
        )