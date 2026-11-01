from abc import ABC, abstractmethod


class CredentialStore(ABC):
    """Contract for securely storing platform credentials."""

    @abstractmethod
    def save(self, key: str, secret: str) -> None:
        """Store or replace a secret."""

    @abstractmethod
    def get(self, key: str) -> str | None:
        """Retrieve a secret, or None if it does not exist."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a stored secret."""