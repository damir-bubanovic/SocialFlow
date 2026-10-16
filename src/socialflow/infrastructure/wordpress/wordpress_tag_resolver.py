import unicodedata
from collections.abc import Iterable

from socialflow.domain.post.tag import Tag
from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag
from socialflow.infrastructure.wordpress.wordpress_tag_creation_plan import (
    WordPressTagCreationPlan,
)


class WordPressTagResolver:
    """Resolve selected SocialFlow tags against remote WordPress tags."""

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Create a Unicode-aware key for matching tag names."""
        return unicodedata.normalize("NFC", name).casefold()

    @classmethod
    def prepare_creation_plan(
        cls,
        selected_tags: Iterable[Tag],
        remote_tags: Iterable[WordPressTag],
    ) -> WordPressTagCreationPlan:
        """Prepare missing WordPress tags for user confirmation."""

        missing = cls.find_missing(
            selected_tags=selected_tags,
            remote_tags=remote_tags,
        )

        return WordPressTagCreationPlan(
            missing_tags=missing,
        )

    @staticmethod
    def find_missing(
        selected_tags: Iterable[Tag],
        remote_tags: Iterable[WordPressTag],
    ) -> tuple[Tag, ...]:
        """Find selected tags that do not exist on WordPress."""

        existing_names = {
            WordPressTagResolver._normalize_name(remote_tag.name)
            for remote_tag in remote_tags
        }

        missing: list[Tag] = []
        seen: set[str] = set()

        for tag in selected_tags:
            key = WordPressTagResolver._normalize_name(tag.name)

            if key in existing_names or key in seen:
                continue

            missing.append(tag)
            seen.add(key)

        return tuple(missing)

    @staticmethod
    def resolve(
            selected_tags: Iterable[Tag],
        remote_tags: Iterable[WordPressTag],
    ) -> tuple[int, ...]:
        remote_by_name: dict[str, set[int]] = {}

        for remote_tag in remote_tags:
            key = WordPressTagResolver._normalize_name(remote_tag.name)
            remote_by_name.setdefault(key, set()).add(remote_tag.id)

        resolved: list[int] = []
        seen: set[int] = set()

        for selected_tag in selected_tags:
            ids = remote_by_name.get(
                WordPressTagResolver._normalize_name(selected_tag.name), set()
            )

            if not ids:
                raise ValueError(
                    f"WordPress tag not found: {selected_tag.name}"
                )

            if len(ids) > 1:
                raise ValueError(
                    f"Ambiguous WordPress tag: {selected_tag.name}"
                )

            tag_id = next(iter(ids))

            if tag_id not in seen:
                resolved.append(tag_id)
                seen.add(tag_id)

        return tuple(resolved)