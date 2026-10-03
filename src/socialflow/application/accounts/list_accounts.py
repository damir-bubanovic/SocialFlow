from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.domain.account.account import Account


class ListAccounts:
    """Application service for listing configured accounts."""

    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    def execute(self) -> tuple[Account, ...]:
        """Return all configured accounts."""
        return self._repository.all()