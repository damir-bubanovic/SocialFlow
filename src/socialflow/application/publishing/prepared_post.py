from dataclasses import dataclass

from socialflow.application.images.prepared_image import PreparedImage
from socialflow.domain.post.post import Post


@dataclass(frozen=True, slots=True)
class PreparedPost:
    """A post prepared for delivery to a publisher."""

    source: Post
    images: tuple[PreparedImage, ...] = ()