from threading import Event
from unittest.mock import Mock

from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.workers.remote_media_loading_controller import (
    RemoteMediaLoadingController,
)


def make_account() -> Account:
    return Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )


def test_controller_starts_without_running_thread():
    controller = RemoteMediaLoadingController(
        list_remote_media=Mock(),
    )

    assert not controller.is_running
    controller.shutdown()


def test_controller_loads_media_in_background(qtbot):
    account = make_account()
    list_remote_media = Mock()
    list_remote_media.execute.return_value = ()

    controller = RemoteMediaLoadingController(
        list_remote_media=list_remote_media,
    )

    try:
        with qtbot.waitSignal(
            controller.media_ready,
            timeout=5000,
        ) as signal:
            controller.start(account, limit=20)

        assert signal.args == [()]

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        list_remote_media.execute.assert_called_once_with(
            account=account,
            limit=20,
        )
    finally:
        controller.shutdown()


def test_controller_reports_retrieval_failure(qtbot):
    account = make_account()
    list_remote_media = Mock()
    list_remote_media.execute.side_effect = RuntimeError(
        "WordPress media request failed"
    )

    controller = RemoteMediaLoadingController(
        list_remote_media=list_remote_media,
    )

    try:
        with qtbot.waitSignal(
            controller.error_occurred,
            timeout=5000,
        ) as signal:
            controller.start(account)

        assert signal.args == ["WordPress media request failed"]

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )
    finally:
        controller.shutdown()


def test_controller_shutdown_waits_for_active_worker(qtbot):
    account = make_account()

    worker_started = Event()
    allow_worker_to_finish = Event()

    def retrieve_media(**kwargs):
        assert kwargs == {
            "account": account,
            "limit": 50,
        }

        worker_started.set()

        if not allow_worker_to_finish.wait(timeout=5):
            raise TimeoutError("Worker was not released")

        return ()

    list_remote_media = Mock()
    list_remote_media.execute.side_effect = retrieve_media

    controller = RemoteMediaLoadingController(
        list_remote_media=list_remote_media,
    )

    try:
        controller.start(account)

        qtbot.waitUntil(
            worker_started.is_set,
            timeout=5000,
        )

        assert controller.is_running

        allow_worker_to_finish.set()
        controller.shutdown()

        assert not controller.is_running

        list_remote_media.execute.assert_called_once_with(
            account=account,
            limit=50,
        )
    finally:
        allow_worker_to_finish.set()
        controller.shutdown()