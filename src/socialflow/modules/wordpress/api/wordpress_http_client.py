from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WordPressHttpResponse:
    """A minimal HTTP response from WordPress."""

    status_code: int


class WordPressHttpClient(ABC):
    """Contract for communicating with the WordPress REST API."""

    @abstractmethod
    def get_authenticated_user(
        self,
        site_url: str,
        username: str,
        application_password: str,
    ) -> WordPressHttpResponse:
        """Request the authenticated WordPress user."""