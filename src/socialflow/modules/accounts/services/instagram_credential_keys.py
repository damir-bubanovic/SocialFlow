from socialflow.modules.accounts.models.account import Account


class InstagramCredentialKeys:
    """Generate stable, platform-specific Instagram credential keys."""

    @staticmethod
    def access_token(account: Account) -> str:
        """Return the key for an Instagram access token."""
        return f"instagram:{account.id}:access_token"