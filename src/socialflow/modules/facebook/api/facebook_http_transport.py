
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class FacebookHttpResponse:
    """Raw HTTP response from the Facebook Graph API."""

    status_code: int
    body: bytes


class FacebookHttpTransport(ABC):
    """Low-level HTTP transport contract for Facebook."""

    @abstractmethod
    def get(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> FacebookHttpResponse:
        """Perform an HTTPS GET request without following redirects."""
