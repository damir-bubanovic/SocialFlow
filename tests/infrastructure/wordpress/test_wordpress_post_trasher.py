
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
from socialflow.infrastructure.wordpress.wordpress_post_trasher import (
    WordPressPostTrasher,
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


def make_trasher(status=200, password="test-password"):
    client = Mock()
    client.trash_post.return_value = status

    credential_store = Mock()
    credential_store.get.return_value = password

    trasher = WordPressPostTrasher(
        client=client,
        credential_store=credential_store,
    )

    return trasher, client, credential_store


def test_trashes_post_using_stored_credentials():
    account = make_account()
    trasher, client, store = make_trasher()

    trasher.trash_post(account=account, post_id=123)

    store.get.assert_called_once_with(
        WordPressCredentialKeys.application_password(account)
    )

    client.trash_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="test-password",
        post_id=123,
    )


def test_rejects_non_wordpress_account():
    account = make_account(
        destination=PublishingDestination.FACEBOOK,
    )
    trasher, client, store = make_trasher()

    with pytest.raises(ValueError, match="WordPress account"):
        trasher.trash_post(account, 123)

    client.trash_post.assert_not_called()
    store.get.assert_not_called()


def test_rejects_missing_wordpress_configuration():
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=None,
    )
    trasher, client, store = make_trasher()

    with pytest.raises(
        ValueError,
        match="settings are incomplete",
    ):
        trasher.trash_post(account, 123)

    client.trash_post.assert_not_called()
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
    trasher, client, store = make_trasher()

    with pytest.raises(
        ValueError,
        match="settings are incomplete",
    ):
        trasher.trash_post(account, 123)

    client.trash_post.assert_not_called()
    store.get.assert_not_called()


@pytest.mark.parametrize(
    "invalid_id",
    [0, -1, True, False, "123", None, 1.5],
)
def test_rejects_invalid_post_id(invalid_id):
    trasher, client, store = make_trasher()

    with pytest.raises(ValueError, match="post ID"):
        trasher.trash_post(
            make_account(),
            invalid_id,
        )

    client.trash_post.assert_not_called()
    store.get.assert_not_called()


@pytest.mark.parametrize("password", [None, ""])
def test_rejects_missing_application_password(password):
    trasher, client, store = make_trasher(password=password)

    with pytest.raises(ValueError, match="password is missing"):
        trasher.trash_post(make_account(), 123)

    store.get.assert_called_once()
    client.trash_post.assert_not_called()


@pytest.mark.parametrize(
    "status",
    [400, 401, 403, 404, 409, 500],
)
def test_rejects_unsuccessful_http_status(status):
    trasher, client, store = make_trasher(status=status)

    with pytest.raises(
        RuntimeError,
        match=f"WordPress post trash failed \\(HTTP {status}\\)",
    ):
        trasher.trash_post(make_account(), 123)

    client.trash_post.assert_called_once()
    store.get.assert_called_once()


def test_propagates_transport_failure():
    trasher, client, _store = make_trasher()
    client.trash_post.side_effect = ValueError(
        "WordPress did not confirm the post was moved to Trash."
    )

    with pytest.raises(ValueError, match="did not confirm"):
        trasher.trash_post(make_account(), 123)

    client.trash_post.assert_called_once()
