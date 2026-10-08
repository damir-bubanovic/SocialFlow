import pytest

from socialflow.application.credentials.credential_store import (
    CredentialStore,
)


def test_credential_store_is_abstract():
    with pytest.raises(TypeError):
        CredentialStore()


def test_credential_store_defines_required_operations():
    assert CredentialStore.__abstractmethods__ == {
        "save",
        "get",
        "delete",
    }