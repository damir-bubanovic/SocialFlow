from unittest.mock import Mock
from threading import Event

from socialflow.domain.account.account import Account
from socialflow.domain.connections.wordpress_connection_config import (
    WordPressConnectionConfig,
)
from socialflow.domain.post.tag import Tag
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag
from socialflow.ui.workers.wordpress_tag_preparation_controller import (
    WordPressTagPreparationController,
)


def make_controller():
    credentials = Mock()
    credentials.get.return_value = "secret"

    tag_client = Mock()
    tag_client.list_tags.return_value = (
        WordPressTag(id=12, name="Python"),
    )

    controller = WordPressTagPreparationController(
        credential_store=credentials,
        tag_client=tag_client,
    )

    account = Account(
        name="WordPress",
        destination=PublishingDestination.WORDPRESS,
        wordpress_config=WordPressConnectionConfig(
            site_url="https://example.com",
            username="admin",
        ),
    )

    return controller, account, tag_client


def test_controller_emits_missing_tag_plan(qtbot):
    controller, account, client = make_controller()
    plans = []

    controller.plan_ready.connect(plans.append)

    with qtbot.waitSignals(
        [controller.plan_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(
            account,
            (
                Tag("Python"),
                Tag("SocialFlow"),
            ),
        )

    assert len(plans) == 1
    assert plans[0].tag_names == ("SocialFlow",)
    assert not controller.is_running
    client.create_tag.assert_not_called()


def test_controller_emits_plan_without_missing_tags(qtbot):
    controller, account, client = make_controller()
    plans = []

    controller.plan_ready.connect(plans.append)

    with qtbot.waitSignals(
        [controller.plan_ready, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(account, (Tag("Python"),))

    assert len(plans) == 1
    assert plans[0].requires_confirmation is False
    assert not controller.is_running
    client.create_tag.assert_not_called()


def test_controller_reports_worker_error(qtbot):
    controller, account, client = make_controller()

    client.list_tags.side_effect = RuntimeError(
        "WordPress tag lookup failed."
    )

    errors = []
    controller.error_occurred.connect(errors.append)

    with qtbot.waitSignals(
        [controller.error_occurred, controller.finished],
        timeout=3000,
        order="strict",
    ):
        controller.start(account, (Tag("Python"),))

    assert errors == ["WordPress tag lookup failed."]
    assert not controller.is_running
    client.create_tag.assert_not_called()


def test_controller_can_start_again_after_completion(qtbot):
    controller, account, client = make_controller()

    for _ in range(2):
        with qtbot.waitSignals(
            [controller.plan_ready, controller.finished],
            timeout=3000,
            order="strict",
        ):
            controller.start(account, (Tag("Python"),))

    assert client.list_tags.call_count == 2
    assert not controller.is_running


def test_controller_does_not_start_after_shutdown():
    controller, account, client = make_controller()

    controller.shutdown()
    controller.start(account, (Tag("Python"),))

    assert not controller.is_running
    client.list_tags.assert_not_called()


def test_shutdown_suppresses_queued_preparation_plan(qtbot):
    """A queued tag plan must not be delivered after shutdown."""
    controller, account, client = make_controller()

    lookup_complete = Event()
    original_list_tags = client.list_tags.return_value

    def list_tags(*args, **kwargs):
        _ = args, kwargs
        lookup_complete.set()
        return original_list_tags

    client.list_tags.side_effect = list_tags

    plan_listener = Mock()
    error_listener = Mock()

    controller.plan_ready.connect(plan_listener)
    controller.error_occurred.connect(error_listener)

    try:
        controller.start(account, (Tag("SocialFlow"),))

        # Wait for the worker without processing Qt UI events.
        assert lookup_complete.wait(timeout=3)

        controller.shutdown()

        assert not controller.is_running

        # Deliver any notifications queued before shutdown.
        qtbot.wait(100)

        plan_listener.assert_not_called()
        error_listener.assert_not_called()
    finally:
        controller.shutdown()


def test_shutdown_suppresses_queued_preparation_error(qtbot):
    """A queued worker error must not be delivered after shutdown."""
    controller, account, client = make_controller()

    lookup_complete = Event()

    def list_tags(*args, **kwargs):
        _ = args, kwargs
        lookup_complete.set()
        raise RuntimeError("Simulated WordPress lookup failure")

    client.list_tags.side_effect = list_tags

    plan_listener = Mock()
    error_listener = Mock()

    controller.plan_ready.connect(plan_listener)
    controller.error_occurred.connect(error_listener)

    try:
        controller.start(account, (Tag("Python"),))

        # Wait without pumping Qt events.
        assert lookup_complete.wait(timeout=3)

        controller.shutdown()

        assert not controller.is_running

        qtbot.wait(100)

        plan_listener.assert_not_called()
        error_listener.assert_not_called()
    finally:
        controller.shutdown()


def test_normal_preparation_forwards_plan_before_completion(qtbot):
    """Normal preparation delivers its plan before the completion signal."""
    controller, account, client = make_controller()

    events = []

    controller.plan_ready.connect(
        lambda plan: events.append(("plan", plan))
    )
    controller.error_occurred.connect(
        lambda message: events.append(("error", message))
    )
    controller.finished.connect(
        lambda: events.append(("finished", None))
    )

    try:
        with qtbot.waitSignals(
            [controller.plan_ready, controller.finished],
            timeout=3000,
            order="strict",
        ):
            controller.start(account, (Tag("SocialFlow"),))

        assert len(events) == 2
        assert events[0][0] == "plan"
        assert events[1] == ("finished", None)

        received_plan = events[0][1]
        assert received_plan.missing_tags == (Tag("SocialFlow"),)

        assert not controller.is_running
        client.list_tags.assert_called_once()
    finally:
        controller.shutdown()