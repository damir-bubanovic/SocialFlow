from unittest.mock import Mock

import pytest

from socialflow.domain.account.account import Account
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)
from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag
from socialflow.infrastructure.wordpress.wordpress_tag_provider import (
    WordPressTagProvider,
)


def make_account(
    *,
    destination: PublishingDestination = PublishingDestination.WORDPRESS,
    config: WordPressConnectionConfig | None = None,
) -> Account:
    if config is None:
        config = WordPressConnectionConfig(
            site_url="https://example.com/",
            username="admin",
        )

    return Account(
        name="Test WordPress",
        destination=destination,
        wordpress_config=config,
    )


def test_provider_lists_wordpress_tags() -> None:
    account = make_account()

    tag_client = Mock()
    tag_client.list_tags.return_value = (
        WordPressTag(id=12, name="Python"),
        WordPressTag(id=34, name="SocialFlow"),
    )

    credential_store = Mock()
    credential_store.get.return_value = "secret"

    provider = WordPressTagProvider(
        tag_client=tag_client,
        credential_store=credential_store,
    )

    result = provider.list_tags(account)

    assert result == (
        Tag(name="Python"),
        Tag(name="SocialFlow"),
    )

    credential_store.get.assert_called_once_with(
        WordPressCredentialKeys.application_password(account)
    )

    tag_client.list_tags.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
    )


@pytest.mark.parametrize("password", [None, ""])
def test_provider_rejects_missing_credentials(password) -> None:
    account = make_account()

    tag_client = Mock()
    credential_store = Mock()
    credential_store.get.return_value = password

    provider = WordPressTagProvider(
        tag_client=tag_client,
        credential_store=credential_store,
    )

    with pytest.raises(ValueError, match="password is missing"):
        provider.list_tags(account)

    tag_client.list_tags.assert_not_called()


def test_provider_rejects_missing_configuration() -> None:
    account = Account(
        name="Test WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=None,
    )

    tag_client = Mock()
    credential_store = Mock()

    provider = WordPressTagProvider(
        tag_client=tag_client,
        credential_store=credential_store,
    )

    with pytest.raises(ValueError, match="settings are incomplete"):
        provider.list_tags(account)

    credential_store.get.assert_not_called()
    tag_client.list_tags.assert_not_called()


def test_provider_rejects_incomplete_configuration() -> None:
    account = make_account(
        config=WordPressConnectionConfig(
            site_url="",
            username="admin",
        )
    )

    tag_client = Mock()
    credential_store = Mock()

    provider = WordPressTagProvider(
        tag_client=tag_client,
        credential_store=credential_store,
    )

    with pytest.raises(ValueError, match="settings are incomplete"):
        provider.list_tags(account)

    credential_store.get.assert_not_called()
    tag_client.list_tags.assert_not_called()


def test_provider_rejects_non_wordpress_account() -> None:
    account = make_account(
        destination=PublishingDestination.FACEBOOK,
    )

    tag_client = Mock()
    credential_store = Mock()

    provider = WordPressTagProvider(
        tag_client=tag_client,
        credential_store=credential_store,
    )

    with pytest.raises(ValueError, match="WordPress account"):
        provider.list_tags(account)

    credential_store.get.assert_not_called()
    tag_client.list_tags.assert_not_called()



def test_provider_creates_wordpress_tag() -> None:
    account = make_account()

    tag_client = Mock()
    tag_client.create_tag.return_value = WordPressTag(
        id=42,
        name="Python",
    )

    credential_store = Mock()
    credential_store.get.return_value = "secret"

    provider = WordPressTagProvider(
        tag_client=tag_client,
        credential_store=credential_store,
    )

    result = provider.create_tag(
        account,
        Tag(name="Python"),
    )

    assert result == Tag(name="Python")

    credential_store.get.assert_called_once_with(
        WordPressCredentialKeys.application_password(account)
    )

    tag_client.create_tag.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
        name="Python",
    )


@pytest.mark.parametrize(
    "application_password",
    [None, ""],
)
def test_provider_rejects_tag_creation_without_credentials(
    application_password: str | None,
) -> None:
    account = make_account()

    tag_client = Mock()
    credential_store = Mock()
    credential_store.get.return_value = application_password

    provider = WordPressTagProvider(
        tag_client=tag_client,
        credential_store=credential_store,
    )

    with pytest.raises(
        ValueError,
        match="application password is missing",
    ):
        provider.create_tag(
            account,
            Tag(name="Python"),
        )

    tag_client.create_tag.assert_not_called()


def test_provider_rejects_tag_creation_without_config() -> None:
    account = Account(
        name="WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    tag_client = Mock()
    credential_store = Mock()

    provider = WordPressTagProvider(
        tag_client=tag_client,
        credential_store=credential_store,
    )

    with pytest.raises(
        ValueError,
        match="connection settings are incomplete",
    ):
        provider.create_tag(account, Tag(name="Python"))

    credential_store.get.assert_not_called()
    tag_client.create_tag.assert_not_called()


def test_provider_rejects_tag_creation_for_non_wordpress_account() -> None:
    account = Account(
        name="Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    tag_client = Mock()
    credential_store = Mock()

    provider = WordPressTagProvider(
        tag_client=tag_client,
        credential_store=credential_store,
    )

    with pytest.raises(
        ValueError,
        match="WordPress account is required",
    ):
        provider.create_tag(account, Tag(name="Python"))

    credential_store.get.assert_not_called()
    tag_client.create_tag.assert_not_called()
