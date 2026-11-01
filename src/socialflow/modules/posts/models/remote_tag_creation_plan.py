
"""Plan for creating remote tags after explicit user approval."""

from dataclasses import dataclass

from socialflow.modules.posts.models.tag import Tag


@dataclass(frozen=True, slots=True)
class RemoteTagCreationPlan:
    """Represent missing remote tags awaiting confirmation."""

    missing_tags: tuple[Tag, ...]

    @property
    def requires_confirmation(self) -> bool:
        return bool(self.missing_tags)

    @property
    def tag_names(self) -> tuple[str, ...]:
        return tuple(tag.name for tag in self.missing_tags)
