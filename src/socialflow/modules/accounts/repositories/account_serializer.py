from typing import Any
from uuid import UUID

from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.account_id import AccountId
from socialflow.modules.accounts.models.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.facebook_page_config import (
    FacebookPageConfig,
)
from socialflow.modules.accounts.models.instagram_account_config import (
    InstagramAccountConfig,
)


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

        if account.facebook_config is not None:
            data["facebook_config"] = {
                "page_id": account.facebook_config.page_id,
                "page_name": account.facebook_config.page_name,
            }

        if account.instagram_config is not None:
            data["instagram_config"] = {
                "instagram_user_id": account.instagram_config.instagram_user_id,
                "username": account.instagram_config.username,
            }

        return data

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Account:
        """Create an account from serialized data."""
        account_id = data.get("id")
        wordpress_data = data.get("wordpress_config")
        facebook_data = data.get("facebook_config")
        instagram_data = data.get("instagram_config")

        wordpress_config = None

        if wordpress_data is not None:
            wordpress_config = WordPressConnectionConfig(
                site_url=wordpress_data["site_url"],
                username=wordpress_data["username"],
            )

        facebook_config = None

        if facebook_data is not None:
            facebook_config = FacebookPageConfig(
                page_id=facebook_data["page_id"],
                page_name=facebook_data["page_name"],
            )

        instagram_config = None

        if instagram_data is not None:
            instagram_config = InstagramAccountConfig(
                instagram_user_id=instagram_data["instagram_user_id"],
                username=instagram_data["username"],
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
            facebook_config=facebook_config,
            instagram_config=instagram_config,
        )
