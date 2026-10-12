from socialflow.application.publishing.publish_result import PublishResult
from socialflow.domain.publishing.publish_request import PublishRequest


class BuildRetryRequest:
    """Build a publishing request containing only failed accounts."""

    @staticmethod
    def execute(
            original_request: PublishRequest,
        results: tuple[PublishResult, ...],
    ) -> PublishRequest | None:
        """Return a retry request, or None if no accounts failed."""
        failed_accounts = {
            result.account
            for result in results
            if not result.succeeded
        }

        accounts_to_retry = tuple(
            account
            for account in original_request.accounts
            if account in failed_accounts
        )

        if not accounts_to_retry:
            return None

        return PublishRequest(
            post=original_request.post,
            accounts=accounts_to_retry,
        )