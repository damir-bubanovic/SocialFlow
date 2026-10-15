from unittest.mock import Mock

from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.workers.remote_post_loading_worker import (
    RemotePostLoadingWorker,
)


def test_worker_emits_retrieved_posts(qtbot):
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    list_remote_posts = Mock()
    list_remote_posts.execute.return_value = ()

    worker = RemotePostLoadingWorker(
        list_remote_posts=list_remote_posts,
        account=account,
    )

    with qtbot.waitSignal(worker.finished, timeout=1000) as signal:
        worker.run()

    assert signal.args == [()]

    list_remote_posts.execute.assert_called_once_with(
        account=account,
        limit=5,
    )


def test_worker_emits_error_when_retrieval_fails(qtbot):
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    list_remote_posts = Mock()
    list_remote_posts.execute.side_effect = RuntimeError(
        "WordPress connection failed"
    )

    worker = RemotePostLoadingWorker(
        list_remote_posts=list_remote_posts,
        account=account,
    )

    with qtbot.waitSignal(worker.failed, timeout=1000) as signal:
        worker.run()

    assert signal.args == ["WordPress connection failed"]