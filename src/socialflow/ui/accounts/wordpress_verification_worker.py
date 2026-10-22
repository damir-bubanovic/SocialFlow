
import logging

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


logger = logging.getLogger(__name__)


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
        # noinspection PyBroadException
        except Exception as error:
            logger.error(
                "Unexpected WordPress verification failure: %s",
                type(error).__name__,
            )
            self.failed.emit(
                "WordPress connection verification failed unexpectedly."
            )
            return

        self.finished.emit(result)
