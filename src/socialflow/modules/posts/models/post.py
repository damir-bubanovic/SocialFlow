from dataclasses import dataclass

from socialflow.modules.posts.models.language import Language
from socialflow.modules.posts.models.image_attachment import ImageAttachment
from socialflow.modules.posts.models.tag import Tag


@dataclass(frozen=True, slots=True)
class Post:
    """A social media post being composed in SocialFlow."""

    text: str
    language: Language
    images: tuple[ImageAttachment, ...] = ()
    tags: tuple[Tag, ...] = ()
    title: str = ""
    category_ids: tuple[int, ...] = ()

    def has_content(self) -> bool:
        """Return whether the post contains text or image content."""
        return bool(self.text.strip()) or bool(self.images)