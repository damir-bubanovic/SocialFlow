from abc import ABC, abstractmethod

from socialflow.domain.account.account import Account
from socialflow.domain.post.tag import Tag


class TagProvider(ABC):
    """Contract for retrieving and creating tags for an account."""

    @abstractmethod
    def list_tags(self, account: Account) -> tuple[Tag, ...]:
        """Return the tags available for an account."""

    @abstractmethod
    def create_tag(self, account: Account, tag: Tag) -> Tag:
        """Create a tag for an account and return it."""