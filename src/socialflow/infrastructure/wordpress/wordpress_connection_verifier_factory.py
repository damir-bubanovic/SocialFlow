
from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.infrastructure.wordpress.urllib_wordpress_http_client import (
    UrllibWordPressHttpClient,
)
from socialflow.infrastructure.wordpress.wordpress_connection_verifier import (
    WordPressConnectionVerifier,
)


class WordPressConnectionVerifierFactory:
    """Create a WordPress verifier with its production dependencies."""

    @staticmethod
    def create(
        credential_store: CredentialStore,
    ) -> WordPressConnectionVerifier:
        return WordPressConnectionVerifier(
            credential_store=credential_store,
            http_client=UrllibWordPressHttpClient(),
        )
