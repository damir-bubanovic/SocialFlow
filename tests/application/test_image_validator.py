from pathlib import Path

import pytest
from PIL import Image

from socialflow.application.images.image_validator import ImageValidator
from socialflow.domain.post.image_attachment import ImageAttachment


def test_image_validator_accepts_readable_image(
    tmp_path: Path,
) -> None:
    path = tmp_path / "valid-image.png"

    image = Image.new("RGB", (100, 100))
    image.save(path)

    attachment = ImageAttachment(path=path)
    validator = ImageValidator()

    validator.validate(attachment)


def test_image_validator_rejects_unreadable_image(
    tmp_path: Path,
) -> None:
    path = tmp_path / "invalid-image.jpg"
    path.write_text("This is not actually an image.")

    attachment = ImageAttachment(path=path)
    validator = ImageValidator()

    with pytest.raises(ValueError, match="Unreadable image file"):
        validator.validate(attachment)