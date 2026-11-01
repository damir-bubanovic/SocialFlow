from dataclasses import dataclass

from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.post import Post


@dataclass(frozen=True, slots=True)
class PublishRequest:
    """A post together with its selected publishing accounts."""

    post: Post
    accounts: tuple[Account, ...]