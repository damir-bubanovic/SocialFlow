from collections.abc import Iterable

from socialflow.domain.post.tag import Tag
from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag


class WordPressTagResolver:
    """Resolve selected SocialFlow tags against remote WordPress tags."""

    @staticmethod
    def resolve(
            selected_tags: Iterable[Tag],
        remote_tags: Iterable[WordPressTag],
    ) -> tuple[int, ...]:
        remote_by_name: dict[str, set[int]] = {}

        for remote_tag in remote_tags:
            key = remote_tag.name.casefold()
            remote_by_name.setdefault(key, set()).add(remote_tag.id)

        resolved: list[int] = []
        seen: set[int] = set()

        for selected_tag in selected_tags:
            ids = remote_by_name.get(
                selected_tag.name.casefold(), set()
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