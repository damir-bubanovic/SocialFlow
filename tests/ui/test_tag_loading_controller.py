
from threading import Event
from unittest.mock import Mock

from socialflow.application.tags.list_tags import ListTags
from socialflow.domain.account.account import Account
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.ui.workers.tag_loading_controller import (
    TagLoadingController,
)


def make_account() -> Account:
    return Account(
        name="WordPress",
        destination=PublishingDestination.WORDPRESS,
    )


def test_controller_emits_loaded_tags(qtbot) -> None:
    account = make_account()
    expected_tags = (Tag(name="Python"),)

    list_tags = Mock(spec=ListTags)
    list_tags.execute.return_value = expected_tags

    controller = TagLoadingController(list_tags)
    listener = Mock()
    controller.tags_ready.connect(listener)

    with qtbot.waitSignals(
        [controller.tags_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(account)

    list_tags.execute.assert_called_once_with(account)
    listener.assert_called_once_with(expected_tags)
    assert not controller.is_running


def test_controller_emits_error(qtbot) -> None:
    account = make_account()

    list_tags = Mock(spec=ListTags)
    list_tags.execute.side_effect = ValueError(
        "WordPress application password is missing."
    )

    controller = TagLoadingController(list_tags)
    listener = Mock()
    controller.error_occurred.connect(listener)

    with qtbot.waitSignals(
        [controller.error_occurred, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(account)

    listener.assert_called_once_with(
        "WordPress application password is missing."
    )
    assert not controller.is_running


def test_controller_prevents_concurrent_loading(qtbot) -> None:
    account = make_account()
    started = Event()
    release = Event()

    list_tags = Mock(spec=ListTags)

    def load_tags(_account: Account) -> tuple[Tag, ...]:
        started.set()
        if not release.wait(timeout=2):
            raise TimeoutError("Test worker was not released.")
        return (Tag(name="Python"),)

    list_tags.execute.side_effect = load_tags

    controller = TagLoadingController(list_tags)

    try:
        controller.start(account)

        assert started.wait(timeout=2)
        assert controller.is_running

        controller.start(account)
        assert list_tags.execute.call_count == 1
    finally:
        release.set()
        with qtbot.waitSignal(controller.finished, timeout=3000):
            controller.shutdown()

    assert not controller.is_running

def test_controller_can_load_another_account_after_finishing(
    qtbot,
) -> None:
    """Allow another request after the previous thread is cleaned up."""
    first_account = Account(
        name="WordPress One",
        destination=PublishingDestination.WORDPRESS,
    )
    second_account = Account(
        name="WordPress Two",
        destination=PublishingDestination.WORDPRESS,
    )

    first_tags = (Tag(name="Python"),)
    second_tags = (Tag(name="Croatian"),)

    list_tags = Mock(spec=ListTags)
    list_tags.execute.side_effect = [
        first_tags,
        second_tags,
    ]

    controller = TagLoadingController(list_tags)
    received_tags = Mock()
    controller.tags_ready.connect(received_tags)

    with qtbot.waitSignals(
        [controller.tags_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(first_account)

    assert not controller.is_running

    with qtbot.waitSignals(
        [controller.tags_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(second_account)

    assert not controller.is_running

    assert list_tags.execute.call_count == 2
    assert list_tags.execute.call_args_list == [
        ((first_account,),),
        ((second_account,),),
    ]

    assert received_tags.call_args_list == [
        ((first_tags,),),
        ((second_tags,),),
    ]

def test_controller_returns_tags_in_original_order(qtbot) -> None:
    """Preserve tag order when loading finishes."""
    account = make_account()
    expected_tags = (
        Tag(name="Python"),
        Tag(name="Croatian"),
        Tag(name="WordPress"),
    )

    list_tags = Mock(spec=ListTags)
    list_tags.execute.return_value = expected_tags

    controller = TagLoadingController(list_tags)
    received = Mock()
    controller.tags_ready.connect(received)

    with qtbot.waitSignals(
        [controller.tags_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(account)

    received.assert_called_once_with(expected_tags)
    assert not controller.is_running

def test_tag_loading_controller_shutdown_during_active_request() -> None:
    """Shutdown must wait for an active worker and release its thread."""
    account = make_account()
    started = Event()
    release = Event()

    list_tags = Mock(spec=ListTags)

    def load_tags(_account: Account) -> tuple[Tag, ...]:
        started.set()

        if not release.wait(timeout=5):
            raise TimeoutError("Test worker was not released.")

        return ()

    list_tags.execute.side_effect = load_tags

    controller = TagLoadingController(list_tags)

    try:
        controller.start(account)

        assert started.wait(timeout=2)
        assert controller.is_running

        release.set()
        controller.shutdown()

        assert not controller.is_running
        assert controller._thread is None
        assert controller._worker is None

        list_tags.execute.assert_called_once_with(account)

    finally:
        release.set()
        controller.shutdown()

def test_controller_shutdown_waits_for_blocked_worker() -> None:
    """Shutdown must wait for an active worker to complete."""
    from threading import Thread
    from time import monotonic

    account = make_account()
    started = Event()
    release = Event()

    list_tags = Mock(spec=ListTags)

    def load_tags(_account: Account) -> tuple[Tag, ...]:
        started.set()

        if not release.wait(timeout=5):
            raise TimeoutError("Test worker was not released.")

        return ()

    list_tags.execute.side_effect = load_tags

    controller = TagLoadingController(list_tags)

    def release_worker() -> None:
        if started.wait(timeout=2):
            release.wait(timeout=0.1)
            release.set()

    releaser = Thread(target=release_worker, daemon=True)

    try:
        controller.start(account)
        assert started.wait(timeout=2)

        releaser.start()

        start_time = monotonic()
        controller.shutdown()
        elapsed = monotonic() - start_time

        assert elapsed >= 0.08
        assert not controller.is_running
        assert controller._thread is None
        assert controller._worker is None

        list_tags.execute.assert_called_once_with(account)

    finally:
        release.set()
        releaser.join(timeout=2) if releaser.ident is not None else None
        controller.shutdown()

def test_controller_does_not_restart_after_shutdown() -> None:
    """A stopped controller must reject new loading requests."""
    account = make_account()
    list_tags = Mock(spec=ListTags)

    controller = TagLoadingController(list_tags)
    controller.shutdown()

    controller.start(account)

    assert not controller.is_running
    list_tags.execute.assert_not_called()

def test_controller_shutdown_is_idempotent(qtbot) -> None:
    """Repeated shutdown calls must not restart or retain a worker."""
    account = make_account()
    list_tags = Mock(spec=ListTags)
    list_tags.execute.return_value = ()

    controller = TagLoadingController(list_tags)

    try:
        with qtbot.waitSignal(controller.finished, timeout=2000):
            controller.start(account)

        assert not controller.is_running

        controller.shutdown()
        controller.shutdown()

        controller.start(account)

        assert not controller.is_running
        assert controller._thread is None
        assert controller._worker is None

        list_tags.execute.assert_called_once_with(account)

    finally:
        controller.shutdown()