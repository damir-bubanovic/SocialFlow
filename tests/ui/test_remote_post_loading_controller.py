
from threading import Event
from unittest.mock import Mock

from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.workers.remote_post_loading_controller import (
    RemotePostLoadingController,
)


def test_controller_starts_without_running_thread():
    controller = RemotePostLoadingController(
        list_remote_posts=Mock(),
    )

    assert not controller.is_running

    controller.shutdown()


def test_controller_loads_posts_in_background(qtbot):
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    list_remote_posts = Mock()
    list_remote_posts.execute.return_value = ()

    controller = RemotePostLoadingController(
        list_remote_posts=list_remote_posts,
    )

    try:
        with qtbot.waitSignal(
            controller.posts_ready,
            timeout=5000,
        ) as signal:
            controller.start(account)

        assert signal.args == [()]

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        list_remote_posts.execute.assert_called_once_with(
            account=account,
            limit=5,
        )
    finally:
        controller.shutdown()


def test_controller_reports_retrieval_failure(qtbot):
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    list_remote_posts = Mock()
    list_remote_posts.execute.side_effect = RuntimeError(
        "WordPress connection failed"
    )

    controller = RemotePostLoadingController(
        list_remote_posts=list_remote_posts,
    )

    try:
        with qtbot.waitSignal(
            controller.error_occurred,
            timeout=5000,
        ) as signal:
            controller.start(account)

        assert signal.args == ["WordPress connection failed"]

        qtbot.waitUntil(
            lambda: not controller.is_running,
            timeout=5000,
        )

        list_remote_posts.execute.assert_called_once_with(
            account=account,
            limit=5,
        )
    finally:
        controller.shutdown()


def test_controller_shutdown_waits_for_active_worker(qtbot):
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    worker_started = Event()
    allow_worker_to_finish = Event()

    def retrieve_posts(**kwargs):
        assert kwargs == {
            "account": account,
            "limit": 5,
        }

        worker_started.set()

        if not allow_worker_to_finish.wait(timeout=5):
            raise TimeoutError("Worker was not released")

        return ()

    list_remote_posts = Mock()
    list_remote_posts.execute.side_effect = retrieve_posts

    controller = RemotePostLoadingController(
        list_remote_posts=list_remote_posts,
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

        list_remote_posts.execute.assert_called_once_with(
            account=account,
            limit=5,
        )
    finally:
        allow_worker_to_finish.set()
        controller.shutdown()
