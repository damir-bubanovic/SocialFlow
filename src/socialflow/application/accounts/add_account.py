from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.domain.account.account import Account
from socialflow.application.accounts.errors import (
    DuplicateAccountError,
    InvalidAccountError,
)


class AddAccount:
    """Application service for adding a publishing account."""

    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    def execute(self, account: Account) -> None:
        """Validate, normalize, and store an account."""
        if not account.has_name():
            raise InvalidAccountError(
                "Account name cannot be empty."
            )

        normalized_account = account.normalized()

        if normalized_account in self._repository.all():
            raise DuplicateAccountError(
                "Account already exists."
            )

        self._repository.add(normalized_account)