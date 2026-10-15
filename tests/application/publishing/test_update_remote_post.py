from unittest.mock import Mock

import pytest

from socialflow.application.publishing.update_remote_post import (
    UpdateRemotePost,
)


def test_update_remote_post_delegates_to_updater():
    updater = Mock()
    use_case = UpdateRemotePost(updater=updater)
    account = Mock()

    use_case.execute(
        account=account,
        post_id=123,
        content="Ažurirani sadržaj čćžšđ",
    )

    updater.update_post.assert_called_once_with(
        account=account,
        post_id=123,
        content="Ažurirani sadržaj čćžšđ",
    )


def test_update_remote_post_propagates_updater_errors():
    updater = Mock()
    updater.update_post.side_effect = RuntimeError(
        "WordPress post update failed (HTTP 403)."
    )

    use_case = UpdateRemotePost(updater=updater)

    with pytest.raises(
        RuntimeError,
        match="WordPress post update failed",
    ):
        use_case.execute(
            account=Mock(),
            post_id=123,
            content="Updated content",
        )

    updater.update_post.assert_called_once()