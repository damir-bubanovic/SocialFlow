
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