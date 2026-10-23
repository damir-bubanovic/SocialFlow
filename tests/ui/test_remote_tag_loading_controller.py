
from threading import Event
from unittest.mock import Mock

from socialflow.application.tags.list_remote_tags import (
    ListRemoteTags,
)
from socialflow.domain.account.account import Account
from socialflow.domain.post.remote_tag import RemoteTag
from socialflow.domain.publishing.destination import (
    PublishingDestination,
)
from socialflow.ui.workers.remote_tag_loading_controller import (
    RemoteTagLoadingController,
)


def make_account() -> Account:
    return Account(
        name="WordPress",
        destination=PublishingDestination.WORDPRESS,
    )



def test_controller_loads_remote_tags(qtbot) -> None:
    account = make_account()
    expected_tags = (
        RemoteTag(remote_id=12, name="Python"),
        RemoteTag(remote_id=34, name="SocialFlow"),
    )

    list_remote_tags = Mock(spec=ListRemoteTags)
    list_remote_tags.execute.return_value = expected_tags

    controller = RemoteTagLoadingController(list_remote_tags)
    received_tags = Mock()

    controller.tags_ready.connect(received_tags)

    try:
        with qtbot.waitSignals(
            [controller.tags_ready, controller.finished],
            timeout=5000,
            order="strict",
        ):
            controller.start(account)

        received_tags.assert_called_once_with(expected_tags)
        assert not controller.is_running
        list_remote_tags.execute.assert_called_once_with(account)
    finally:
        controller.shutdown()



def test_controller_reports_remote_tag_errors(qtbot) -> None:
    account = make_account()

    list_remote_tags = Mock(spec=ListRemoteTags)
    list_remote_tags.execute.side_effect = RuntimeError(
        "WordPress connection failed"
    )

    controller = RemoteTagLoadingController(list_remote_tags)
    error_listener = Mock()
    controller.error_occurred.connect(error_listener)

    try:
        with qtbot.waitSignals(
            [controller.error_occurred, controller.finished],
            timeout=5000,
            order="strict",
        ):
            controller.start(account)

        error_listener.assert_called_once_with(
            "WordPress connection failed"
        )
        assert not controller.is_running
    finally:
        controller.shutdown()


def test_controller_prevents_concurrent_loading(qtbot) -> None:
    account = make_account()
    started = Event()
    release = Event()

    list_remote_tags = Mock(spec=ListRemoteTags)

    def load_tags(_account: Account) -> tuple[RemoteTag, ...]:
        started.set()

        if not release.wait(timeout=5):
            raise TimeoutError("Test worker was not released.")

        return ()

    list_remote_tags.execute.side_effect = load_tags

    controller = RemoteTagLoadingController(list_remote_tags)

    try:
        controller.start(account)

        qtbot.waitUntil(started.is_set, timeout=5000)

        controller.start(account)

        assert controller.is_running
        list_remote_tags.execute.assert_called_once_with(account)
    finally:
        release.set()
        controller.shutdown()

    assert not controller.is_running


def test_controller_does_not_restart_after_shutdown() -> None:
    account = make_account()
    list_remote_tags = Mock(spec=ListRemoteTags)

    controller = RemoteTagLoadingController(list_remote_tags)

    controller.shutdown()
    controller.start(account)

    assert not controller.is_running
    list_remote_tags.execute.assert_not_called()
