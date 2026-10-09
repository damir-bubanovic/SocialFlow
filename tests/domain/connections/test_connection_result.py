import pytest
from dataclasses import FrozenInstanceError

from socialflow.domain.connections.connection_result import (
    ConnectionResult,
)
from socialflow.domain.connections.connection_status import (
    ConnectionStatus,
)


def test_connected_result_is_successful() -> None:
    result = ConnectionResult(
        status=ConnectionStatus.CONNECTED,
        message="Connection verified.",
    )

    assert result.is_connected is True
    assert result.message == "Connection verified."


@pytest.mark.parametrize(
    "status",
    [
        ConnectionStatus.INVALID_CREDENTIALS,
        ConnectionStatus.UNREACHABLE,
        ConnectionStatus.ERROR,
    ],
)
def test_failed_connection_result_is_not_connected(
    status: ConnectionStatus,
) -> None:
    result = ConnectionResult(status=status)

    assert result.is_connected is False


def test_connection_result_has_empty_message_by_default() -> None:
    result = ConnectionResult(
        status=ConnectionStatus.CONNECTED,
    )

    assert result.message == ""


def test_connection_result_is_immutable() -> None:
    result = ConnectionResult(
        status=ConnectionStatus.CONNECTED,
    )

    with pytest.raises(FrozenInstanceError):
        setattr(result, "message", "Modified")