from unittest.mock import Mock

import pytest

from socialflow.domain.account.account import Account
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)
from socialflow.infrastructure.wordpress.wordpress_post_updater import (
    WordPressPostUpdater,
)


def make_account(
    destination=PublishingDestination.WORDPRESS,
    config=None,
):
    if config is None and destination == PublishingDestination.WORDPRESS:
        config = WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        )

    return Account(
        name="Main Account",
        destination=destination,
        wordpress_config=config,
    )


def make_updater(status=200, password="test-password"):
    client = Mock()
    client.update_post.return_value = status

    credential_store = Mock()
    credential_store.get.return_value = password

    updater = WordPressPostUpdater(
        client=client,
        credential_store=credential_store,
    )

    return updater, client, credential_store


def test_updates_post_using_stored_credentials():
    account = make_account()
    updater, client, store = make_updater()

    updater.update_post(
        account=account,
        post_id=123,
        content="Ažurirani sadržaj čćžšđ",
    )

    store.get.assert_called_once_with(
        WordPressCredentialKeys.application_password(account)
    )

    client.update_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="test-password",
        post_id=123,
        content="Ažurirani sadržaj čćžšđ",
    )


def test_rejects_non_wordpress_account():
    account = make_account(
        destination=PublishingDestination.FACEBOOK,
    )
    updater, client, store = make_updater()

    with pytest.raises(ValueError, match="WordPress account"):
        updater.update_post(account, 123, "Updated content")

    client.update_post.assert_not_called()
    store.get.assert_not_called()


def test_rejects_missing_wordpress_configuration():
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=None,
    )
    updater, client, store = make_updater()

    with pytest.raises(ValueError, match="settings are incomplete"):
        updater.update_post(account, 123, "Updated content")

    client.update_post.assert_not_called()
    store.get.assert_not_called()


@pytest.mark.parametrize(
    "site_url, username",
    [
        ("", "admin"),
        ("https://example.com", ""),
    ],
)
def test_rejects_incomplete_wordpress_configuration(site_url, username):
    account = make_account(
        config=WordPressConnectionConfig(
            site_url=site_url,
            username=username,
        ),
    )
    updater, client, store = make_updater()

    with pytest.raises(ValueError, match="settings are incomplete"):
        updater.update_post(account, 123, "Updated content")

    client.update_post.assert_not_called()
    store.get.assert_not_called()


@pytest.mark.parametrize("post_id", [0, -1, True, "123", None])
def test_rejects_invalid_post_id(post_id):
    updater, client, store = make_updater()

    with pytest.raises(ValueError, match="post ID"):
        updater.update_post(
            make_account(),
            post_id,
            "Updated content",
        )

    client.update_post.assert_not_called()
    store.get.assert_not_called()


@pytest.mark.parametrize("content", ["", "   ", None])
def test_rejects_empty_or_invalid_content(content):
    updater, client, store = make_updater()

    with pytest.raises(ValueError, match="content is required"):
        updater.update_post(make_account(), 123, content)

    client.update_post.assert_not_called()
    store.get.assert_not_called()


@pytest.mark.parametrize("password", [None, ""])
def test_rejects_missing_application_password(password):
    updater, client, store = make_updater(password=password)

    with pytest.raises(ValueError, match="password is missing"):
        updater.update_post(
            make_account(),
            123,
            "Updated content",
        )

    store.get.assert_called_once()
    client.update_post.assert_not_called()


@pytest.mark.parametrize("status", [400, 401, 403, 404, 500])
def test_rejects_unsuccessful_http_status(status):
    updater, client, store = make_updater(status=status)

    with pytest.raises(
        RuntimeError,
        match=f"WordPress post update failed \\(HTTP {status}\\)",
    ):
        updater.update_post(
            make_account(),
            123,
            "Updated content",
        )

    client.update_post.assert_called_once()
    store.get.assert_called_once()