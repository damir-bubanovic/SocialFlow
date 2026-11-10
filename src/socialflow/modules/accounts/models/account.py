from dataclasses import dataclass
from dataclasses import field
from uuid import uuid4

from socialflow.modules.accounts.models.account_id import AccountId
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.modules.accounts.models.facebook_page_config import (
    FacebookPageConfig,
)
from socialflow.modules.accounts.models.instagram_account_config import (
    InstagramAccountConfig,
)


@dataclass(frozen=True, slots=True)
class Account:
    """A configured publishing account."""

    name: str
    destination: PublishingDestination
    wordpress_config: WordPressConnectionConfig | None = None
    id: AccountId = field(
        default_factory=lambda: AccountId(uuid4()),
    )
    facebook_config: FacebookPageConfig | None = None
    instagram_config: InstagramAccountConfig | None = None

    def has_name(self) -> bool:
        """Return whether the account has a meaningful name."""
        return bool(self.name.strip())

    def normalized(self) -> "Account":
        """Return the account with normalized values."""
        return Account(
            name=self.name.strip(),
            destination=self.destination,
            id=self.id,
            wordpress_config=(
                self.wordpress_config.normalized()
                if self.wordpress_config is not None
                else None
            ),
            facebook_config=(
                self.facebook_config.normalized()
                if self.facebook_config is not None
                else None
            ),
            instagram_config=(
                self.instagram_config.normalized()
                if self.instagram_config is not None
                else None
            ),
        )

    def display_name(self) -> str:
        """Return the account name used for display."""
        return f"{self.name} ({self.destination.display_name})"