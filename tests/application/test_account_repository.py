from socialflow.application.accounts.account_repository import AccountRepository
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


def test_account_repository_stores_account() -> None:
    repository = InMemoryAccountRepository()

    account = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    repository.add(account)

    assert repository.all() == (account,)
