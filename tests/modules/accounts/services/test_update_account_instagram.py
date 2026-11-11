
from socialflow.core.destination import PublishingDestination
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.instagram_account_config import (
    InstagramAccountConfig,
)
from socialflow.modules.accounts.repositories.in_memory_account_repository import (
    InMemoryAccountRepository,
)
from socialflow.modules.accounts.services.update_account import UpdateAccount


def test_update_instagram_account_preserves_configuration() -> None:
    repository = InMemoryAccountRepository()

    current = Account(
        name="Old Instagram",
        destination=PublishingDestination.INSTAGRAM,
        instagram_config=InstagramAccountConfig(
            instagram_user_id="12345",
            username="old_user",
        ),
    )
    repository.add(current)

    updated = Account(
        name="New Instagram",
        destination=PublishingDestination.INSTAGRAM,
        instagram_config=InstagramAccountConfig(
            instagram_user_id=" 67890 ",
            username=" new_user ",
        ),
    )

    UpdateAccount(repository).execute(current, updated)

    saved = repository.all()[0]

    assert saved.id == current.id
    assert saved.name == "New Instagram"
    assert saved.instagram_config == InstagramAccountConfig(
        instagram_user_id="67890",
        username="new_user",
    )


def test_update_to_other_destination_discards_instagram_config() -> None:
    repository = InMemoryAccountRepository()

    current = Account(
        name="Instagram",
        destination=PublishingDestination.INSTAGRAM,
        instagram_config=InstagramAccountConfig(
            instagram_user_id="12345",
            username="example_user",
        ),
    )
    repository.add(current)

    updated = Account(
        name="Facebook",
        destination=PublishingDestination.FACEBOOK,
        instagram_config=InstagramAccountConfig(
            instagram_user_id="67890",
            username="should_not_persist",
        ),
    )

    UpdateAccount(repository).execute(current, updated)

    saved = repository.all()[0]

    assert saved.id == current.id
    assert saved.destination == PublishingDestination.FACEBOOK
    assert saved.instagram_config is None


def test_update_instagram_account_does_not_keep_other_configs() -> None:
    repository = InMemoryAccountRepository()

    current = Account(
        name="Instagram",
        destination=PublishingDestination.INSTAGRAM,
        instagram_config=InstagramAccountConfig(
            instagram_user_id="12345",
            username="example_user",
        ),
    )
    repository.add(current)

    updated = Account(
        name="Updated Instagram",
        destination=PublishingDestination.INSTAGRAM,
        instagram_config=InstagramAccountConfig(
            instagram_user_id="67890",
            username="updated_user",
        ),
    )

    UpdateAccount(repository).execute(current, updated)

    saved = repository.all()[0]

    assert saved.wordpress_config is None
    assert saved.facebook_config is None
    assert saved.instagram_config is not None
