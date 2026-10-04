from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.domain.account.account import Account


class InMemoryAccountRepository(AccountRepository):
    """Stores publishing accounts in memory."""

    def __init__(self) -> None:
        self._accounts: list[Account] = []

    def all(self) -> tuple[Account, ...]:
        """Return all stored accounts."""
        return tuple(self._accounts)

    def add(self, account: Account) -> None:
        """Store an account."""
        self._accounts.append(account)

    def remove(self, account: Account) -> None:
        """Remove an account."""
        self._accounts.remove(account)