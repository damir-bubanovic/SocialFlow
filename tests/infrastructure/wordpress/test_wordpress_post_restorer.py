
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
from socialflow.infrastructure.wordpress.wordpress_post_restorer import (
    WordPressPostRestorer,
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


def make_restorer(status=200, password="test-password"):
    client = Mock()
    client.restore_post.return_value = status

    credential_store = Mock()
    credential_store.get.return_value = password

    restorer = WordPressPostRestorer(
        client=client,
        credential_store=credential_store,
    )

    return restorer, client, credential_store


def test_restores_post_using_stored_credentials():
    account = make_account()
    restorer, client, store = make_restorer()

    restorer.restore_post(account=account, post_id=123)

    store.get.assert_called_once_with(
        WordPressCredentialKeys.application_password(account)
    )

    client.restore_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="test-password",
        post_id=123,
    )


def test_rejects_non_wordpress_account():
    account = make_account(
        destination=PublishingDestination.FACEBOOK,
    )
    restorer, client, store = make_restorer()

    with pytest.raises(ValueError, match="WordPress account"):
        restorer.restore_post(account, 123)

    client.restore_post.assert_not_called()
    store.get.assert_not_called()


def test_rejects_missing_wordpress_configuration():
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=None,
    )
    restorer, client, store = make_restorer()

    with pytest.raises(
        ValueError,
        match="settings are incomplete",
    ):
        restorer.restore_post(account, 123)

    client.restore_post.assert_not_called()
    store.get.assert_not_called()


@pytest.mark.parametrize(
    ("site_url", "username"),
    [
        ("", "admin"),
        ("https://example.com", ""),
    ],
)
def test_rejects_incomplete_configuration(site_url, username):
    account = make_account(
        config=WordPressConnectionConfig(
            site_url=site_url,
            username=username,
        ),
    )
    restorer, client, store = make_restorer()

    with pytest.raises(
        ValueError,
        match="settings are incomplete",
    ):
        restorer.restore_post(account, 123)

    client.restore_post.assert_not_called()
    store.get.assert_not_called()


@pytest.mark.parametrize(
    "invalid_id",
    [0, -1, True, False, "123", None, 1.5],
)
def test_rejects_invalid_post_id(invalid_id):
    restorer, client, store = make_restorer()

    with pytest.raises(ValueError, match="post ID"):
        restorer.restore_post(
            make_account(),
            invalid_id,
        )

    client.restore_post.assert_not_called()
    store.get.assert_not_called()


@pytest.mark.parametrize("password", [None, ""])
def test_rejects_missing_application_password(password):
    restorer, client, store = make_restorer(password=password)

    with pytest.raises(ValueError, match="password is missing"):
        restorer.restore_post(make_account(), 123)

    store.get.assert_called_once()
    client.restore_post.assert_not_called()


@pytest.mark.parametrize(
    "status",
    [400, 401, 403, 404, 409, 500],
)
def test_rejects_unsuccessful_http_status(status):
    restorer, client, store = make_restorer(status=status)

    with pytest.raises(
        RuntimeError,
        match=f"WordPress post restore failed \\(HTTP {status}\\)",
    ):
        restorer.restore_post(make_account(), 123)

    client.restore_post.assert_called_once()
    store.get.assert_called_once()


def test_propagates_transport_failure():
    restorer, client, _store = make_restorer()
    client.restore_post.side_effect = ValueError(
        "WordPress did not confirm the post was restored as a draft."
    )

    with pytest.raises(ValueError, match="did not confirm"):
        restorer.restore_post(make_account(), 123)

    client.restore_post.assert_called_once()
