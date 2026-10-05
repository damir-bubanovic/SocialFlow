from dataclasses import dataclass
from datetime import datetime

from socialflow.domain.account.account import Account
from socialflow.domain.post.post import Post


@dataclass(frozen=True)
class Publication:
    """A successfully published post for one account."""

    account: Account
    post: Post
    published_at: datetime