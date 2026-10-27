
from unittest.mock import Mock

import pytest

from socialflow.application.publishing.trash_remote_post import (
    TrashRemotePost,
)


def test_trash_remote_post_forwards_account_and_id():
    trasher = Mock()
    use_case = TrashRemotePost(trasher=trasher)
    account = Mock()

    use_case.execute(
        account=account,
        post_id=123,
    )

    trasher.trash_post.assert_called_once_with(
        account=account,
        post_id=123,
    )


@pytest.mark.parametrize(
    "invalid_id",
    [0, -1, True, False, "123", None, 1.5],
)
def test_trash_remote_post_rejects_invalid_id(invalid_id):
    trasher = Mock()
    use_case = TrashRemotePost(trasher=trasher)

    with pytest.raises(
        ValueError,
        match="remote post ID",
    ):
        use_case.execute(
            account=Mock(),
            post_id=invalid_id,
        )

    trasher.trash_post.assert_not_called()
