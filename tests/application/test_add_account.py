import pytest

from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.application.accounts.add_account import AddAccount
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.application.accounts.errors import (
    DuplicateAccountError,
    InvalidAccountError,
)


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


def test_add_account_stores_valid_account() -> None:
    repository = InMemoryAccountRepository()
    service = AddAccount(repository)

    account = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    service.execute(account)

    assert repository.all() == (account,)


def test_add_account_rejects_empty_name() -> None:
    repository = InMemoryAccountRepository()
    service = AddAccount(repository)

    account = Account(
        name="   ",
        destination=PublishingDestination.FACEBOOK,
    )

    with pytest.raises(
        InvalidAccountError,
        match="Account name cannot be empty.",
    ):
        service.execute(account)

    assert repository.all() == ()

def test_add_account_rejects_duplicate_account() -> None:
    repository = InMemoryAccountRepository()
    service = AddAccount(repository)

    account = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    service.execute(account)

    with pytest.raises(
        DuplicateAccountError,
        match="Account already exists.",
    ):
        service.execute(account)

    assert repository.all() == (account,)

def test_add_account_stores_normalized_name() -> None:
    repository = InMemoryAccountRepository()
    service = AddAccount(repository)

    service.execute(
        Account(
            name="  SocialFlow Facebook  ",
            destination=PublishingDestination.FACEBOOK,
        )
    )

    assert repository.all()[0].name == "SocialFlow Facebook"


def test_add_account_rejects_duplicate_after_normalization() -> None:
    repository = InMemoryAccountRepository()
    service = AddAccount(repository)

    service.execute(
        Account(
            name="SocialFlow Facebook",
            destination=PublishingDestination.FACEBOOK,
        )
    )

    with pytest.raises(
        DuplicateAccountError,
        match="Account already exists.",
    ):
        service.execute(
            Account(
                name="  SocialFlow Facebook  ",
                destination=PublishingDestination.FACEBOOK,
            )
        )

    assert len(repository.all()) == 1