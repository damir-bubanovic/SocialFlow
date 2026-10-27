
from socialflow.application.publishing.remote_post_restorer import (
    RemotePostRestorer,
)
from socialflow.domain.account.account import Account


class RestoreRemotePost:
    """Restore an existing remote post from Trash as a draft."""

    def __init__(
        self,
        restorer: RemotePostRestorer,
    ) -> None:
        self._restorer = restorer

    def execute(
        self,
        account: Account,
        post_id: int,
    ) -> None:
        if type(post_id) is not int or post_id <= 0:
            raise ValueError(
                "A valid remote post ID is required."
            )

        self._restorer.restore_post(
            account=account,
            post_id=post_id,
        )
