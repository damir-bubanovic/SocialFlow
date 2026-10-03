from dataclasses import dataclass

from socialflow.domain.language.language import Language


@dataclass(frozen=True, slots=True)
class Post:
    """A social media post being composed in SocialFlow."""

    text: str
    language: Language

    def has_content(self) -> bool:
        """Return whether the post contains non-whitespace text."""
        return bool(self.text.strip())