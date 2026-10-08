from pathlib import Path

from socialflow.infrastructure.publishing.publication_image_inspector import (
    PublicationImageInspector,
)


def test_inspector_returns_no_missing_images(tmp_path) -> None:
    image = tmp_path / "photo.png"
    image.write_bytes(b"image content")

    result = PublicationImageInspector.missing_images(
        (image,)
    )

    assert result == ()


def test_inspector_detects_missing_image(tmp_path) -> None:
    missing = tmp_path / "deleted.png"

    result = PublicationImageInspector.missing_images(
        (missing,)
    )

    assert result == (missing,)


def test_inspector_detects_only_missing_images(tmp_path) -> None:
    existing = tmp_path / "existing.png"
    existing.write_bytes(b"image content")

    missing = tmp_path / "missing.png"

    result = PublicationImageInspector.missing_images(
        (existing, missing)
    )

    assert result == (missing,)