from abc import ABC, abstractmethod

from socialflow.domain.account.account import Account


class AccountRepository(ABC):
    """Contract for storing and retrieving publishing accounts."""

    @abstractmethod
    def all(self) -> tuple[Account, ...]:
        """Return all configured accounts."""

    @abstractmethod
    def add(self, account: Account) -> None:
        """Store an account."""