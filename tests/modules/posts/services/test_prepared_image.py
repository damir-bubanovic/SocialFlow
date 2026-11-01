from pathlib import Path

from socialflow.modules.posts.services.prepared_image import PreparedImage
from socialflow.modules.posts.models.image_attachment import ImageAttachment
from socialflow.core.destination import PublishingDestination


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