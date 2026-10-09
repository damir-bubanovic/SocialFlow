from abc import ABC, abstractmethod

from socialflow.domain.account.account import Account
from socialflow.domain.connections.connection_result import (
    ConnectionResult,
)


class ConnectionVerifier(ABC):
    """Contract for verifying publishing account connections."""

    @abstractmethod
    def verify(self, account: Account) -> ConnectionResult:
        """Return the result of verifying an account connection."""