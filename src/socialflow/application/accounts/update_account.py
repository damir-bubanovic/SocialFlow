from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.application.accounts.errors import (
    AccountNotFoundError,
    DuplicateAccountError,
    InvalidAccountError,
)
from socialflow.domain.account.account import Account


class UpdateAccount:
    """Application service for updating a publishing account."""

    def __init__(self, repository: AccountRepository) -> None:
        self._repository = repository

    def execute(self, current: Account, updated: Account) -> None:
        """Validate, normalize, and update an account."""
        accounts = self._repository.all()

        if current not in accounts:
            raise AccountNotFoundError(
                "Account could not be found."
            )

        if not updated.has_name():
            raise InvalidAccountError(
                "Account name cannot be empty."
            )

        normalized_account = updated.normalized()

        if (
            normalized_account != current
            and normalized_account in accounts
        ):
            raise DuplicateAccountError(
                "Account already exists."
            )

        self._repository.update(
            current,
            normalized_account,
        )