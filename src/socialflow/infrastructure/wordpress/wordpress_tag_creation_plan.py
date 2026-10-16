from dataclasses import dataclass

from socialflow.domain.post.tag import Tag


@dataclass(frozen=True, slots=True)
class WordPressTagCreationPlan:
    """Represent missing tags awaiting user confirmation."""

    missing_tags: tuple[Tag, ...]

    @property
    def requires_confirmation(self) -> bool:
        return bool(self.missing_tags)

    @property
    def tag_names(self) -> tuple[str, ...]:
        return tuple(tag.name for tag in self.missing_tags)