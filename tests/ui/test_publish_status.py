from socialflow.ui.posts.publish_status import PublishStatus
from socialflow.application.publishing.publish_result import PublishResult
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination


def test_publish_status_is_empty_by_default(qtbot) -> None:
    status = PublishStatus()
    qtbot.addWidget(status)

    assert status.text() == ""
    assert status.property("status") == ""


def test_publish_status_can_show_success(qtbot) -> None:
    status = PublishStatus()
    qtbot.addWidget(status)

    status.show_success()

    assert status.text() == "Publish request completed."
    assert status.property("status") == "success"


def test_publish_status_can_be_cleared(qtbot) -> None:
    status = PublishStatus()
    qtbot.addWidget(status)

    status.show_success()
    status.clear_status()

    assert status.text() == ""
    assert status.property("status") == ""

def test_publish_status_can_show_error(qtbot) -> None:
    status = PublishStatus()
    qtbot.addWidget(status)

    status.show_error()

    assert status.text() == "Publish request failed."
    assert status.property("status") == "error"

def test_publish_status_can_show_successful_results(qtbot) -> None:
    status = PublishStatus()
    qtbot.addWidget(status)

    facebook_account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    wordpress_account = Account(
        name="Main Website",
        destination=PublishingDestination.WORDPRESS,
    )

    results = (
        PublishResult(
            account=facebook_account,
            succeeded=True,
        ),
        PublishResult(
            account=wordpress_account,
            succeeded=True,
        ),
    )

    status.show_results(results)

    assert status.text() == (
        "Main Facebook — Published\n"
        "Main Website — Published"
    )
    assert status.property("status") == "success"


def test_publish_status_can_show_partial_failure(qtbot) -> None:
    status = PublishStatus()
    qtbot.addWidget(status)

    facebook_account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    wordpress_account = Account(
        name="Main Website",
        destination=PublishingDestination.WORDPRESS,
    )

    results = (
        PublishResult(
            account=facebook_account,
            succeeded=True,
        ),
        PublishResult(
            account=wordpress_account,
            succeeded=False,
            error=RuntimeError("Publishing failed."),
        ),
    )

    status.show_results(results)

    assert status.text() == (
        "Main Facebook — Published\n"
        "Main Website — Failed"
    )
    assert status.property("status") == "error"