from socialflow.application.publishing.error_classifier import ErrorCategory
from socialflow.application.publishing.publish_result import PublishResult
from socialflow.domain.account.account import Account
from socialflow.domain.publishing.destination import PublishingDestination


def test_publish_result_represents_success() -> None:
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    result = PublishResult(
        account=account,
        succeeded=True,
    )

    assert result.account is account
    assert result.succeeded
    assert result.error is None


def test_publish_result_represents_failure() -> None:
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    error = RuntimeError("Publishing failed.")

    result = PublishResult(
        account=account,
        succeeded=False,
        error=error,
    )

    assert result.account is account
    assert not result.succeeded
    assert result.error is error


def test_successful_result_has_no_error_category() -> None:
    """Successful publishing must not have an error category."""
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    result = PublishResult(
        account=account,
        succeeded=True,
    )

    assert result.error_category is None


def test_connection_failure_has_transient_category() -> None:
    """Connection failures must be classified as transient."""
    account = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    result = PublishResult(
        account=account,
        succeeded=False,
        error=ConnectionError("Connection lost."),
    )

    assert result.error_category is ErrorCategory.TRANSIENT


def test_unexpected_failure_has_unknown_category() -> None:
    """Unexpected exceptions must have an unknown classification."""
    account = Account(
        name="Main WordPress",
        destination=PublishingDestination.WORDPRESS,
    )

    result = PublishResult(
        account=account,
        succeeded=False,
        error=RuntimeError("Unexpected failure."),
    )

    assert result.error_category is ErrorCategory.UNKNOWN
