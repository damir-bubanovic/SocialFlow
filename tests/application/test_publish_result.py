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