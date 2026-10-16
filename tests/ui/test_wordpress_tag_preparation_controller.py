from unittest.mock import Mock

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