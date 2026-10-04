from dataclasses import dataclass

from socialflow.domain.account.account import Account
from socialflow.domain.post.post import Post


@dataclass(frozen=True, slots=True)
class PublishRequest:
    """A post together with its selected publishing accounts."""

    post: Post
    accounts: tuple[Account, ...]