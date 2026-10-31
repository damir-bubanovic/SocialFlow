
from unittest.mock import Mock

import pytest

from socialflow.domain.account.account import Account
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.domain.post.remote_category import RemoteCategory
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_category import (
    WordPressCategory,
)
from socialflow.infrastructure.wordpress.wordpress_category_client import (
    WordPressCategoryClient,
)
from socialflow.infrastructure.wordpress.wordpress_category_provider import (
    WordPressCategoryProvider,
)
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)


def make_account(
    destination=PublishingDestination.WORDPRESS,
    config=None,
):
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


def make_provider(password="secret"):
    client = Mock(spec=WordPressCategoryClient)
    credentials = Mock()
    credentials.get.return_value = password

    return (
        WordPressCategoryProvider(client, credentials),
        client,
        credentials,
    )


def test_provider_lists_categories_and_subcategories():
    account = make_account()
    provider, client, credentials = make_provider()

    client.list_categories.return_value = (
        WordPressCategory(10, "Technology"),
        WordPressCategory(20, "Python", 10),
    )

    result = provider.list_remote_categories(account)

    assert result == (
        RemoteCategory(10, "Technology"),
        RemoteCategory(20, "Python", 10),
    )

    credentials.get.assert_called_once_with(
        WordPressCredentialKeys.application_password(account)
    )

    client.list_categories.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
    )


def test_provider_returns_empty_category_list():
    provider, client, _ = make_provider()
    client.list_categories.return_value = ()

    assert provider.list_remote_categories(make_account()) == ()


def test_provider_creates_top_level_category():
    account = make_account()
    provider, client, _ = make_provider()

    client.create_category.return_value = WordPressCategory(
        30, "Tutorials"
    )

    result = provider.create_category(
        account,
        "Tutorials",
    )

    assert result == RemoteCategory(30, "Tutorials")

    client.create_category.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
        name="Tutorials",
        parent_id=0,
    )


def test_provider_creates_subcategory():
    account = make_account()
    provider, client, _ = make_provider()

    client.create_category.return_value = WordPressCategory(
        20, "Python", 10
    )

    result = provider.create_category(
        account,
        "Python",
        parent_id=10,
    )

    assert result == RemoteCategory(20, "Python", 10)

    client.create_category.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="secret",
        name="Python",
        parent_id=10,
    )


@pytest.mark.parametrize("password", [None, ""])
@pytest.mark.parametrize("operation", ["list", "create"])
def test_provider_rejects_missing_password(password, operation):
    account = make_account()
    provider, client, _ = make_provider(password)

    with pytest.raises(ValueError, match="password is missing"):
        if operation == "list":
            provider.list_remote_categories(account)
        else:
            provider.create_category(account, "Python")

    client.list_categories.assert_not_called()
    client.create_category.assert_not_called()


@pytest.mark.parametrize("operation", ["list", "create"])
def test_provider_rejects_missing_configuration(operation):
    account = Account(
        name="WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=None,
    )
    provider, client, credentials = make_provider()

    with pytest.raises(ValueError, match="settings are incomplete"):
        if operation == "list":
            provider.list_remote_categories(account)
        else:
            provider.create_category(account, "Python")

    credentials.get.assert_not_called()
    client.list_categories.assert_not_called()
    client.create_category.assert_not_called()


@pytest.mark.parametrize("operation", ["list", "create"])
def test_provider_rejects_incomplete_configuration(operation):
    account = make_account(
        config=WordPressConnectionConfig(
            site_url="",
            username="admin",
        )
    )
    provider, client, credentials = make_provider()

    with pytest.raises(ValueError, match="settings are incomplete"):
        if operation == "list":
            provider.list_remote_categories(account)
        else:
            provider.create_category(account, "Python")

    credentials.get.assert_not_called()
    client.list_categories.assert_not_called()
    client.create_category.assert_not_called()


@pytest.mark.parametrize("operation", ["list", "create"])
def test_provider_rejects_non_wordpress_account(operation):
    account = make_account(
        destination=PublishingDestination.FACEBOOK,
    )
    provider, client, credentials = make_provider()

    with pytest.raises(ValueError, match="WordPress account"):
        if operation == "list":
            provider.list_remote_categories(account)
        else:
            provider.create_category(account, "Python")

    credentials.get.assert_not_called()
    client.list_categories.assert_not_called()
    client.create_category.assert_not_called()


def test_provider_propagates_category_client_errors():
    provider, client, _ = make_provider()
    client.list_categories.side_effect = ConnectionError(
        "WordPress unavailable"
    )

    with pytest.raises(ConnectionError, match="unavailable"):
        provider.list_remote_categories(make_account())


def test_provider_propagates_creation_errors():
    provider, client, _ = make_provider()
    client.create_category.side_effect = ValueError(
        "Existing category has a different parent."
    )

    with pytest.raises(ValueError, match="different parent"):
        provider.create_category(
            make_account(),
            "Python",
            parent_id=10,
        )
