from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.application.accounts.errors import AccountNotFoundError
from socialflow.domain.account.account import Account


class RemoveAccount:
    """Application service for removing a publishing account."""

    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    def execute(self, account: Account) -> None:
        """Remove the account."""
        if account not in self._repository.all():
            raise AccountNotFoundError(
                "Account could not be found."
            )

        self._repository.remove(account)