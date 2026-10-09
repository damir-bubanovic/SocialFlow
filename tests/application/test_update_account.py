import pytest

from socialflow.application.accounts.account_repository import AccountRepository
from socialflow.application.accounts.errors import (
    AccountNotFoundError,
    DuplicateAccountError,
    InvalidAccountError,
)
from socialflow.application.accounts.update_account import UpdateAccount
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


def test_update_account_updates_configured_account() -> None:
    repository = InMemoryAccountRepository()

    current = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(current)

    updated = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    service = UpdateAccount(repository)
    service.execute(current, updated)

    stored_accounts = repository.all()

    assert len(stored_accounts) == 1

    stored_account = stored_accounts[0]

    assert stored_account.name == "Main Facebook"
    assert stored_account.destination == PublishingDestination.FACEBOOK
    assert stored_account.id == current.id
    assert stored_account.id != updated.id


def test_update_account_normalizes_name() -> None:
    repository = InMemoryAccountRepository()

    current = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(current)

    service = UpdateAccount(repository)
    service.execute(
        current,
        Account(
            name="  Main Facebook  ",
            destination=PublishingDestination.FACEBOOK,
        ),
    )

    assert repository.all()[0].name == "Main Facebook"


def test_update_account_rejects_empty_name() -> None:
    repository = InMemoryAccountRepository()

    current = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    repository.add(current)

    service = UpdateAccount(repository)

    with pytest.raises(
        InvalidAccountError,
        match="Account name cannot be empty.",
    ):
        service.execute(
            current,
            Account(
                name="   ",
                destination=PublishingDestination.FACEBOOK,
            ),
        )

    assert repository.all() == (current,)


def test_update_account_rejects_duplicate_account() -> None:
    repository = InMemoryAccountRepository()

    facebook = Account(
        name="SocialFlow Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    instagram = Account(
        name="SocialFlow Instagram",
        destination=PublishingDestination.INSTAGRAM,
    )

    repository.add(facebook)
    repository.add(instagram)

    service = UpdateAccount(repository)

    with pytest.raises(
        DuplicateAccountError,
        match="Account already exists.",
    ):
        service.execute(
            facebook,
            instagram,
        )

    assert repository.all() == (
        facebook,
        instagram,
    )


def test_update_account_rejects_unknown_account() -> None:
    repository = InMemoryAccountRepository()
    service = UpdateAccount(repository)

    current = Account(
        name="Unknown Facebook",
        destination=PublishingDestination.FACEBOOK,
    )
    updated = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    with pytest.raises(
        AccountNotFoundError,
        match="Account could not be found.",
    ):
        service.execute(current, updated)

    assert repository.all() == ()