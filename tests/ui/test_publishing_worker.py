"""Tests for the Qt publishing worker's completion signals."""

from unittest.mock import Mock

from socialflow.application.publishing.publish_post import PublishPost
from socialflow.domain.publishing.publish_request import PublishRequest
from socialflow.ui.posts.publishing_worker import PublishingWorker
from socialflow.application.publishing.errors import PublishingError


def test_worker_emits_publish_results(qtbot) -> None:
    service = Mock(spec=PublishPost)
    request = PublishRequest(post=Mock(), accounts=())
    results = (object(),)
    service.execute.return_value = results
    worker = PublishingWorker(service, request)

    with qtbot.waitSignal(worker.finished, timeout=1000) as signal:
        worker.run()

    service.execute.assert_called_once_with(
        request,
        on_progress=worker.progress.emit,
    )
    assert signal.args == [results]


def test_worker_emits_safe_failure_message(qtbot) -> None:
    service = Mock(spec=PublishPost)
    request = PublishRequest(post=Mock(), accounts=())
    service.execute.side_effect = PublishingError("Sensitive internal detail")
    worker = PublishingWorker(service, request)

    with qtbot.waitSignal(worker.failed, timeout=1000) as signal:
        worker.run()

    service.execute.assert_called_once_with(
        request,
        on_progress=worker.progress.emit,
    )
    assert signal.args == ["Publishing could not be completed."]

def test_worker_handles_missing_image_preparation(qtbot) -> None:
    from socialflow.application.publishing.errors import (
        ImagePreparationNotConfiguredError,
    )

    service = Mock(spec=PublishPost)
    request = PublishRequest(post=Mock(), accounts=())

    service.execute.side_effect = ImagePreparationNotConfiguredError(
        "Image preparation is not configured."
    )

    worker = PublishingWorker(service, request)

    with qtbot.waitSignal(worker.failed, timeout=1000) as signal:
        worker.run()

    assert signal.args == ["Publishing could not be completed."]

def test_worker_emits_progress_for_each_account(qtbot) -> None:
    """Forward each account result through the progress signal."""
    service = Mock(spec=PublishPost)
    request = PublishRequest(post=Mock(), accounts=())

    first_result = object()
    second_result = object()
    results = (first_result, second_result)

    def execute(_request, *, on_progress):
        assert _request is request

        for result in results:
            on_progress(result)

        return results

    service.execute.side_effect = execute

    worker = PublishingWorker(service, request)
    progress_listener = Mock()

    worker.progress.connect(progress_listener)

    with qtbot.waitSignal(worker.finished, timeout=1000) as signal:
        worker.run()

    assert signal.args == [results]
    assert progress_listener.call_count == 2
    assert progress_listener.call_args_list[0].args == (first_result,)
    assert progress_listener.call_args_list[1].args == (second_result,)

def test_worker_handles_unexpected_exception(qtbot) -> None:
    service = Mock(spec=PublishPost)
    request = PublishRequest(post=Mock(), accounts=())

    service.execute.side_effect = RuntimeError(
        "Sensitive unexpected failure"
    )

    worker = PublishingWorker(service, request)

    finished_listener = Mock()
    worker.finished.connect(finished_listener)

    with qtbot.waitSignal(worker.failed, timeout=1000) as signal:
        worker.run()

    service.execute.assert_called_once_with(
        request,
        on_progress=worker.progress.emit,
    )

    assert signal.args == ["Publishing could not be completed."]
    finished_listener.assert_not_called()

def test_worker_preserves_progress_before_unexpected_failure(qtbot) -> None:
    service = Mock(spec=PublishPost)
    request = PublishRequest(post=Mock(), accounts=())

    def execute(_request, *, on_progress=None):
        assert _request is request
        assert callable(on_progress)

        on_progress("Publishing started")

        raise RuntimeError("Unexpected publishing failure")

    service.execute.side_effect = execute

    worker = PublishingWorker(service, request)

    progress_listener = Mock()
    finished_listener = Mock()

    worker.progress.connect(progress_listener)
    worker.finished.connect(finished_listener)

    with qtbot.waitSignal(worker.failed, timeout=1000) as signal:
        worker.run()

    progress_listener.assert_called_once_with("Publishing started")
    finished_listener.assert_not_called()

    assert signal.args == ["Publishing could not be completed."]
    service.execute.assert_called_once()