import pytest

from socialflow.application.accounts.errors import AccountNotFoundError
from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.application.accounts.remove_account import RemoveAccount
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination


class InMemoryAccountRepository(AccountRepository):
    """Test repository that stores accounts in memory."""

    def __init__(self) -> None:
        self._accounts: list[Account] = []

    def all(self) -> tuple[Account, ...]:
        return tuple(self._accounts)

    def add(self, account: Account) -> None:
        self._accounts.append(account)

    def remove(self, account: Account) -> None:
        self._accounts.remove(account)

    def update(self, current: Account, updated: Account) -> None:
        index = self._accounts.index(current)
        self._accounts[index] = updated


def test_remove_account_removes_configured_account() -> None:
    repository = InMemoryAccountRepository()

    account = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(account)

    service = RemoveAccount(repository)
    service.execute(account)

    assert repository.all() == ()

def test_remove_account_rejects_unknown_account() -> None:
    repository = InMemoryAccountRepository()
    service = RemoveAccount(repository)

    account = Account(
        name="Unknown Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    with pytest.raises(
        AccountNotFoundError,
        match="Account could not be found.",
    ):
        service.execute(account)

    assert repository.all() == ()