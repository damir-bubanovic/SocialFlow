from abc import ABC, abstractmethod


class WordPressPostClient(ABC):
    """Transport contract for creating WordPress posts."""

    @abstractmethod
    def create_post(
        self,
        site_url: str,
        username: str,
        application_password: str,
        content: str,
    ) -> int:
        """Return the HTTP status code from the create-post request."""