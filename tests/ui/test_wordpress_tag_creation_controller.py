from unittest.mock import Mock

import pytest

from socialflow.domain.account.account import Account
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag
from socialflow.infrastructure.wordpress.wordpress_tag_creation_plan import (
    WordPressTagCreationPlan,
)
from socialflow.ui.workers.wordpress_tag_creation_controller import (
    WordPressTagCreationController,
)


def make_controller():
    credentials = Mock()
    credentials.get.return_value = "secret"

    client = Mock()
    client.create_tag.return_value = WordPressTag(
        id=42,
        name="SocialFlow",
    )

    controller = WordPressTagCreationController(
        credential_store=credentials,
        tag_client=client,
    )

    account = Account(
        name="WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    plan = WordPressTagCreationPlan(
        missing_tags=(Tag("SocialFlow"),),
    )

    return controller, account, plan, client


def test_controller_emits_created_tags(qtbot):
    controller, account, plan, client = make_controller()
    results = []

    controller.tags_created.connect(results.append)

    with qtbot.waitSignals(
        [controller.tags_created, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(account, plan)

    assert len(results) == 1
    assert results[0][0].name == "SocialFlow"
    assert not controller.is_running
    client.create_tag.assert_called_once()


def test_controller_reports_creation_error(qtbot):
    controller, account, plan, client = make_controller()

    client.create_tag.side_effect = RuntimeError(
        "WordPress tag creation failed."
    )

    errors = []
    controller.error_occurred.connect(errors.append)

    with qtbot.waitSignals(
        [controller.error_occurred, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(account, plan)

    assert errors == ["WordPress tag creation failed."]
    assert not controller.is_running


def test_controller_can_start_again_after_completion(qtbot):
    controller, account, plan, client = make_controller()

    for _ in range(2):
        with qtbot.waitSignals(
            [controller.tags_created, controller.finished],
            timeout=3000,
            order="strict",
        ):
            controller.start(account, plan)

    assert client.create_tag.call_count == 2
    assert not controller.is_running


def test_controller_rejects_empty_plan():
    controller, account, _, client = make_controller()

    empty_plan = WordPressTagCreationPlan(missing_tags=())

    with pytest.raises(ValueError):
        controller.start(account, empty_plan)

    assert not controller.is_running
    client.create_tag.assert_not_called()


def test_controller_does_not_start_after_shutdown():
    controller, account, plan, client = make_controller()

    controller.shutdown()
    controller.start(account, plan)

    assert not controller.is_running
    client.create_tag.assert_not_called()

def test_repeated_shutdown_after_completion_is_safe(qtbot):
    controller, account, plan, client = make_controller()

    finished_count = []
    controller.finished.connect(lambda: finished_count.append(1))

    with qtbot.waitSignals(
        [controller.tags_created, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(account, plan)

    assert not controller.is_running
    assert len(finished_count) == 1

    controller.shutdown()
    controller.shutdown()

    assert not controller.is_running
    assert len(finished_count) == 1

    controller.start(account, plan)

    assert not controller.is_running
    assert len(finished_count) == 1
    client.create_tag.assert_called_once()

def test_shutdown_during_active_tag_creation(qtbot):
    from threading import Event, Thread

    controller, account, _, client = make_controller()

    plan = WordPressTagCreationPlan(
        missing_tags=(
            Tag("Python"),
            Tag("SocialFlow"),
        ),
    )

    request_started = Event()
    release_request = Event()
    interruption_observed = Event()

    finished_signals = []
    controller.finished.connect(
        lambda: finished_signals.append(True)
    )

    def create_tag(**kwargs):
        request_started.set()

        if not release_request.wait(timeout=5):
            raise TimeoutError(
                "Test request was not released."
            )

        return WordPressTag(
            id=42,
            name=kwargs["name"],
        )

    client.create_tag.side_effect = create_tag

    controller.start(account, plan)

    qtbot.waitUntil(
        request_started.is_set,
        timeout=3000,
    )

    assert controller.is_running

    active_thread = controller._thread
    assert active_thread is not None

    def release_after_interruption():
        try:
            for _ in range(500):
                if active_thread.isInterruptionRequested():
                    interruption_observed.set()
                    return

                if release_request.wait(timeout=0.01):
                    return
        finally:
            release_request.set()

    helper = Thread(
        target=release_after_interruption,
        daemon=True,
    )
    helper.start()

    try:
        controller.shutdown()
    finally:
        release_request.set()
        helper.join(timeout=5)

    assert not helper.is_alive()
    assert interruption_observed.is_set()

    assert not controller.is_running
    assert controller._thread is None
    assert controller._worker is None

    assert client.create_tag.call_count == 1
    assert (
        client.create_tag.call_args_list[0].kwargs["name"]
        == "Python"
    )

    qtbot.waitUntil(
        lambda: len(finished_signals) == 1,
        timeout=3000,
    )

    controller.shutdown()

    assert len(finished_signals) == 1

    controller.start(account, plan)

    assert not controller.is_running
    assert client.create_tag.call_count == 1

