
"""Contract for preparing and creating remote tags."""

from abc import ABC, abstractmethod

from socialflow.modules.accounts.models.account import Account
from socialflow.modules.posts.models.remote_tag import RemoteTag
from socialflow.modules.posts.models.tag import Tag


class RemoteTagCreationService(ABC):
    """Prepare missing tags and create explicitly approved tags."""

    @abstractmethod
    def prepare_creation(
        self,
        account: Account,
        selected_tags: tuple[Tag, ...],
    ) -> tuple[Tag, ...]:
        """Return missing tags after checking remote state.

        Implementations must reject ambiguous existing matches
        and must not create any tags during preparation.
        """

    @abstractmethod
    def create_approved_tags(
        self,
        account: Account,
        approved_tags: tuple[Tag, ...],
    ) -> tuple[RemoteTag, ...]:
        """Create approved tags in order and return the results.

        Implementations must stop on the first failure.
        """
