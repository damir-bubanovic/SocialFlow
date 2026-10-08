from dataclasses import dataclass
from datetime import datetime

from socialflow.domain.account.account import Account
from socialflow.domain.post.post import Post
from socialflow.domain.publishing.publication_id import PublicationId


@dataclass(frozen=True)
class Publication:
    """A successfully published post for one account."""

    id: PublicationId
    account: Account
    post: Post
    published_at: datetime