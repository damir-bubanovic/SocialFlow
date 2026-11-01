import pytest

from socialflow.modules.posts.services.errors import (
    PublisherNotConfiguredError,
)
from socialflow.modules.posts.services.publish_result import PublishResult
from socialflow.modules.accounts.models.account import Account
from socialflow.core.destination import PublishingDestination
from socialflow.modules.posts.components.publishing_error_formatter import (
    PublishingErrorFormatter,
)


@pytest.mark.parametrize(
    ("error", "expected_message"),
    [
        (
            ConnectionError("Connection lost."),
            "Connection problem. Check your connection before retrying.",
        ),
        (
            TimeoutError("Request timed out."),
            "Connection problem. Check your connection before retrying.",
        ),
        (
            PublisherNotConfiguredError("Missing publisher."),
            "Publishing configuration needs attention.",
        ),
        (
            RuntimeError("Internal diagnostic information."),
            "Publishing failed. Please check the details.",
        ),
    ],
)
def test_formats_publishing_errors(
    error: Exception,
    expected_message: str,
) -> None:
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    result = PublishResult(
        account=account,
        succeeded=False,
        error=error,
    )

    assert PublishingErrorFormatter.format(result) == expected_message