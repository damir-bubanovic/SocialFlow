
from socialflow.modules.accounts.models.account import Account


class FacebookCredentialKeys:
    """Generate stable, platform-specific Facebook credential keys."""

    @staticmethod
    def page_access_token(account: Account) -> str:
        """Return the key for a Facebook Page access token."""
        return f"facebook:{account.id}:page_access_token"
