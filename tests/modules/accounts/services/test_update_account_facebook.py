
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.facebook_page_config import (
    FacebookPageConfig,
)
from socialflow.modules.accounts.repositories.in_memory_account_repository import (
    InMemoryAccountRepository,
)
from socialflow.modules.accounts.services.add_account import AddAccount
from socialflow.modules.accounts.services.update_account import UpdateAccount


def test_add_facebook_account_preserves_page_config() -> None:
    repository = InMemoryAccountRepository()

    account = Account(
        name="  Facebook Main  ",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id=" 12345 ",
            page_name=" My Page ",
        ),
    )

    AddAccount(repository).execute(account)

    stored = repository.all()[0]

    assert stored.name == "Facebook Main"
    assert stored.facebook_config == FacebookPageConfig(
        page_id="12345",
        page_name="My Page",
    )
    assert stored.id == account.id


def test_update_facebook_account_preserves_page_config() -> None:
    repository = InMemoryAccountRepository()

    current = Account(
        name="Facebook",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="123",
            page_name="Old Page",
        ),
    )
    repository.add(current)

    updated = Account(
        name=" Updated Facebook ",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id=" 456 ",
            page_name=" New Page ",
        ),
    )

    UpdateAccount(repository).execute(current, updated)

    stored = repository.all()[0]

    assert stored.id == current.id
    assert stored.name == "Updated Facebook"
    assert stored.facebook_config == FacebookPageConfig(
        page_id="456",
        page_name="New Page",
    )
    assert stored.wordpress_config is None


def test_update_facebook_account_can_clear_page_config() -> None:
    repository = InMemoryAccountRepository()

    current = Account(
        name="Facebook",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="123",
            page_name="Old Page",
        ),
    )
    repository.add(current)

    updated = Account(
        name="Facebook",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=None,
    )

    UpdateAccount(repository).execute(current, updated)

    assert repository.all()[0].facebook_config is None


def test_switch_from_facebook_to_wordpress_clears_page_config() -> None:
    repository = InMemoryAccountRepository()

    current = Account(
        name="Account",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id="123",
            page_name="Page",
        ),
    )
    repository.add(current)

    updated = Account(
        name="Account",
        destination=PublishingDestination.WORDPRESS,
    )

    UpdateAccount(repository).execute(current, updated)

    stored = repository.all()[0]

    assert stored.destination == PublishingDestination.WORDPRESS
    assert stored.facebook_config is None
    assert stored.id == current.id


def test_switch_from_wordpress_to_facebook_saves_page_config() -> None:
    repository = InMemoryAccountRepository()

    current = Account(
        name="Account",
        destination=PublishingDestination.WORDPRESS,
    )
    repository.add(current)

    updated = Account(
        name="Account",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=FacebookPageConfig(
            page_id=" 999 ",
            page_name=" New Facebook Page ",
        ),
    )

    UpdateAccount(repository).execute(current, updated)

    stored = repository.all()[0]

    assert stored.destination == PublishingDestination.FACEBOOK
    assert stored.facebook_config == FacebookPageConfig(
        page_id="999",
        page_name="New Facebook Page",
    )
    assert stored.id == current.id


def test_update_does_not_modify_original_account() -> None:
    repository = InMemoryAccountRepository()

    config = FacebookPageConfig(
        page_id="123",
        page_name="Original Page",
    )
    current = Account(
        name="Facebook",
        destination=PublishingDestination.FACEBOOK,
        facebook_config=config,
    )
    repository.add(current)

    UpdateAccount(repository).execute(
        current,
        Account(
            name="Facebook Updated",
            destination=PublishingDestination.FACEBOOK,
            facebook_config=FacebookPageConfig(
                page_id="456",
                page_name="Updated Page",
            ),
        ),
    )

    assert current.facebook_config == config
    assert repository.all()[0].facebook_config != config
