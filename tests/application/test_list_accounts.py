from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.application.accounts.list_accounts import ListAccounts
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


def test_list_accounts_returns_configured_accounts() -> None:
    repository = InMemoryAccountRepository()

    facebook = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    wordpress = Account(
        name="SocialFlow WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    repository.add(facebook)
    repository.add(wordpress)

    service = ListAccounts(repository)

    assert service.execute() == (
        facebook,
        wordpress,
    )


def test_list_accounts_returns_empty_tuple_when_no_accounts_exist() -> None:
    repository = InMemoryAccountRepository()
    service = ListAccounts(repository)

    assert service.execute() == ()