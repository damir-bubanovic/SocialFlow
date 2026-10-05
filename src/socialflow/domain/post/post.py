from dataclasses import dataclass

from socialflow.domain.language.language import Language
from socialflow.domain.post.image_attachment import ImageAttachment
from socialflow.domain.post.tag import Tag


@dataclass(frozen=True, slots=True)
class Post:
    """A social media post being composed in SocialFlow."""

    text: str
    language: Language
    images: tuple[ImageAttachment, ...] = ()
    tags: tuple[Tag, ...] = ()

    def has_content(self) -> bool:
        """Return whether the post contains text or image content."""
        return bool(self.text.strip()) or bool(self.images)