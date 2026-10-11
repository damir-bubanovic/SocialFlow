
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

    service.execute.assert_called_once_with(request)
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

    def execute(_request):
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
