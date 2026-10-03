from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.application.accounts.errors import InvalidAccountError
from socialflow.domain.account.account import Account


class AddAccount:
    """Application service for adding a publishing account."""

    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    def execute(self, account: Account) -> None:
        """Validate and store an account."""
        if not account.has_name():
            raise InvalidAccountError(
                "Account name cannot be empty."
            )

        self._repository.add(account)