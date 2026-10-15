import pytest

from socialflow.domain.post.tag import Tag
from socialflow.infrastructure.wordpress.wordpress_tag import WordPressTag
from socialflow.infrastructure.wordpress.wordpress_tag_resolver import (
    WordPressTagResolver,
)


def test_resolves_selected_tags_in_order() -> None:
    result = WordPressTagResolver().resolve(
        (Tag("SocialFlow"), Tag("Python")),
        (WordPressTag(12, "Python"), WordPressTag(34, "SocialFlow")),
    )
    assert result == (34, 12)


def test_matches_names_case_insensitively() -> None:
    result = WordPressTagResolver().resolve(
        (Tag("PYTHON"),),
        (WordPressTag(12, "Python"),),
    )
    assert result == (12,)


def test_deduplicates_selected_tags() -> None:
    result = WordPressTagResolver().resolve(
        (Tag("Python"), Tag("python")),
        (WordPressTag(12, "Python"),),
    )
    assert result == (12,)


def test_empty_selection_returns_empty_tuple() -> None:
    assert WordPressTagResolver().resolve((), ()) == ()


def test_missing_tag_raises_error() -> None:
    with pytest.raises(
        ValueError,
        match="WordPress tag not found: Missing",
    ):
        WordPressTagResolver().resolve(
            (Tag("Missing"),),
            (),
        )


def test_ambiguous_remote_name_raises_error() -> None:
    with pytest.raises(
        ValueError,
        match="Ambiguous WordPress tag: Python",
    ):
        WordPressTagResolver().resolve(
            (Tag("Python"),),
            (
                WordPressTag(12, "Python"),
                WordPressTag(34, "python"),
            ),
        )


def test_duplicate_remote_id_is_not_ambiguous() -> None:
    assert WordPressTagResolver().resolve(
        (Tag("Python"),),
        (
            WordPressTag(12, "Python"),
            WordPressTag(12, "python"),
        ),
    ) == (12,)