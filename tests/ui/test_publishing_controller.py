
from threading import Event
from unittest.mock import Mock

from socialflow.application.publishing.errors import PublishingError
from socialflow.application.publishing.publish_post import PublishPost
from socialflow.domain.publishing.publish_request import PublishRequest
from socialflow.ui.posts.publishing_controller import PublishingController


def create_request() -> PublishRequest:
    return PublishRequest(post=Mock(), accounts=())


def test_controller_returns_results(qtbot) -> None:
    service = Mock(spec=PublishPost)
    request = create_request()
    results = (object(),)
    service.execute.return_value = results

    controller = PublishingController(service)
    listener = Mock()
    controller.result_ready.connect(listener)

    with qtbot.waitSignals(
        [controller.result_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(request)

    service.execute.assert_called_once()
    args, kwargs = service.execute.call_args

    assert args == (request,)
    assert callable(kwargs["on_progress"])
    listener.assert_called_once_with(results)
    assert not controller.is_running


def test_controller_reports_publishing_error(qtbot) -> None:
    service = Mock(spec=PublishPost)
    service.execute.side_effect = PublishingError(
        "Sensitive internal detail"
    )

    controller = PublishingController(service)
    listener = Mock()
    controller.error_occurred.connect(listener)

    with qtbot.waitSignals(
        [controller.error_occurred, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(create_request())

    listener.assert_called_once_with(
        "Publishing could not be completed."
    )
    assert not controller.is_running


def test_controller_prevents_concurrent_publishing(qtbot) -> None:
    service = Mock(spec=PublishPost)
    started = Event()
    release = Event()

    def execute(_request, *, on_progress=None):
        assert callable(on_progress)
        started.set()
        if not release.wait(timeout=2):
            raise PublishingError("Worker was not released.")
        return ()

    service.execute.side_effect = execute

    controller = PublishingController(service)

    try:
        controller.start(create_request())
        assert started.wait(timeout=2)
        assert controller.is_running

        controller.start(create_request())
        assert service.execute.call_count == 1

    finally:
        release.set()
        controller.shutdown()

    qtbot.waitUntil(
        lambda: not controller.is_running,
        timeout=3000,
    )
    assert service.execute.call_count == 1

def test_controller_forwards_publishing_progress(qtbot) -> None:
    """Forward individual publishing results before completion."""
    service = Mock(spec=PublishPost)
    request = create_request()

    first_result = object()
    second_result = object()
    results = (first_result, second_result)

    def execute(_request, *, on_progress):
        assert _request is request

        for result in results:
            on_progress(result)

        return results

    service.execute.side_effect = execute

    controller = PublishingController(service)
    progress_listener = Mock()

    controller.progress.connect(progress_listener)

    with qtbot.waitSignals(
        [controller.progress, controller.progress, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(request)

    assert progress_listener.call_count == 2
    assert progress_listener.call_args_list[0].args == (first_result,)
    assert progress_listener.call_args_list[1].args == (second_result,)
    assert not controller.is_running

def test_shutdown_during_active_publishing(
    qtbot,
    monkeypatch,
) -> None:
    from threading import Thread

    from PySide6.QtCore import QThread

    import socialflow.ui.posts.publishing_controller as controller_module

    service = Mock(spec=PublishPost)
    request = create_request()

    publishing_started = Event()
    release_publishing = Event()
    publishing_completed = Event()
    shutdown_wait_started = Event()

    results = (object(),)

    class ObservedThread(QThread):
        def wait(self, *args, **kwargs):
            shutdown_wait_started.set()
            return super().wait(*args, **kwargs)

    monkeypatch.setattr(
        controller_module,
        "QThread",
        ObservedThread,
    )

    def execute(_request, *, on_progress=None):
        assert _request is request
        assert callable(on_progress)
        publishing_started.set()

        if not release_publishing.wait(timeout=5):
            raise TimeoutError(
                "Publishing was not released."
            )

        publishing_completed.set()
        return results

    service.execute.side_effect = execute

    controller = PublishingController(service)

    finished_listener = Mock()
    result_listener = Mock()

    controller.finished.connect(finished_listener)
    controller.result_ready.connect(result_listener)

    controller.start(request)

    qtbot.waitUntil(
        publishing_started.is_set,
        timeout=3000,
    )

    assert controller.is_running

    active_thread = controller._thread
    assert active_thread is not None

    observations = []

    def release_after_shutdown_begins():
        try:
            if not shutdown_wait_started.wait(timeout=5):
                observations.append(
                    "Shutdown did not enter thread.wait()."
                )
                return

            observations.append(
                (
                    publishing_completed.is_set(),
                    active_thread.isRunning(),
                )
            )
        finally:
            release_publishing.set()

    helper = Thread(
        target=release_after_shutdown_begins,
        daemon=True,
    )

    try:
        helper.start()

        controller.shutdown()

    finally:
        release_publishing.set()
        helper.join(timeout=5)

    assert not helper.is_alive()
    assert observations == [(False, True)]

    assert shutdown_wait_started.is_set()
    assert publishing_completed.is_set()
    assert not active_thread.isRunning()

    qtbot.waitUntil(
        lambda: not controller.is_running,
        timeout=3000,
    )

    assert controller._thread is None
    assert controller._worker is None

    qtbot.waitUntil(
        lambda: finished_listener.call_count == 1,
        timeout=3000,
    )

    controller.shutdown()

    assert finished_listener.call_count == 1
    assert controller._shutting_down is True

    controller.start(create_request())

    assert not controller.is_running
    assert controller._thread is None
    assert controller._worker is None

    assert finished_listener.call_count == 1
    service.execute.assert_called_once()

def test_controller_can_start_again_after_completion(qtbot) -> None:
    service = Mock(spec=PublishPost)
    service.execute.return_value = ()

    controller = PublishingController(service)

    finished_listener = Mock()
    result_listener = Mock()

    controller.finished.connect(finished_listener)
    controller.result_ready.connect(result_listener)

    first_request = create_request()
    second_request = create_request()

    with qtbot.waitSignals(
        [controller.result_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(first_request)

    assert not controller.is_running
    assert controller._thread is None
    assert controller._worker is None

    with qtbot.waitSignals(
        [controller.result_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(second_request)

    assert not controller.is_running
    assert controller._thread is None
    assert controller._worker is None

    assert service.execute.call_count == 2
    assert service.execute.call_args_list[0].args == (
        first_request,
    )
    assert service.execute.call_args_list[1].args == (
        second_request,
    )

    assert finished_listener.call_count == 2
    assert result_listener.call_count == 2

def test_controller_rejects_start_after_shutdown() -> None:
    service = Mock(spec=PublishPost)
    service.execute.return_value = ()

    controller = PublishingController(service)

    controller.shutdown()

    controller.start(create_request())

    assert not controller.is_running
    assert controller._thread is None
    assert controller._worker is None

    service.execute.assert_not_called()