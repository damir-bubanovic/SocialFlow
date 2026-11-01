from dataclasses import dataclass

from socialflow.modules.posts.services.prepared_image import PreparedImage
from socialflow.modules.posts.models.post import Post


@dataclass(frozen=True, slots=True)
class PreparedPost:
    """A post prepared for delivery to a publisher."""

    source: Post
    images: tuple[PreparedImage, ...] = ()