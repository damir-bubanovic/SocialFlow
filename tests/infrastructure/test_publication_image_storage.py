import pytest
from unittest.mock import patch

from socialflow.domain.post.image_attachment import ImageAttachment
from socialflow.infrastructure.storage.publication_image_storage import (
    PublicationImageStorage,
)


def test_store_creates_managed_image_copy(tmp_path) -> None:
    source = tmp_path / "original.png"
    source.write_bytes(b"image content")

    storage = PublicationImageStorage(tmp_path / "managed")
    stored = storage.store(ImageAttachment(path=source))

    assert stored.path.is_file()
    assert stored.path.read_bytes() == b"image content"
    assert stored.path != source
    assert source.is_file()


def test_store_avoids_filename_collisions(tmp_path) -> None:
    source = tmp_path / "photo.jpg"
    source.write_bytes(b"image content")

    storage = PublicationImageStorage(tmp_path / "managed")
    attachment = ImageAttachment(path=source)

    first = storage.store(attachment)
    second = storage.store(attachment)

    assert first.path != second.path
    assert first.path.is_file()
    assert second.path.is_file()


def test_store_rejects_missing_source(tmp_path) -> None:
    source = tmp_path / "photo.png"
    source.write_bytes(b"image content")

    attachment = ImageAttachment(path=source)
    source.unlink()

    storage = PublicationImageStorage(tmp_path / "managed")

    with pytest.raises(FileNotFoundError):
        storage.store(attachment)

def test_store_removes_partial_file_when_copy_fails(
    tmp_path,
) -> None:
    source = tmp_path / "original.png"
    source.write_bytes(b"image content")

    managed_directory = tmp_path / "managed"
    storage = PublicationImageStorage(managed_directory)

    attachment = ImageAttachment(path=source)

    def failing_copy(source_path, destination_path):
        destination_path.write_bytes(b"partial content")
        raise OSError("Simulated copy failure")

    with patch(
        "socialflow.infrastructure.storage.publication_image_storage.shutil.copy2",
        side_effect=failing_copy,
    ):
        with pytest.raises(OSError, match="Simulated copy failure"):
            storage.store(attachment)

    assert not list(managed_directory.glob("*"))
    assert source.is_file()