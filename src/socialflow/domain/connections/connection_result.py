from dataclasses import dataclass

from socialflow.domain.connections.connection_status import (
    ConnectionStatus,
)


@dataclass(frozen=True, slots=True)
class ConnectionResult:
    """Result of verifying a publishing platform connection."""

    status: ConnectionStatus
    message: str = ""

    @property
    def is_connected(self) -> bool:
        """Return whether the connection was verified successfully."""
        return self.status == ConnectionStatus.CONNECTED