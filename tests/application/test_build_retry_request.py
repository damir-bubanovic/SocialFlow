from socialflow.application.publishing.build_retry_request import (
    BuildRetryRequest,
)
from socialflow.application.publishing.publish_result import PublishResult
from socialflow.domain.account.account import Account
from socialflow.domain.language.language import Language
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.destination import PublishingDestination
from socialflow.domain.publishing.publish_request import PublishRequest


def create_request() -> PublishRequest:
    """Create a request targeting Facebook and WordPress."""
    post = Post(
        text="Hello from SocialFlow",
        language=Language.ENGLISH,
    )

    facebook = Account(
        name="Main Facebook",
        destination=PublishingDestination.FACEBOOK,
    )

    wordpress = Account(
        name="Main Website",
        destination=PublishingDestination.WORDPRESS,
    )

    return PublishRequest(
        post=post,
        accounts=(facebook, wordpress),
    )


def test_retry_request_contains_only_failed_accounts() -> None:
    request = create_request()
    facebook, wordpress = request.accounts

    results = (
        PublishResult(account=facebook, succeeded=True),
        PublishResult(
            account=wordpress,
            succeeded=False,
            error=RuntimeError("WordPress publishing failed."),
        ),
    )

    retry_request = BuildRetryRequest().execute(request, results)

    assert retry_request is not None
    assert retry_request.post is request.post
    assert retry_request.accounts == (wordpress,)


def test_retry_request_is_none_when_all_accounts_succeed() -> None:
    request = create_request()

    results = tuple(
        PublishResult(account=account, succeeded=True)
        for account in request.accounts
    )

    retry_request = BuildRetryRequest().execute(request, results)

    assert retry_request is None


def test_retry_request_contains_all_failed_accounts() -> None:
    request = create_request()

    results = tuple(
        PublishResult(
            account=account,
            succeeded=False,
            error=RuntimeError("Publishing failed."),
        )
        for account in request.accounts
    )

    retry_request = BuildRetryRequest().execute(request, results)

    assert retry_request is not None
    assert retry_request.accounts == request.accounts


def test_retry_request_preserves_original_account_order() -> None:
    request = create_request()
    facebook, wordpress = request.accounts

    results = (
        PublishResult(
            account=wordpress,
            succeeded=False,
            error=RuntimeError("WordPress failed."),
        ),
        PublishResult(
            account=facebook,
            succeeded=False,
            error=RuntimeError("Facebook failed."),
        ),
    )

    retry_request = BuildRetryRequest().execute(request, results)

    assert retry_request is not None
    assert retry_request.accounts == (facebook, wordpress)