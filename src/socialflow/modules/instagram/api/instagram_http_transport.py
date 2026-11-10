from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class InstagramHttpResponse:
    """Raw HTTP response from the Instagram API."""

    status_code: int
    body: bytes


class InstagramHttpTransport(ABC):
    """Low-level HTTP transport contract for Instagram."""

    @abstractmethod
    def get(
        self,
        url: str,
        headers: Mapping[str, str],
        timeout: float,
    ) -> InstagramHttpResponse:
        """Perform an HTTPS GET request without following redirects."""

    @abstractmethod
    def post(
        self,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
        timeout: float,
    ) -> InstagramHttpResponse:
        """Perform an HTTPS POST request without following redirects."""