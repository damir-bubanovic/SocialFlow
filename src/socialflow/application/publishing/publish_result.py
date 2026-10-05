from dataclasses import dataclass

from socialflow.domain.account.account import Account


@dataclass(frozen=True)
class PublishResult:
    """Result of a publishing attempt for one account."""

    account: Account
    succeeded: bool
    error: Exception | None = None