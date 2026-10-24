from unittest.mock import Mock

import pytest

from socialflow.application.publishing.list_remote_media import (
    ListRemoteMedia,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_media import RemoteMedia
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)


def test_list_remote_media_forwards_account_and_limit():
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    media = RemoteMedia(
        remote_id=123,
        destination=PublishingDestination.WORDPRESS,
        source_url="https://example.com/photo.jpg",
        title="Photo",
    )

    provider = Mock()
    provider.list_media.return_value = (media,)

    use_case = ListRemoteMedia(provider)

    result = use_case.execute(
        account=account,
        limit=20,
    )

    assert result == (media,)

    provider.list_media.assert_called_once_with(
        account=account,
        limit=20,
    )


def test_list_remote_media_uses_default_limit():
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    provider = Mock()
    provider.list_media.return_value = ()

    result = ListRemoteMedia(provider).execute(account)

    assert result == ()

    provider.list_media.assert_called_once_with(
        account=account,
        limit=50,
    )


@pytest.mark.parametrize(
    "limit",
    [0, -1, 101, True, False, "20", 1.5],
)
def test_list_remote_media_rejects_invalid_limit(limit):
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    provider = Mock()
    use_case = ListRemoteMedia(provider)

    with pytest.raises(ValueError, match="Media limit"):
        use_case.execute(
            account=account,
            limit=limit,
        )

    provider.list_media.assert_not_called()