from enum import Enum


class ConnectionStatus(str, Enum):
    """Possible outcomes of a platform connection check."""

    CONNECTED = "connected"
    INVALID_CREDENTIALS = "invalid_credentials"
    UNREACHABLE = "unreachable"
    ERROR = "error"