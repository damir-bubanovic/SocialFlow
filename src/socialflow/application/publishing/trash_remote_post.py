
from socialflow.application.publishing.remote_post_trasher import (
    RemotePostTrasher,
)
from socialflow.domain.account.account import Account


class TrashRemotePost:
    """Move an existing remote post to Trash."""

    def __init__(
        self,
        trasher: RemotePostTrasher,
    ) -> None:
        self._trasher = trasher

    def execute(
        self,
        account: Account,
        post_id: int,
    ) -> None:
        if type(post_id) is not int or post_id <= 0:
            raise ValueError(
                "A valid remote post ID is required."
            )

        self._trasher.trash_post(
            account=account,
            post_id=post_id,
        )
