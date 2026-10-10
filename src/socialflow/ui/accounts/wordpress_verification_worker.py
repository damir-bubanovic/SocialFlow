
from PySide6.QtCore import QObject, Signal, Slot

from socialflow.application.connections.connection_verifier import (
    ConnectionVerifier,
)
from socialflow.application.credentials.errors import (
    CredentialStorageError,
)
from socialflow.domain.account.account import Account
from socialflow.domain.connections.connection_result import (
    ConnectionResult,
)


class WordPressVerificationWorker(QObject):
    """Run WordPress connection verification outside the UI thread."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        verifier: ConnectionVerifier,
        account: Account,
    ) -> None:
        super().__init__()

        self._verifier = verifier
        self._account = account

    @Slot()
    def run(self) -> None:
        """Verify the account and emit the outcome."""
        try:
            result: ConnectionResult = self._verifier.verify(
                self._account
            )
        except CredentialStorageError:
            self.failed.emit(
                "Could not access stored WordPress credentials."
            )
            return

        self.finished.emit(result)
