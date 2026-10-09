from socialflow.domain.account.account import Account


class WordPressCredentialKeys:
    """Generate stable credential keys for WordPress accounts."""

    @staticmethod
    def application_password(account: Account) -> str:
        """Return the key used to store an application password."""
        return f"wordpress:{account.id}:application_password"