from unittest.mock import Mock

import pytest

from socialflow.application.publishing.remote_media_provider import (
    RemoteMediaProvider,
)
from socialflow.domain.account.account import Account
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.domain.post.remote_media import RemoteMedia
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.infrastructure.wordpress.wordpress_credential_keys import (
    WordPressCredentialKeys,
)
from socialflow.infrastructure.wordpress.wordpress_media_provider import (
    WordPressMediaProvider,
)


def make_wordpress_account() -> Account:
    return Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=WordPressConnectionConfig(
            site_url="https://example.com/",
            username="admin",
        ),
    )


def make_provider(
    records: list[dict] | dict | None = None,
    password: str | None = "test-password",
):
    """Create a WordPress media provider with mocked dependencies."""
    client = Mock()
    client.list_media.return_value = (
        [] if records is None else records
    )

    credential_store = Mock()
    credential_store.get.return_value = password

    provider = WordPressMediaProvider(
        client=client,
        credential_store=credential_store,
    )

    return provider, client, credential_store


def test_retrieves_wordpress_media_with_stored_credentials():
    account = make_wordpress_account()
    provider, client, credential_store = make_provider()

    result = provider.list_media(account, limit=20)

    assert result == ()
    assert isinstance(provider, RemoteMediaProvider)

    credential_store.get.assert_called_once_with(
        WordPressCredentialKeys.application_password(account)
    )

    client.list_media.assert_called_once_with(
        site_url="https://example.com",
        username="admin",
        application_password="test-password",
        limit=20,
    )


def test_converts_wordpress_media_records():
    records = [
        {
            "id": 123,
            "source_url": "https://example.com/uploads/photo.jpg",
            "title": {"rendered": "Example photo"},
            "media_details": {
                "sizes": {
                    "thumbnail": {
                        "source_url": (
                            "https://example.com/uploads/photo-150x150.jpg"
                        )
                    }
                }
            },
        },
        {
            "id": 456,
            "source_url": "https://example.com/uploads/banner.png",
            "title": {"rendered": "Banner"},
            "media_details": {"sizes": {}},
        },
    ]

    provider, _, _ = make_provider(records=records)

    result = provider.list_media(make_wordpress_account())

    assert result == (
        RemoteMedia(
            remote_id=123,
            destination=PublishingDestination.WORDPRESS,
            source_url="https://example.com/uploads/photo.jpg",
            title="Example photo",
            thumbnail_url=(
                "https://example.com/uploads/photo-150x150.jpg"
            ),
        ),
        RemoteMedia(
            remote_id=456,
            destination=PublishingDestination.WORDPRESS,
            source_url="https://example.com/uploads/banner.png",
            title="Banner",
        ),
    )


def test_rejects_non_wordpress_account():
    provider, client, credential_store = make_provider()

    account = Account(
        name="Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    with pytest.raises(ValueError, match="WordPress account"):
        provider.list_media(account)

    credential_store.get.assert_not_called()
    client.list_media.assert_not_called()


def test_rejects_incomplete_connection_settings():
    provider, client, credential_store = make_provider()

    account = Account(
        name="WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    with pytest.raises(ValueError, match="incomplete"):
        provider.list_media(account)

    credential_store.get.assert_not_called()
    client.list_media.assert_not_called()


def test_rejects_missing_application_password():
    provider, client, credential_store = make_provider(
        password=None
    )

    with pytest.raises(ValueError, match="password is missing"):
        provider.list_media(make_wordpress_account())

    credential_store.get.assert_called_once()
    client.list_media.assert_not_called()


@pytest.mark.parametrize(
    "limit",
    [0, -1, 101, True, False, "20", 1.5],
)
def test_rejects_invalid_media_limit(limit):
    provider, client, credential_store = make_provider()

    with pytest.raises(ValueError, match="Media limit"):
        provider.list_media(
            make_wordpress_account(),
            limit=limit,
        )

    credential_store.get.assert_not_called()
    client.list_media.assert_not_called()


@pytest.mark.parametrize(
    "record",
    [
        {"id": 0, "source_url": "https://example.com/a.jpg"},
        {"id": True, "source_url": "https://example.com/a.jpg"},
        {"id": 123, "source_url": "http://example.com/a.jpg"},
        {"id": 123, "source_url": None},
        {
            "id": 123,
            "source_url": "https://example.com/a.jpg",
            "title": {"rendered": 42},
        },
        {
            "id": 123,
            "source_url": "https://example.com/a.jpg",
            "media_details": {"sizes": {"thumbnail": "invalid"}},
        },
    ],
)
def test_rejects_malformed_wordpress_media(record):
    provider, _, _ = make_provider(records=[record])

    with pytest.raises(ValueError):
        provider.list_media(make_wordpress_account())


def test_rejects_non_list_response():
    provider, _, _ = make_provider(records={"id": 123})

    with pytest.raises(ValueError, match="media response"):
        provider.list_media(make_wordpress_account())