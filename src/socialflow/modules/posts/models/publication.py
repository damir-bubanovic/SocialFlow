from dataclasses import dataclass
from datetime import datetime

from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.post import Post
from socialflow.modules.posts.models.publication_id import PublicationId


@dataclass(frozen=True)
class Publication:
    """A successfully published post for one account."""

    id: PublicationId
    account: Account
    post: Post
    published_at: datetime