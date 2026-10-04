from pathlib import Path

import pytest

from socialflow.domain.post.image_attachment import ImageAttachment


def test_image_attachment_contains_source_path(
    tmp_path: Path,
) -> None:
    path = tmp_path / "socialflow-image.jpg"
    path.touch()

    attachment = ImageAttachment(path=path)

    assert attachment.path == path


def test_image_attachment_rejects_unsupported_format() -> None:
    with pytest.raises(ValueError, match="Unsupported image format"):
        ImageAttachment(path=Path("/tmp/socialflow-image.txt"))


def test_image_attachment_accepts_uppercase_extension(
    tmp_path: Path,
) -> None:
    path = tmp_path / "socialflow-image.JPG"
    path.touch()

    attachment = ImageAttachment(path=path)

    assert attachment.path == path


def test_image_attachment_rejects_missing_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing-image.jpg"

    with pytest.raises(ValueError, match="Image file does not exist"):
        ImageAttachment(path=path)

def test_image_attachment_exposes_filename(
    tmp_path: Path,
) -> None:
    path = tmp_path / "socialflow-image.jpg"
    path.touch()

    attachment = ImageAttachment(path=path)

    assert attachment.filename == "socialflow-image.jpg"