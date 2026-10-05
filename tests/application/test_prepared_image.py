from pathlib import Path

from socialflow.application.images.prepared_image import PreparedImage
from socialflow.domain.post.image_attachment import ImageAttachment
from socialflow.domain.publishing.destination import PublishingDestination


def test_prepared_image_contains_source_destination_and_path(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "source.jpg"
    prepared_path = tmp_path / "prepared.jpg"

    source_path.touch()
    prepared_path.touch()

    source = ImageAttachment(
        path=source_path,
    )

    prepared = PreparedImage(
        source=source,
        destination=PublishingDestination.INSTAGRAM,
        path=prepared_path,
    )

    assert prepared.source == source
    assert prepared.destination == PublishingDestination.INSTAGRAM
    assert prepared.path == prepared_path