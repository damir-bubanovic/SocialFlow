import keyring
from keyring.errors import PasswordDeleteError

from socialflow.application.credentials.credential_store import (
    CredentialStore,
)


class KeyringCredentialStore(CredentialStore):
    """Store credentials using the operating system keyring."""

    SERVICE_NAME = "SocialFlow"

    def save(self, key: str, secret: str) -> None:
        keyring.set_password(
            self.SERVICE_NAME,
            key,
            secret,
        )

    def get(self, key: str) -> str | None:
        return keyring.get_password(
            self.SERVICE_NAME,
            key,
        )

    def delete(self, key: str) -> None:
        try:
            keyring.delete_password(
                self.SERVICE_NAME,
                key,
            )
        except PasswordDeleteError:
            pass