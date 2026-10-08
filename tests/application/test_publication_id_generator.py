from socialflow.application.publishing.publication_id_generator import (
    PublicationIdGenerator,
)
from socialflow.domain.publishing.publication_id import PublicationId


def test_publication_id_generator_defines_generation_contract() -> None:
    assert PublicationIdGenerator.generate.__annotations__[
        "return"
    ] is PublicationId