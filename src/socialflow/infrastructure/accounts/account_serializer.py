
from typing import Any
from uuid import UUID

from socialflow.domain.account.account import Account
from socialflow.domain.account.account_id import AccountId
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.domain.publishing.destination import PublishingDestination


class AccountSerializer:
    """Converts accounts to and from storage data."""

    @staticmethod
    def to_dict(account: Account) -> dict[str, Any]:
        """Convert an account to serializable data."""
        data: dict[str, Any] = {
            "id": str(account.id),
            "name": account.name,
            "destination": account.destination.value,
        }

        if account.wordpress_config is not None:
            data["wordpress_config"] = {
                "site_url": account.wordpress_config.site_url,
                "username": account.wordpress_config.username,
            }

        return data

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Account:
        """Create an account from serialized data."""
        account_id = data.get("id")
        wordpress_data = data.get("wordpress_config")

        wordpress_config = None

        if wordpress_data is not None:
            wordpress_config = WordPressConnectionConfig(
                site_url=wordpress_data["site_url"],
                username=wordpress_data["username"],
            )

        return Account(
            name=data["name"],
            destination=PublishingDestination(data["destination"]),
            id=(
                AccountId(UUID(account_id))
                if account_id is not None
                else AccountId(UUID(int=0))
            ),
            wordpress_config=wordpress_config,
        )
