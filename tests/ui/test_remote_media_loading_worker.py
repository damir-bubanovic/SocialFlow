from unittest.mock import Mock

from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.workers.remote_media_loading_worker import (
    RemoteMediaLoadingWorker,
)


def make_account() -> Account:
    return Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )


def test_worker_emits_retrieved_media(qtbot):
    account = make_account()
    list_remote_media = Mock()
    list_remote_media.execute.return_value = ()

    worker = RemoteMediaLoadingWorker(
        list_remote_media=list_remote_media,
        account=account,
        limit=20,
    )

    with qtbot.waitSignal(worker.finished, timeout=1000) as signal:
        worker.run()

    assert signal.args == [()]
    list_remote_media.execute.assert_called_once_with(
        account=account,
        limit=20,
    )


def test_worker_uses_default_limit(qtbot):
    account = make_account()
    list_remote_media = Mock()
    list_remote_media.execute.return_value = ()

    worker = RemoteMediaLoadingWorker(
        list_remote_media=list_remote_media,
        account=account,
    )

    with qtbot.waitSignal(worker.finished, timeout=1000):
        worker.run()

    list_remote_media.execute.assert_called_once_with(
        account=account,
        limit=50,
    )


def test_worker_emits_error_when_retrieval_fails(qtbot):
    account = make_account()
    list_remote_media = Mock()
    list_remote_media.execute.side_effect = RuntimeError(
        "WordPress media request failed"
    )

    worker = RemoteMediaLoadingWorker(
        list_remote_media=list_remote_media,
        account=account,
    )

    with qtbot.waitSignal(worker.failed, timeout=1000) as signal:
        worker.run()

    assert signal.args == ["WordPress media request failed"]