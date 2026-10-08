from uuid import UUID

from socialflow.domain.publishing.publication_id import PublicationId


def test_publication_id_stores_uuid() -> None:
    value = UUID("12345678-1234-5678-1234-567812345678")

    publication_id = PublicationId(value=value)

    assert publication_id.value == value


def test_publication_id_converts_to_string() -> None:
    publication_id = PublicationId(
        value=UUID("12345678-1234-5678-1234-567812345678")
    )

    assert (
        str(publication_id)
        == "12345678-1234-5678-1234-567812345678"
    )