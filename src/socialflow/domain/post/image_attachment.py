from dataclasses import dataclass
from pathlib import Path

SUPPORTED_IMAGE_EXTENSIONS = frozenset({
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
})

@dataclass(frozen=True, slots=True)
class ImageAttachment:
    """An image file attached to a SocialFlow post."""

    path: Path

    def __post_init__(self) -> None:
        """Validate that the attachment uses a supported image format."""
        if self.path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            raise ValueError(
                f"Unsupported image format: {self.path.suffix or 'none'}"
            )

        if not self.path.is_file():
            raise ValueError(
                f"Image file does not exist: {self.path}"
            )

    @property
    def filename(self) -> str:
        """Return the image filename without its directory path."""
        return self.path.name