import shutil
from pathlib import Path
from uuid import uuid4

from socialflow.domain.post.image_attachment import ImageAttachment


class PublicationImageStorage:
    """Preserve publication images in application-managed storage."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def store(self, image: ImageAttachment) -> ImageAttachment:
        """Copy an image and remove incomplete copies on failure."""
        self._directory.mkdir(parents=True, exist_ok=True)

        destination = self._directory / (
            f"{uuid4().hex}_{image.filename}"
        )

        try:
            shutil.copy2(image.path, destination)
            return ImageAttachment(path=destination)

        except Exception:
            destination.unlink(missing_ok=True)
            raise