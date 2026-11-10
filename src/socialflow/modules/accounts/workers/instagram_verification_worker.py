import logging

from PySide6.QtCore import QObject, Signal, Slot

from socialflow.modules.accounts.models.account import Account
from socialflow.modules.accounts.models.connection_result import (
    ConnectionResult,
)
from socialflow.modules.accounts.services.connection_verifier import (
    ConnectionVerifier,
)
from socialflow.modules.accounts.services.credential_errors import (
    CredentialStorageError,
)


logger = logging.getLogger(__name__)


class InstagramVerificationWorker(QObject):
    """Run Instagram connection verification outside the UI thread."""

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
                "Could not access stored Instagram credentials."
            )
            return
        except (RuntimeError, ValueError, TypeError, OSError) as error:
            logger.error(
                "Unexpected Instagram verification failure: %s",
                type(error).__name__,
            )
            self.failed.emit(
                "Instagram connection verification failed unexpectedly."
            )
            return

        self.finished.emit(result)