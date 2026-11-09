from socialflow.modules.posts.components.publish_status import PublishStatus
from socialflow.modules.posts.services.publish_result import PublishResult
from socialflow.modules.accounts.models.account import Account
from socialflow.core.destination import PublishingDestination


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
        "Main Website — Failed: "
        "Publishing failed. Please check the details."
    )
    assert status.property("status") == "error"

from socialflow.modules.posts.services.errors import (
    PublisherNotConfiguredError,
)

def test_publish_status_shows_persistence_warning(qtbot) -> None:
    """Successful publishing with failed history storage shows a warning."""
    status = PublishStatus()
    qtbot.addWidget(status)

    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    result = PublishResult(
        account=account,
        succeeded=True,
        persistence_error=OSError(
            "Sensitive local filesystem information."
        ),
    )

    status.show_results((result,))

    assert status.text() == (
        "Main Facebook — Published — Warning: local publication "
        "history could not be saved."
    )
    assert status.property("status") == "warning"

    # Raw exception details must not be displayed.
    assert "Sensitive local filesystem information" not in status.text()


def test_publish_status_shows_mixed_success_and_persistence_warning(
    qtbot,
) -> None:
    """A history warning does not turn successful publishing into failure."""
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
            persistence_error=OSError("History storage failed."),
        ),
        PublishResult(
            account=wordpress_account,
            succeeded=True,
        ),
    )

    status.show_results(results)

    assert status.text() == (
        "Main Facebook — Published — Warning: local publication "
        "history could not be saved.\n"
        "Main Website — Published"
    )
    assert status.property("status") == "warning"


def test_publish_status_prioritizes_remote_failure_over_warning(
    qtbot,
) -> None:
    """A remote publishing failure takes precedence over history warnings."""
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
            persistence_error=OSError("History storage failed."),
        ),
        PublishResult(
            account=wordpress_account,
            succeeded=False,
            error=RuntimeError("Publishing failed."),
        ),
    )

    status.show_results(results)

    assert status.text() == (
        "Main Facebook — Published — Warning: local publication "
        "history could not be saved.\n"
        "Main Website — Failed: "
        "Publishing failed. Please check the details."
    )
    assert status.property("status") == "error"

def test_publish_status_displays_publishing_error(qtbot) -> None:
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    status = PublishStatus()
    qtbot.addWidget(status)

    result = PublishResult(
        account=account,
        succeeded=False,
        error=PublisherNotConfiguredError(
            "External publishing is not configured."
        ),
    )

    status.show_results((result,))

    assert status.text() == (
        "Main Facebook — Failed: "
        "Publishing configuration needs attention."
    )
    assert status.property("status") == "error"