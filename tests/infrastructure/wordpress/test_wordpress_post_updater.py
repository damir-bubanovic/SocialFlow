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


def test_updates_existing_post_tags():
    account = make_account()
    updater, client, store = make_updater()

    updater.update_post(
        account=account,
        post_id=123,
        content="Updated content",
        tags=(12, 34),
    )

    client.update_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="test-password",
        post_id=123,
        content="Updated content",
        tags=(12, 34),
    )


def test_removes_all_existing_post_tags():
    account = make_account()
    updater, client, store = make_updater()

    updater.update_post(
        account=account,
        post_id=123,
        content="Updated content",
        tags=(),
    )

    client.update_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="test-password",
        post_id=123,
        content="Updated content",
        tags=(),
    )


@pytest.mark.parametrize(
    "tags",
    [
        (0,),
        (-1,),
        (True,),
        ("12",),
        (12.5,),
        (None,),
        [12],
    ],
)
def test_rejects_invalid_existing_post_tags(tags):
    updater, client, store = make_updater()

    with pytest.raises(
        ValueError,
        match="WordPress tag IDs must be positive integers",
    ):
        updater.update_post(
            account=make_account(),
            post_id=123,
            content="Updated content",
            tags=tags,
        )

    client.update_post.assert_not_called()
    store.get.assert_not_called()

def test_updates_existing_post_featured_image():
    account = make_account()
    updater, client, store = make_updater()

    updater.update_post(
        account=account,
        post_id=123,
        content="Updated content",
        featured_media_id=456,
    )

    client.update_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="test-password",
        post_id=123,
        content="Updated content",
        featured_media_id=456,
    )

    store.get.assert_called_once()


def test_removes_existing_post_featured_image():
    account = make_account()
    updater, client, store = make_updater()

    updater.update_post(
        account=account,
        post_id=123,
        content="Updated content",
        featured_media_id=0,
    )

    client.update_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="test-password",
        post_id=123,
        content="Updated content",
        featured_media_id=0,
    )

    store.get.assert_called_once()


def test_updates_post_tags_and_featured_image_together():
    account = make_account()
    updater, client, store = make_updater()

    updater.update_post(
        account=account,
        post_id=123,
        content="Updated content",
        tags=(12, 34),
        featured_media_id=456,
    )

    client.update_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="test-password",
        post_id=123,
        content="Updated content",
        tags=(12, 34),
        featured_media_id=456,
    )

    store.get.assert_called_once()


@pytest.mark.parametrize(
    "featured_media_id",
    [
        -1,
        True,
        False,
        "123",
        12.5,
    ],
)
def test_rejects_invalid_featured_media_id(featured_media_id):
    updater, client, store = make_updater()

    with pytest.raises(
        ValueError,
        match="WordPress featured media ID",
    ):
        updater.update_post(
            account=make_account(),
            post_id=123,
            content="Updated content",
            featured_media_id=featured_media_id,
        )

    client.update_post.assert_not_called()
    store.get.assert_not_called()

@pytest.mark.parametrize(
    "status",
    ("draft", "pending", "private", "publish"),
)
def test_updates_wordpress_post_status(status):
    account = make_account()
    updater, client, _ = make_updater()

    updater.update_post(
        account=account,
        post_id=123,
        content="Updated content",
        status=status,
    )

    client.update_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="test-password",
        post_id=123,
        content="Updated content",
        status=status,
    )


@pytest.mark.parametrize(
    "status",
    ("", "scheduled", "trash", "PUBLISH", 123, True),
)
def test_rejects_unsupported_wordpress_post_status(status):
    account = make_account()
    updater, client, _ = make_updater()

    with pytest.raises(
        ValueError,
        match="Unsupported WordPress post status",
    ):
        updater.update_post(
            account=account,
            post_id=123,
            content="Updated content",
            status=status,
        )

    client.update_post.assert_not_called()



@pytest.mark.parametrize(
    "featured_media_id",
    [789, 0],
    ids=["replace-image", "remove-image"],
)
def test_featured_image_change_reaches_wordpress_client(
    featured_media_id,
):
    updater, client, store = make_updater()

    updater.update_post(
        account=make_account(),
        post_id=123,
        content="Updated content čćžšđ",
        featured_media_id=featured_media_id,
    )

    kwargs = client.update_post.call_args.kwargs

    assert kwargs["post_id"] == 123
    assert kwargs["featured_media_id"] == featured_media_id
    assert "tags" not in kwargs
    assert "status" not in kwargs


@pytest.mark.parametrize(
    "invalid_id",
    [-1, True, False, 1.5, "789", [], {}],
)
def test_rejects_invalid_featured_media_ids_before_network_call(
    invalid_id,
):
    updater, client, store = make_updater()

    with pytest.raises(
        ValueError,
        match="featured media ID",
    ):
        updater.update_post(
            account=make_account(),
            post_id=123,
            content="Updated content",
            featured_media_id=invalid_id,
        )

    client.update_post.assert_not_called()
    store.get.assert_not_called()


def test_featured_image_change_propagates_wordpress_failure():
    updater, client, store = make_updater(status=403)

    with pytest.raises(
        RuntimeError,
        match="WordPress post update failed",
    ):
        updater.update_post(
            account=make_account(),
            post_id=123,
            content="Updated content",
            featured_media_id=789,
        )

    client.update_post.assert_called_once()



@pytest.mark.parametrize(
    "title",
    ["Updated title", "Novi naslov čćžšđ"],
)
def test_updates_wordpress_post_title(title):
    updater, client, store = make_updater()

    updater.update_post(
        account=make_account(),
        post_id=123,
        content="Updated content",
        title=title,
    )

    client.update_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="test-password",
        post_id=123,
        content="Updated content",
        title=title,
    )

    store.get.assert_called_once()


@pytest.mark.parametrize(
    "title",
    ["", "   ", 123, True, [], None],
)
def test_wordpress_updater_rejects_invalid_title_except_none(title):
    updater, client, store = make_updater()

    if title is None:
        updater.update_post(
            account=make_account(),
            post_id=123,
            content="Updated content",
            title=title,
        )
        client.update_post.assert_called_once()
    else:
        with pytest.raises(
            ValueError,
            match="WordPress post title",
        ):
            updater.update_post(
                account=make_account(),
                post_id=123,
                content="Updated content",
                title=title,
            )

        client.update_post.assert_not_called()
        store.get.assert_not_called()


def test_wordpress_updater_combines_title_and_excerpt():
    updater, client, _store = make_updater()

    updater.update_post(
        account=make_account(),
        post_id=123,
        content="Updated content",
        title="Novi naslov",
        excerpt="Novi sažetak",
        tags=(12, 34),
        status="draft",
    )

    client.update_post.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="test-password",
        post_id=123,
        content="Updated content",
        tags=(12, 34),
        status="draft",
        excerpt="Novi sažetak",
        title="Novi naslov",
    )
