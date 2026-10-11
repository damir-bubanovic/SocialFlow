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

    service.execute.assert_called_once_with(request)
    assert signal.args == [results]


def test_worker_emits_safe_failure_message(qtbot) -> None:
    service = Mock(spec=PublishPost)
    request = PublishRequest(post=Mock(), accounts=())
    service.execute.side_effect = PublishingError("Sensitive internal detail")
    worker = PublishingWorker(service, request)

    with qtbot.waitSignal(worker.failed, timeout=1000) as signal:
        worker.run()

    service.execute.assert_called_once_with(request)
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