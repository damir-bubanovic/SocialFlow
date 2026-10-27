
from unittest.mock import Mock

from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.workers.remote_trashed_post_loading_worker import (
    RemoteTrashedPostLoadingWorker,
)


def test_worker_emits_trashed_posts(qtbot):
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    use_case = Mock()
    use_case.execute.return_value = ()

    worker = RemoteTrashedPostLoadingWorker(
        list_trashed_remote_posts=use_case,
        account=account,
    )

    with qtbot.waitSignal(worker.finished, timeout=1000) as signal:
        worker.run()

    assert signal.args == [()]

    use_case.execute.assert_called_once_with(
        account=account,
        limit=50,
    )


def test_worker_emits_error_when_trash_retrieval_fails(qtbot):
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    use_case = Mock()
    use_case.execute.side_effect = RuntimeError(
        "WordPress Trash retrieval failed"
    )

    worker = RemoteTrashedPostLoadingWorker(
        list_trashed_remote_posts=use_case,
        account=account,
    )

    with qtbot.waitSignal(worker.failed, timeout=1000) as signal:
        worker.run()

    assert signal.args == [
        "WordPress Trash retrieval failed"
    ]

    use_case.execute.assert_called_once_with(
        account=account,
        limit=50,
    )
