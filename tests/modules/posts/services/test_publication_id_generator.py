from socialflow.modules.posts.services.publication_id_generator import (
    PublicationIdGenerator,
)
from socialflow.modules.posts.models.publication_id import PublicationId


def test_publication_id_generator_defines_generation_contract() -> None:
    assert PublicationIdGenerator.generate.__annotations__[
        "return"
    ] is PublicationId