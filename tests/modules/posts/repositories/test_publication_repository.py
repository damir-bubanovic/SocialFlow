import pytest

from socialflow.modules.posts.repositories.publication_repository import (
    PublicationRepository,
)


def test_publication_repository_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        PublicationRepository()