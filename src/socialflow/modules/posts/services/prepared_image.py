from dataclasses import dataclass
from pathlib import Path

from socialflow.modules.posts.models.image_attachment import ImageAttachment
from socialflow.core.destination import PublishingDestination


@dataclass(frozen=True, slots=True)
class PreparedImage:
    """An image prepared for a specific publishing destination."""

    source: ImageAttachment
    destination: PublishingDestination
    path: Path