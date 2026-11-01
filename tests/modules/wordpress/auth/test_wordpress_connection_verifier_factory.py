
from unittest.mock import Mock

from socialflow.application.credentials.credential_store import (
    CredentialStore,
)
from socialflow.modules.wordpress.api.urllib_wordpress_http_client import (
    UrllibWordPressHttpClient,
)
from socialflow.modules.wordpress.auth.wordpress_connection_verifier import (
    WordPressConnectionVerifier,
)
from socialflow.modules.wordpress.auth.wordpress_connection_verifier_factory import (
    WordPressConnectionVerifierFactory,
)


def test_factory_creates_wordpress_connection_verifier() -> None:
    credential_store = Mock(spec=CredentialStore)

    verifier = WordPressConnectionVerifierFactory.create(
        credential_store=credential_store,
    )

    assert isinstance(verifier, WordPressConnectionVerifier)
    assert isinstance(verifier._http_client, UrllibWordPressHttpClient)
    assert verifier._credential_store is credential_store
