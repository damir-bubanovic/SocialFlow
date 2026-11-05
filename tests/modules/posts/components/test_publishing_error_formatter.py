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
from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
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

@pytest.mark.parametrize(
    ("code", "expected_message"),
    [
        (
            190,
            "Facebook access token expired or invalid. "
            "Reconnect the Facebook Page.",
        ),
        (
            200,
            "Facebook Page permissions are insufficient. "
            "Check the Page access permissions.",
        ),
        (
            10,
            "Facebook Page permissions are insufficient. "
            "Check the Page access permissions.",
        ),
        (
            100,
            "Publishing configuration needs attention.",
        ),
    ],
)
def test_formats_facebook_api_errors(
    code: int,
    expected_message: str,
) -> None:
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    error = FacebookApiError(
        message="Sensitive API diagnostic: secret-token-123",
        status_code=400,
        code=code,
        is_transient=False,
    )

    result = PublishResult(
        account=account,
        succeeded=False,
        error=error,
    )

    formatted = PublishingErrorFormatter.format(result)

    assert formatted == expected_message
    assert "secret-token-123" not in formatted