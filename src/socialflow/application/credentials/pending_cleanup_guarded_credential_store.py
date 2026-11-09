from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.modules.accounts.repositories.json_pending_credential_cleanup_repository import (
    JsonPendingCredentialCleanupRepository,
)


class PendingCleanupGuardedCredentialStore(CredentialStore):
    """Prevent credential replacement while cleanup remains pending."""

    def __init__(
        self,
        credential_store: CredentialStore,
        cleanup_repository: JsonPendingCredentialCleanupRepository,
    ) -> None:
        self._credential_store = credential_store
        self._cleanup_repository = cleanup_repository

    def save(self, key: str, secret: str) -> None:
        """Save a credential unless its key has pending cleanup."""
        if key in self._cleanup_repository.all():
            raise ValueError(
                "Credential cannot be saved while cleanup is pending."
            )

        self._credential_store.save(key, secret)

    def get(self, key: str) -> str | None:
        """Retrieve a credential from the underlying store."""
        return self._credential_store.get(key)

    def delete(self, key: str) -> None:
        """Delete a credential from the underlying store."""
        self._credential_store.delete(key)