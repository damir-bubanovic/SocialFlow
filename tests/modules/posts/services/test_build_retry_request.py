from socialflow.modules.posts.services.build_retry_request import (
    BuildRetryRequest,
)
from socialflow.modules.posts.services.publish_result import PublishResult
from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.language import Language
from socialflow.modules.posts.models.post import Post
from socialflow.core.destination import PublishingDestination
from socialflow.modules.posts.models.publish_request import PublishRequest


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

def test_retry_request_ignores_successful_publish_with_persistence_error() -> None:
    """A local history failure must not trigger duplicate remote publishing."""
    request = create_request()
    facebook, wordpress = request.accounts

    results = (
        PublishResult(
            account=facebook,
            succeeded=True,
            persistence_error=OSError("History storage failed."),
        ),
        PublishResult(
            account=wordpress,
            succeeded=True,
        ),
    )

    retry_request = BuildRetryRequest().execute(request, results)

    assert retry_request is None


def test_retry_request_excludes_persistence_warning_from_mixed_results() -> None:
    """Only genuine remote publishing failures are eligible for retry."""
    request = create_request()
    facebook, wordpress = request.accounts

    results = (
        PublishResult(
            account=facebook,
            succeeded=True,
            persistence_error=OSError("History storage failed."),
        ),
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