
import logging

from PySide6.QtCore import QObject, Signal, Slot

from socialflow.modules.facebook.api.facebook_api_error import (
    FacebookApiError,
)
from socialflow.modules.facebook.api.facebook_page_discovery_service import (
    FacebookPageDiscoveryService,
)
from socialflow.modules.facebook.models.discovered_facebook_page import (
    DiscoveredFacebookPage,
)


logger = logging.getLogger(__name__)


class FacebookPageDiscoveryWorker(QObject):
    """Discover Facebook Pages outside the UI thread."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        discovery_service: FacebookPageDiscoveryService,
        user_access_token: str,
    ) -> None:
        super().__init__()

        self._discovery_service = discovery_service
        self._user_access_token = user_access_token

    @Slot()
    def run(self) -> None:
        """Discover Pages and emit a safe result or error."""
        try:
            pages: list[DiscoveredFacebookPage] = (
                self._discovery_service.discover(
                    self._user_access_token
                )
            )
        except FacebookApiError as error:
            logger.warning(
                "Facebook Page discovery failed: %s",
                str(error),
            )
            self.failed.emit(
                "Could not discover Facebook Pages. "
                "Check your Facebook access token and permissions."
            )
            return
        # noinspection PyBroadException
        except Exception as error:
            logger.error(
                "Unexpected Facebook Page discovery failure: %s",
                type(error).__name__,
            )
            self.failed.emit(
                "Facebook Page discovery failed unexpectedly."
            )
            return
        finally:
            # Do not retain the user token after discovery finishes.
            self._user_access_token = ""

        self.finished.emit(pages)
