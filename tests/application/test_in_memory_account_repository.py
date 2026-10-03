from socialflow.application.accounts.in_memory_account_repository import (
    InMemoryAccountRepository,
)
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination


def test_in_memory_account_repository_is_empty_by_default() -> None:
    repository = InMemoryAccountRepository()

    assert repository.all() == ()


def test_in_memory_account_repository_stores_accounts() -> None:
    repository = InMemoryAccountRepository()

    account = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    repository.add(account)

    assert repository.all() == (account,)